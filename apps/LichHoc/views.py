from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta
import io
import csv

from .models import LichHoc, LopHoc, MonHoc, DangKyHocPhan, YeuCauDoiLich, KHUNG_GIO_TIET
from .forms import FormLichHoc, FormLopHoc
from apps.PhongHoc.models import PhongHoc


def cap_nhat_trang_thai_phong(ngay=None):
    """Cập nhật trạng thái phòng dựa trên lịch học."""
    if ngay is None:
        ngay = timezone.now().date()
    # Phòng đang có lịch hoạt động hôm nay
    phong_dang_dung_ids = LichHoc.objects.filter(
        ngay_hoc=ngay, trang_thai='hoat_dong'
    ).values_list('phong_hoc_id', flat=True).distinct()
    # Cập nhật phòng đang sử dụng
    PhongHoc.objects.filter(id__in=phong_dang_dung_ids).exclude(
        trang_thai='bao_tri'
    ).update(trang_thai='dang_su_dung')
    # Cập nhật phòng trống (không có lịch hôm nay và không bảo trì)
    PhongHoc.objects.exclude(id__in=phong_dang_dung_ids).exclude(
        trang_thai='bao_tri'
    ).update(trang_thai='trong')


def kiem_tra_quyen_lich(view_func):
    """Decorator: chỉ giáo vụ mới được quản lý lịch học."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dang_nhap')
        if not (request.user.la_giao_vu or request.user.la_quan_tri):
            messages.error(request, 'Chỉ giáo vụ hoặc quản trị viên mới có quyền quản lý lịch học.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def danh_sach_lich(request):
    """Danh sách lịch học - mặc định hôm nay, có nút chuyển ngày."""
    hom_nay = timezone.now().date()
    
    # Cập nhật trạng thái phòng
    cap_nhat_trang_thai_phong(hom_nay)
    
    # Lọc theo ngày — mặc định hôm nay
    ngay_loc = request.GET.get('ngay', '')
    if ngay_loc:
        try:
            ngay_hien_tai = datetime.strptime(ngay_loc, '%Y-%m-%d').date()
        except ValueError:
            ngay_hien_tai = hom_nay
    else:
        ngay_hien_tai = hom_nay
    
    ngay_truoc = ngay_hien_tai - timedelta(days=1)
    ngay_sau = ngay_hien_tai + timedelta(days=1)
    
    # Khởi tạo queryset
    queryset = LichHoc.objects.select_related(
        'mon_hoc', 'giang_vien', 'phong_hoc', 'lop_hoc'
    ).filter(ngay_hoc=ngay_hien_tai)

    # PHÂN QUYỀN HIỂN THỊ DỮ LIỆU CHÍNH
    if request.user.la_sinh_vien:
        # Sinh viên: Chỉ thấy lịch của các lớp mình đã đăng ký
        lop_ids = DangKyHocPhan.objects.filter(sinh_vien=request.user).values_list('lop_hoc_id', flat=True)
        queryset = queryset.filter(lop_hoc_id__in=lop_ids)
    elif request.user.la_giang_vien:
        # Giảng viên: Chỉ thấy lịch dạy của mình
        queryset = queryset.filter(giang_vien=request.user)
    # Admin/Giáo vụ: Thấy toàn bộ (không cần filter thêm)

    # Tìm kiếm
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(
            Q(mon_hoc__ten_mon__icontains=tu_khoa) |
            Q(mon_hoc__ma_mon__icontains=tu_khoa)
        )

    # Bộ lọc nâng cao
    phong_loc = request.GET.get('phong', '')
    if phong_loc:
        if phong_loc.isdigit():
            queryset = queryset.filter(phong_hoc_id=phong_loc)
        else:
            queryset = queryset.filter(phong_hoc__ma_phong=phong_loc)

    lop_loc = request.GET.get('lop', '')
    if lop_loc:
        queryset = queryset.filter(lop_hoc_id=lop_loc)

    buoi_loc = request.GET.get('buoi', '')
    buoi_map = {
        'sang': (1, 5),
        'chieu': (6, 10),
        'toi': (11, 14),
    }
    if buoi_loc in buoi_map:
        bd, kt = buoi_map[buoi_loc]
        queryset = queryset.filter(tiet_bat_dau__lte=kt, tiet_ket_thuc__gte=bd)

    tiet_loc = request.GET.get('tiet', '')
    if tiet_loc:
        try:
            tiet_loc_int = int(tiet_loc)
            queryset = queryset.filter(tiet_bat_dau__lte=tiet_loc_int, tiet_ket_thuc__gte=tiet_loc_int)
        except ValueError:
            tiet_loc = ''

    trang_thai = request.GET.get('trang_thai', '')
    if trang_thai:
        queryset = queryset.filter(trang_thai=trang_thai)

    # Sắp xếp: Ưu tiên lịch hoạt động, sau đó theo tiết bắt đầu
    queryset = queryset.annotate(
        priority=Case(
            When(trang_thai='hoat_dong', then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('priority', 'tiet_bat_dau')

    page_size = request.GET.get('page_size', '10')
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 10

    paginator = Paginator(queryset, page_size)
    trang = request.GET.get('page')
    lich_hocs = paginator.get_page(trang)

    # Tên thứ trong tuần
    thu_map = {0: 'Thứ Hai', 1: 'Thứ Ba', 2: 'Thứ Tư', 3: 'Thứ Năm', 4: 'Thứ Sáu', 5: 'Thứ Bảy', 6: 'Chủ Nhật'}
    ten_thu = thu_map.get(ngay_hien_tai.weekday(), '')

    # TÙY CHỌN FILTER TRONG TEMPLATE (Cũng phải lọc theo quyền)
    ds_phong_qs = LichHoc.objects.filter(ngay_hoc=ngay_hien_tai)
    ds_lop_qs = LichHoc.objects.filter(ngay_hoc=ngay_hien_tai, lop_hoc__isnull=False)

    if request.user.la_sinh_vien:
        lop_ids_personal = DangKyHocPhan.objects.filter(sinh_vien=request.user).values_list('lop_hoc_id', flat=True)
        ds_phong_qs = ds_phong_qs.filter(lop_hoc_id__in=lop_ids_personal)
        ds_lop_qs = ds_lop_qs.filter(lop_hoc_id__in=lop_ids_personal)
    elif request.user.la_giang_vien:
        ds_phong_qs = ds_phong_qs.filter(giang_vien=request.user)
        ds_lop_qs = ds_lop_qs.filter(giang_vien=request.user)

    ds_phong = ds_phong_qs.values_list('phong_hoc_id', 'phong_hoc__ma_phong').distinct().order_by('phong_hoc__ma_phong')
    ds_lop = ds_lop_qs.values_list('lop_hoc_id', 'lop_hoc__ten_lop').distinct().order_by('lop_hoc__ten_lop')

    context = {
        'lich_hocs': lich_hocs,
        'tu_khoa': tu_khoa,
        'ngay_hien_tai': ngay_hien_tai,
        'ngay_truoc': ngay_truoc,
        'ngay_sau': ngay_sau,
        'hom_nay': hom_nay,
        'ten_thu': ten_thu,
        'trang_thai_loc': trang_thai,
        'phong_loc': phong_loc,
        'lop_loc': lop_loc,
        'buoi_loc': buoi_loc,
        'tiet_loc': tiet_loc,
        'ds_phong': ds_phong,
        'ds_lop': ds_lop,
        'tiet_choices': list(range(1, 15)),
        'khung_gio': KHUNG_GIO_TIET,
    }
    return render(request, 'LichHoc/DanhSach.html', context)


@kiem_tra_quyen_lich
def them_lich(request):
    """Thêm lịch học mới."""
    if request.method == 'POST':
        form = FormLichHoc(request.POST)
        if form.is_valid():
            lich = form.save()
            # Tạo thông báo tự động cho giảng viên
            from apps.ThongBao.models import ThongBao
            from apps.NguoiDung.models import NguoiDung
            ThongBao.objects.create(
                tieu_de=f'Lịch dạy mới: {lich.mon_hoc}',
                noi_dung=f'Bạn được phân công dạy môn {lich.mon_hoc} lớp {lich.lop_hoc.ten_lop if lich.lop_hoc else "-"} tại phòng {lich.phong_hoc.ma_phong}, '
                         f'ngày {lich.ngay_hoc}, tiết {lich.tiet_bat_dau}-{lich.tiet_ket_thuc}.',
                loai='doi_lich',
                nguoi_tao=request.user,
                nguoi_nhan=lich.giang_vien
            )
            # Tạo thông báo cho sinh viên đăng ký lớp học phần
            if lich.lop_hoc:
                sv_ids = DangKyHocPhan.objects.filter(lop_hoc=lich.lop_hoc).values_list('sinh_vien_id', flat=True)
                sinh_viens = NguoiDung.objects.filter(id__in=sv_ids)
                for sv in sinh_viens:
                    ThongBao.objects.create(
                        tieu_de=f'Lịch học mới: {lich.mon_hoc}',
                        noi_dung=f'Lớp bạn có lịch học môn {lich.mon_hoc} tại phòng {lich.phong_hoc.ma_phong}, '
                                 f'ngày {lich.ngay_hoc}, tiết {lich.tiet_bat_dau}-{lich.tiet_ket_thuc}.',
                        loai='doi_lich',
                        nguoi_tao=request.user,
                        nguoi_nhan=sv
                    )
            messages.success(request, f'Đã thêm lịch học "{lich.mon_hoc}" thành công.')
            return redirect('danh_sach_lich')
    else:
        form = FormLichHoc()
    ds_mon_hoc = MonHoc.objects.order_by('ma_mon', 'ten_mon')
    return render(request, 'LichHoc/ThemMoi.html', {'form': form, 'ds_mon_hoc': ds_mon_hoc})


@kiem_tra_quyen_lich
def chinh_sua_lich(request, pk):
    """Chỉnh sửa lịch học."""
    lich = get_object_or_404(LichHoc, pk=pk)
    if request.method == 'POST':
        form = FormLichHoc(request.POST, instance=lich)
        if form.is_valid():
            lich_moi = form.save()
            from apps.ThongBao.models import ThongBao
            from apps.NguoiDung.models import NguoiDung
            # Thông báo cho Giảng viên
            ThongBao.objects.create(
                tieu_de=f'Thay đổi lịch dạy: {lich_moi.mon_hoc}',
                noi_dung=f'Lịch dạy môn {lich_moi.mon_hoc} của bạn đã được cập nhật.',
                loai='doi_lich',
                nguoi_tao=request.user,
                nguoi_nhan=lich_moi.giang_vien
            )
            # Thông báo cho Sinh viên
            if lich_moi.lop_hoc:
                sv_ids = DangKyHocPhan.objects.filter(lop_hoc=lich_moi.lop_hoc).values_list('sinh_vien_id', flat=True)
                sinh_viens = NguoiDung.objects.filter(id__in=sv_ids)
                for sv in sinh_viens:
                    ThongBao.objects.create(
                        tieu_de=f'Thay đổi lịch học: {lich_moi.mon_hoc}',
                        noi_dung=f'Lịch học môn {lich_moi.mon_hoc} của lớp bạn đã được giáo vụ cập nhật.',
                        loai='doi_lich',
                        nguoi_tao=request.user,
                        nguoi_nhan=sv
                    )
            messages.success(request, f'Đã cập nhật lịch học "{lich_moi.mon_hoc}".')
            return redirect('danh_sach_lich')
    else:
        form = FormLichHoc(instance=lich)
    ds_mon_hoc = MonHoc.objects.order_by('ma_mon', 'ten_mon')
    return render(request, 'LichHoc/ChinhSua.html', {'form': form, 'lich': lich, 'ds_mon_hoc': ds_mon_hoc})


@kiem_tra_quyen_lich
def huy_lich(request, pk):
    """Hủy lịch học."""
    lich = get_object_or_404(LichHoc, pk=pk)
    if request.method == 'POST':
        lich.trang_thai = 'da_huy'
        lich.save()
        from apps.ThongBao.models import ThongBao
        from apps.NguoiDung.models import NguoiDung
        # Thông báo cho GV
        ThongBao.objects.create(
            tieu_de=f'Hủy lịch dạy: {lich.mon_hoc}',
            noi_dung=f'Lịch dạy môn {lich.mon_hoc} ngày {lich.ngay_hoc} đã bị hủy.',
            loai='huy_lich',
            nguoi_tao=request.user,
            nguoi_nhan=lich.giang_vien
        )
        # Thông báo cho SV
        if lich.lop_hoc:
            sv_ids = DangKyHocPhan.objects.filter(lop_hoc=lich.lop_hoc).values_list('sinh_vien_id', flat=True)
            sinh_viens = NguoiDung.objects.filter(id__in=sv_ids)
            for sv in sinh_viens:
                ThongBao.objects.create(
                    tieu_de=f'Hủy lịch học: {lich.mon_hoc}',
                    noi_dung=f'Lịch học môn {lich.mon_hoc} ngày {lich.ngay_hoc} đã bị hủy.',
                    loai='huy_lich',
                    nguoi_tao=request.user,
                    nguoi_nhan=sv
                )
        messages.success(request, f'Đã hủy lịch học "{lich.mon_hoc}".')
        return redirect('danh_sach_lich')
    return render(request, 'LichHoc/XacNhanHuy.html', {'lich': lich})


@kiem_tra_quyen_lich
def xoa_lich(request, pk):
    """Xóa vĩnh viễn lịch học."""
    lich = get_object_or_404(LichHoc, pk=pk)
    if request.method == 'POST':
        mon_hoc_ten = str(lich.mon_hoc)
        lich.delete()
        messages.success(request, f'Đã xóa vĩnh viễn lịch học môn "{mon_hoc_ten}".')
    return redirect('danh_sach_lich')


@login_required
def tra_cuu_phong(request):
    """Tra cứu phòng trống theo ngày + tiết."""
    ket_qua = None
    page_obj = None
    ngay = request.GET.get('ngay', '')
    if not ngay:
        ngay = timezone.now().date().strftime('%Y-%m-%d')
        
    tiet_bd = request.GET.get('tiet_bd', '')
    tiet_kt = request.GET.get('tiet_kt', '')
    
    if not tiet_bd or not tiet_kt:
        # Tự động xác định tiết hiện tại dựa trên giờ hệ thống
        current_hour = timezone.now().hour
        if current_hour < 12:
            tiet_bd = tiet_bd or '1'
            tiet_kt = tiet_kt or '5'
        elif current_hour < 18:
            tiet_bd = tiet_bd or '6'
            tiet_kt = tiet_kt or '10'
        else:
            tiet_bd = tiet_bd or '11'
            tiet_kt = tiet_kt or '14'

    if ngay and tiet_bd and tiet_kt:
        try:
            # Flexible date parsing
            ngay_hien_tai = datetime.strptime(ngay, '%Y-%m-%d').date()
        except ValueError:
            ngay_hien_tai = timezone.now().date()
            ngay = ngay_hien_tai.strftime('%Y-%m-%d')
            
        # Tìm phòng đã có lịch trong khoảng thời gian
        phong_da_dung = LichHoc.objects.filter(
            ngay_hoc=ngay_hien_tai,
            trang_thai='hoat_dong',
            tiet_bat_dau__lt=int(tiet_kt),
            tiet_ket_thuc__gt=int(tiet_bd),
        ).values_list('phong_hoc_id', flat=True)

        qs = PhongHoc.objects.exclude(
            id__in=phong_da_dung
        ).exclude(trang_thai='bao_tri').order_by('ma_phong')
        
        # Lọc thêm theo tòa nhà và loại phòng
        toa_nha_loc = request.GET.get('toa_nha', '')
        if toa_nha_loc:
            qs = qs.filter(toa_nha=toa_nha_loc)
            
        loai_phong_loc = request.GET.get('loai_phong', '')
        if loai_phong_loc:
            qs = qs.filter(loai_phong=loai_phong_loc)

        page_size = request.GET.get('page_size', '10')
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 10

        paginator = Paginator(qs, page_size)
        trang = request.GET.get('page')
        ket_qua = paginator.get_page(trang)
        page_obj = ket_qua

    context = {
        'ket_qua': ket_qua,
        'page_obj': page_obj,
        'ngay': ngay,
        'tiet_bd': tiet_bd,
        'tiet_kt': tiet_kt,
        'toa_nha_loc': request.GET.get('toa_nha', ''),
        'loai_phong_loc': request.GET.get('loai_phong', ''),
        'page_size': request.GET.get('page_size', '10'),
        'ds_toa_nha': PhongHoc.objects.values_list('toa_nha', flat=True).distinct().order_by('toa_nha'),
        'loai_phong_choices': PhongHoc.LoaiPhong.choices,
    }
    return render(request, 'LichHoc/TraCuu.html', context)

@login_required
def goi_y_phong_toi_uu(request):
    """
    API Gợi ý phòng thông minh dựa trên thuật toán Heuristic Scoring.
    """
    from .optimization import algorithm_room_scoring
    
    ngay_str = request.GET.get('ngay')
    try:
        tiet_bd = int(request.GET.get('tiet_bd', 1))
        tiet_kt = int(request.GET.get('tiet_kt', 1))
        si_so = int(request.GET.get('si_so', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Dữ liệu đầu vào không hợp lệ'}, status=400)
        
    khoa_id = request.GET.get('khoa', '')
    lop_id = request.GET.get('lop_id')

    if not ngay_str:
        return JsonResponse({'error': 'Thiếu ngày học'}, status=400)

    # Gọi thuật toán tập trung
    ket_qua_raw = algorithm_room_scoring(ngay_str, tiet_bd, tiet_kt, si_so, khoa_id, lop_id)

    # Format lại dữ liệu cho JSON Response
    data = []
    for item in ket_qua_raw[:10]: # Lấy top 10
        phong = item['phong_obj']
        data.append({
            'id': phong.id,
            'ten_phong': f"{phong.toa_nha}.{phong.ten_phong}",
            'suc_chua': phong.suc_chua,
            'loai_phong': phong.get_loai_phong_display(),
            'ghi_chu': phong.ghi_chu,
            'score': item['score'],
            'ly_do': item['ly_do']
        })

    return JsonResponse({'data': data})


def api_loc_lop_theo_mon(request):
    """API trả về danh sách lớp khi chọn môn hoặc ngược lại."""
    mon_id = request.GET.get('mon_id')
    lop_id = request.GET.get('lop_id')
    
    if mon_id:
        lops = LopHoc.objects.filter(mon_hoc_id=mon_id).values('id', 'ten_lop')
        return JsonResponse({'lops': list(lops)})
    
    if lop_id:
        lop = LopHoc.objects.filter(id=lop_id).select_related('mon_hoc').first()
        if lop and lop.mon_hoc:
            return JsonResponse({
                'mon_id': lop.mon_hoc.id,
                'mon_ten': lop.mon_hoc.ten_mon,
                'giang_vien_id': lop.giang_vien.id if lop.giang_vien else ''
            })
            
    return JsonResponse({'error': 'Invalid request'}, status=400)

@kiem_tra_quyen_lich
def them_lich_hang_loat(request):
    """Tạo lịch học lặp theo tuần (chọn thứ, từ ngày → đến ngày)."""
    if request.method == 'POST':
        form = FormLichHoc(request.POST)
        # Lấy thông tin lặp
        ngay_bd = request.POST.get('ngay_bat_dau', '')
        ngay_kt = request.POST.get('ngay_ket_thuc', '')
        thu_chon = request.POST.getlist('thu_trong_tuan')  # ['1','3','5']
        
        if not ngay_bd or not ngay_kt or not thu_chon:
            messages.error(request, 'Vui lòng chọn đầy đủ: ngày bắt đầu, ngày kết thúc, và thứ trong tuần.')
            ds_mon_hoc = MonHoc.objects.order_by('ma_mon', 'ten_mon')
            return render(request, 'LichHoc/ThemMoiHangLoat.html', {'form': form, 'ds_mon_hoc': ds_mon_hoc})
        
        try:
            start = datetime.strptime(ngay_bd, '%Y-%m-%d').date()
            end = datetime.strptime(ngay_kt, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Ngày không hợp lệ.')
            ds_mon_hoc = MonHoc.objects.order_by('ma_mon', 'ten_mon')
            return render(request, 'LichHoc/ThemMoiHangLoat.html', {'form': form, 'ds_mon_hoc': ds_mon_hoc})
        
        thu_ints = [int(t) for t in thu_chon]  # 0=Mon, 1=Tue,...
        
        # Validate form (trừ ngay_hoc vì sẽ tự tạo)
        # Tạm set ngay_hoc để form valid
        post_data = request.POST.copy()
        post_data['ngay_hoc'] = ngay_bd
        form = FormLichHoc(post_data)
        
        if form.is_valid():
            mon_hoc = form.cleaned_data['mon_hoc']
            lop_hoc = form.cleaned_data['lop_hoc']
            giang_vien = form.cleaned_data['giang_vien']
            phong_hoc = form.cleaned_data['phong_hoc']
            tiet_bd = form.cleaned_data['tiet_bat_dau']
            tiet_kt_val = form.cleaned_data['tiet_ket_thuc']
            si_so = form.cleaned_data['si_so']
            ghi_chu = form.cleaned_data.get('ghi_chu', '')
            
            so_lich_tao = 0
            so_trung = 0
            current = start
            while current <= end:
                if current.weekday() in thu_ints:
                    # Kiểm tra trùng phòng
                    if LichHoc.kiem_tra_trung_phong(phong_hoc.id, current, tiet_bd, tiet_kt_val):
                        so_trung += 1
                        current += timedelta(days=1)
                        continue
                    # Kiểm tra trùng GV
                    if LichHoc.kiem_tra_trung_giang_vien(giang_vien.id, current, tiet_bd, tiet_kt_val):
                        so_trung += 1
                        current += timedelta(days=1)
                        continue
                    
                    LichHoc.objects.create(
                        mon_hoc=mon_hoc,
                        lop_hoc=lop_hoc,
                        ma_lop=lop_hoc.ten_lop if lop_hoc else '',
                        giang_vien=giang_vien,
                        phong_hoc=phong_hoc,
                        ngay_hoc=current,
                        tiet_bat_dau=tiet_bd,
                        tiet_ket_thuc=tiet_kt_val,
                        si_so=si_so,
                        ghi_chu=ghi_chu,
                    )
                    so_lich_tao += 1
                current += timedelta(days=1)
            
            if so_lich_tao > 0:
                messages.success(request, f'Đã tạo {so_lich_tao} lịch học thành công. {f"({so_trung} bị bỏ qua do trùng)" if so_trung else ""}')
            else:
                messages.warning(request, f'Không tạo được lịch nào. {so_trung} xung đột phát hiện.')
            return redirect('danh_sach_lich')
    else:
        form = FormLichHoc()
    
    ds_mon_hoc = MonHoc.objects.order_by('ma_mon', 'ten_mon')
    return render(request, 'LichHoc/ThemMoiHangLoat.html', {'form': form, 'ds_mon_hoc': ds_mon_hoc})


def _doc_csv_upload(csv_file):
    file_data = csv_file.read()
    encodings = ['utf-8-sig', 'utf-16', 'windows-1258', 'utf-8']
    decoded_file = None

    for encoding in encodings:
        try:
            decoded_file = file_data.decode(encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if not decoded_file:
        raise ValueError('Không thể nhận diện bảng mã file CSV. Vui lòng dùng UTF-8.')

    io_string = io.StringIO(decoded_file)
    try:
        dialect = csv.Sniffer().sniff(decoded_file[:2000], delimiters=',;')
        return list(csv.DictReader(io_string, dialect=dialect))
    except Exception:
        io_string.seek(0)
        return list(csv.DictReader(io_string))


def _lay_queryset_lop_hoc_phan(request):
    queryset = LopHoc.objects.select_related('mon_hoc').annotate(
        so_sv=Count('dang_ky_hoc_phans')
    ).order_by('ten_lop')

    tu_khoa = request.GET.get('q', '').strip()
    if tu_khoa:
        queryset = queryset.filter(
            Q(ten_lop__icontains=tu_khoa) |
            Q(mon_hoc__ten_mon__icontains=tu_khoa) |
            Q(mon_hoc__ma_mon__icontains=tu_khoa)
        )

    khoa_loc = request.GET.get('khoa', '').strip()
    if khoa_loc:
        queryset = queryset.filter(khoa=khoa_loc)

    nien_khoa_loc = request.GET.get('nien_khoa', '').strip()
    if nien_khoa_loc:
        queryset = queryset.filter(nien_khoa=nien_khoa_loc)

    context = {
        'tu_khoa': tu_khoa,
        'khoa_loc': khoa_loc,
        'nien_khoa_loc': nien_khoa_loc,
    }
    return queryset, context


@kiem_tra_quyen_lich
def lay_tien_do_nhap_lop_csv(request):
    task_id = request.GET.get('task_id')
    progress = cache.get(f'lop_import_progress_{task_id}', 0)
    status = cache.get(f'lop_import_status_{task_id}', 'Đang xử lý...')
    return JsonResponse({'progress': progress, 'status': status})


@kiem_tra_quyen_lich
def danh_sach_lop(request):
    """Danh sách lớp học."""
    from django.db.models import Count
    queryset = LopHoc.objects.annotate(
        so_sv=Count('dang_ky_hoc_phans')
    ).order_by('ten_lop')

    # Filters
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(ten_lop__icontains=tu_khoa)
    
    khoa_loc = request.GET.get('khoa', '')
    if khoa_loc:
        queryset = queryset.filter(khoa=khoa_loc)
        
    nien_khoa_loc = request.GET.get('nien_khoa', '')
    if nien_khoa_loc:
        queryset = queryset.filter(nien_khoa=nien_khoa_loc)

    # Dữ liệu cho bộ lọc
    ds_khoa = LopHoc.objects.values_list('khoa', flat=True).distinct().exclude(khoa='')
    ds_nien_khoa = LopHoc.objects.values_list('nien_khoa', flat=True).distinct().exclude(nien_khoa='')
    
    paginator = Paginator(queryset, 15)
    trang = request.GET.get('page')
    lop_hocs = paginator.get_page(trang)
    
    return render(request, 'LichHoc/DanhSachLop.html', {
        'lop_hocs': lop_hocs,
        'tu_khoa': tu_khoa,
        'khoa_loc': khoa_loc,
        'nien_khoa_loc': nien_khoa_loc,
        'ds_khoa': ds_khoa,
        'ds_nien_khoa': ds_nien_khoa,
    })


@kiem_tra_quyen_lich
def them_lop(request):
    """Thêm lớp học mới."""
    if request.method == 'POST':
        form = FormLopHoc(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm lớp học mới thành công.')
            return redirect('danh_sach_lop')
    else:
        form = FormLopHoc()
    return render(request, 'LichHoc/ThemMoiLop.html', {'form': form})


@kiem_tra_quyen_lich
def chinh_sua_lop(request, pk):
    """Chỉnh sửa lớp học."""
    lop = get_object_or_404(LopHoc, pk=pk)
    if request.method == 'POST':
        form = FormLopHoc(request.POST, instance=lop)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật lớp {lop.ten_lop}.')
            return redirect('danh_sach_lop')
    else:
        form = FormLopHoc(instance=lop)
    return render(request, 'LichHoc/ChinhSuaLop.html', {'form': form, 'lop': lop})


def kiem_tra_quyen_xem_lop(view_func):
    """Decorator: giáo vụ, admin, hoặc giảng viên được xem DS sinh viên."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dang_nhap')
        if not (request.user.la_quan_tri or request.user.la_giao_vu or request.user.la_giang_vien):
            messages.error(request, 'Bạn không có quyền xem danh sách này.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@kiem_tra_quyen_xem_lop
def danh_sach_sv_lop(request, pk):
    """Xem danh sách sinh viên đăng ký một lớp học phần."""
    lop = get_object_or_404(LopHoc, pk=pk)
    dang_ky_list = DangKyHocPhan.objects.filter(
        lop_hoc=lop
    ).select_related('sinh_vien').order_by('sinh_vien__ho_ten')
    
    # Lịch học của lớp này
    lich_hocs = LichHoc.objects.filter(
        lop_hoc=lop, trang_thai='hoat_dong'
    ).select_related('mon_hoc', 'phong_hoc', 'giang_vien').order_by('ngay_hoc', 'tiet_bat_dau')
    
    return render(request, 'LichHoc/DanhSachSVLop.html', {
        'lop': lop,
        'dang_ky_list': dang_ky_list,
        'lich_hocs': lich_hocs,
    })


@kiem_tra_quyen_lich
def them_sv_vao_lop(request, pk):
    """Thêm sinh viên vào lớp học phần."""
    from apps.NguoiDung.models import NguoiDung
    lop = get_object_or_404(LopHoc, pk=pk)
    if request.method == 'POST':
        sv_ids = request.POST.getlist('sinh_vien_ids')
        so_them = 0
        for sv_id in sv_ids:
            _, created = DangKyHocPhan.objects.get_or_create(
                sinh_vien_id=sv_id, lop_hoc=lop
            )
            if created:
                so_them += 1
        messages.success(request, f'Đã thêm {so_them} sinh viên vào lớp {lop.ten_lop}.')
        return redirect('danh_sach_sv_lop', pk=lop.pk)
    
    # DS sinh viên chưa đăng ký lớp này
    da_dk_ids = DangKyHocPhan.objects.filter(lop_hoc=lop).values_list('sinh_vien_id', flat=True)
    sv_chua_dk = NguoiDung.objects.filter(
        vai_tro='sinh_vien', is_active=True
    ).exclude(id__in=da_dk_ids).select_related('lop_sinh_hoat').order_by('ho_ten')
    
    return render(request, 'LichHoc/ThemSVVaoLop.html', {
        'lop': lop,
        'sv_chua_dk': sv_chua_dk,
    })


@kiem_tra_quyen_lich
def xoa_sv_khoi_lop(request, pk, sv_id):
    """Xóa sinh viên khỏi lớp học phần."""
    lop = get_object_or_404(LopHoc, pk=pk)
    dk = get_object_or_404(DangKyHocPhan, lop_hoc=lop, sinh_vien_id=sv_id)
    if request.method == 'POST':
        dk.delete()
        messages.success(request, 'Đã xóa sinh viên khỏi lớp học phần.')
    return redirect('danh_sach_sv_lop', pk=lop.pk)
@kiem_tra_quyen_lich
@transaction.atomic
def nhap_lop_hoc_csv(request):
    """Nhập danh sách lớp học phần từ CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        try:
            rows = _doc_csv_upload(request.FILES['csv_file'])
            if not rows:
                messages.error(request, 'File CSV không có dữ liệu.')
                return redirect('danh_sach_lop')

            ghi_de = request.POST.get('ghi_de') == 'on'
            errors = []
            seen_lops = set()
            total_rows = len(rows)
            task_id = request.POST.get('task_id', 'manual')

            for index, row in enumerate(rows, start=2):
                ten_lop = row.get('ten_lop', '').strip().upper()
                ma_mon = row.get('ma_mon', '').strip().upper()
                ten_mon = row.get('ten_mon', '').strip()

                if not ten_lop or not ma_mon or not ten_mon:
                    errors.append(f'Dòng {index}: Thiếu một trong các cột bắt buộc ten_lop, ma_mon, ten_mon.')
                    continue

                if ten_lop in seen_lops:
                    errors.append(f"Dòng {index}: Lớp '{ten_lop}' bị trùng trong file.")
                seen_lops.add(ten_lop)

                if not ghi_de and LopHoc.objects.filter(ten_lop=ten_lop).exists():
                    errors.append(f"Dòng {index}: Lớp '{ten_lop}' đã tồn tại.")

            if errors:
                messages.error(request, 'Lỗi dữ liệu:<br>' + '<br>'.join(errors[:10]))
                return redirect('danh_sach_lop')

            count_new = 0
            count_upd = 0

            for index, row in enumerate(rows, start=1):
                percent = int((index / total_rows) * 100)
                cache.set(f'lop_import_progress_{task_id}', percent, 300)
                cache.set(f'lop_import_status_{task_id}', f"Đang xử lý lớp {index}/{total_rows}...", 300)

                ten_lop = row.get('ten_lop', '').strip().upper()
                ma_mon = row.get('ma_mon', '').strip().upper()
                ten_mon = row.get('ten_mon', '').strip()
                khoa = row.get('khoa', '').strip()
                nien_khoa = row.get('nien_khoa', '').strip()
                ten_gv = row.get('giang_vien', '').strip()

                mon_hoc, mon_created = MonHoc.objects.get_or_create(
                    ma_mon=ma_mon,
                    defaults={'ten_mon': ten_mon},
                )
                if not mon_created and mon_hoc.ten_mon != ten_mon:
                    mon_hoc.ten_mon = ten_mon
                    mon_hoc.save(update_fields=['ten_mon'])

                lop_hoc, created = LopHoc.objects.get_or_create(ten_lop=ten_lop)
                lop_hoc.mon_hoc = mon_hoc
                lop_hoc.khoa = khoa
                lop_hoc.nien_khoa = nien_khoa
                
                # Tìm giảng viên theo tên
                if ten_gv:
                    from apps.NguoiDung.models import NguoiDung
                    gv_obj = NguoiDung.objects.filter(ho_ten__iexact=ten_gv, vai_tro='giang_vien').first()
                    if gv_obj:
                        lop_hoc.giang_vien = gv_obj
                
                lop_hoc.save()

                if created:
                    count_new += 1
                else:
                    count_upd += 1

            cache.delete(f'lop_import_progress_{task_id}')
            cache.delete(f'lop_import_status_{task_id}')
            messages.success(request, f'Đã xử lý xong: Thêm mới {count_new}, Cập nhật {count_upd} lớp học phần.')
        except Exception as exc:
            messages.error(request, f'Lỗi hệ thống khi nhập CSV: {exc}')

    return redirect('danh_sach_lop')


@kiem_tra_quyen_lich
def xuat_lop_hoc_csv(request):
    """Xuất danh sách lớp học phần ra CSV."""
    queryset, _ = _lay_queryset_lop_hoc_phan(request)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="danh_sach_lop_hoc_phan.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Tên lớp học phần', 'Mã học phần', 'Tên môn học', 'Khoa', 'Niên khóa', 'Số sinh viên'])

    for lop in queryset:
        writer.writerow([
            lop.ten_lop,
            lop.mon_hoc.ma_mon if lop.mon_hoc else '',
            lop.mon_hoc.ten_mon if lop.mon_hoc else '',
            lop.khoa,
            lop.nien_khoa,
            lop.so_sv,
        ])

    return response


@kiem_tra_quyen_lich
def danh_sach_lop(request):
    """Danh sÃ¡ch lá»›p há»c pháº§n."""
    queryset, filter_context = _lay_queryset_lop_hoc_phan(request)

    ds_khoa = LopHoc.objects.exclude(khoa='').values_list('khoa', flat=True).distinct().order_by('khoa')
    ds_nien_khoa = LopHoc.objects.exclude(nien_khoa='').values_list('nien_khoa', flat=True).distinct().order_by('nien_khoa')
    thong_ke = {
        'tong_lop': queryset.count(),
        'tong_mon': queryset.exclude(mon_hoc__isnull=True).values('mon_hoc_id').distinct().count(),
        'tong_sinh_vien': DangKyHocPhan.objects.filter(lop_hoc_id__in=queryset.values('id')).count(),
        'tong_khoa': queryset.exclude(khoa='').values('khoa').distinct().count(),
    }

    paginator = Paginator(queryset, 15)
    trang = request.GET.get('page')
    lop_hocs = paginator.get_page(trang)

    context = {
        'lop_hocs': lop_hocs,
        'ds_khoa': ds_khoa,
        'ds_nien_khoa': ds_nien_khoa,
        'thong_ke': thong_ke,
        'mau_csv': 'ten_lop,ma_mon,ten_mon,khoa,nien_khoa',
    }
    context.update(filter_context)
    return render(request, 'LichHoc/DanhSachLop.html', context)


@kiem_tra_quyen_lich
def them_lop(request):
    """ThÃªm lá»›p há»c pháº§n má»›i."""
    if request.method == 'POST':
        form = FormLopHoc(request.POST)
        if form.is_valid():
            lop = form.save()
            messages.success(request, f'ÄÃ£ thÃªm lá»›p {lop.ten_lop} thÃ nh cÃ´ng.')
            return redirect('danh_sach_lop')
    else:
        form = FormLopHoc()
    return render(request, 'LichHoc/ThemMoiLop.html', {'form': form})


@kiem_tra_quyen_lich
def chinh_sua_lop(request, pk):
    """Chá»‰nh sá»­a lá»›p há»c pháº§n."""
    lop = get_object_or_404(LopHoc.objects.select_related('mon_hoc'), pk=pk)
    if request.method == 'POST':
        form = FormLopHoc(request.POST, instance=lop)
        if form.is_valid():
            lop = form.save()
            messages.success(request, f'ÄÃ£ cáº­p nháº­t lá»›p {lop.ten_lop}.')
            return redirect('danh_sach_lop')
    else:
        form = FormLopHoc(instance=lop)
    return render(request, 'LichHoc/ChinhSuaLop.html', {'form': form, 'lop': lop})


@login_required
def khung_gio_hoc(request):
    """Trang hiển thị khung giờ tiết học theo quy định DUT."""
    return render(request, 'LichHoc/KhungGioHoc.html', {
        'khung_gio': KHUNG_GIO_TIET,
    })


@login_required
def thoi_khoa_bieu_tuan(request):
    """Thời khóa biểu dạng lưới theo tuần."""
    hom_nay = timezone.now().date()

    ngay_chon = request.GET.get('ngay', '')
    if ngay_chon:
        try:
            ngay_goc = datetime.strptime(ngay_chon, '%Y-%m-%d').date()
        except ValueError:
            ngay_goc = hom_nay
    else:
        ngay_goc = hom_nay

    dau_tuan = ngay_goc - timedelta(days=ngay_goc.weekday())
    cuoi_tuan = dau_tuan + timedelta(days=6)
    tuan_truoc = dau_tuan - timedelta(days=7)
    tuan_sau = dau_tuan + timedelta(days=7)

    thu_map = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'CN']
    ds_ngay = []
    for i in range(7):
        ngay = dau_tuan + timedelta(days=i)
        ds_ngay.append({'ngay': ngay, 'ten_thu': thu_map[i]})

    filters = {
        'ngay_hoc__gte': dau_tuan,
        'ngay_hoc__lte': cuoi_tuan,
    }

    is_personal = request.user.la_sinh_vien or request.user.la_giang_vien

    if is_personal:
        filters['trang_thai'] = 'hoat_dong'

    if request.user.la_sinh_vien:
        lop_ids = DangKyHocPhan.objects.filter(
            sinh_vien=request.user
        ).values_list('lop_hoc_id', flat=True)
        filters['lop_hoc_id__in'] = lop_ids
    elif request.user.la_giang_vien:
        filters['giang_vien'] = request.user

    lich_hocs = LichHoc.objects.filter(**filters).select_related(
        'mon_hoc', 'phong_hoc', 'giang_vien', 'lop_hoc'
    )

    ds_tiet = list(range(1, 15))

    if is_personal:
        # ─── PERSONAL VIEW (SV/GV): rowspan merged cells ───
        start_cells = {}
        skip_cells = set()
        for lich in lich_hocs:
            wd = lich.ngay_hoc.weekday()
            start = lich.tiet_bat_dau
            end = lich.tiet_ket_thuc
            rowspan = end - start + 1
            start_cells[(wd, start)] = {'lich': lich, 'rowspan': rowspan}
            for t in range(start + 1, end + 1):
                skip_cells.add((wd, t))

        grid_rows = []
        for tiet in range(1, 15):
            cells = []
            for wd in range(7):
                key = (wd, tiet)
                if key in skip_cells:
                    cells.append({'type': 'skip'})
                elif key in start_cells:
                    info = start_cells[key]
                    cells.append({'type': 'start', 'lich': info['lich'], 'rowspan': info['rowspan']})
                else:
                    cells.append({'type': 'empty'})
            grid_rows.append({'tiet': tiet, 'cells': cells})

        template_name = 'LichHoc/ThoiKhoaBieuTuan.html'
    else:
        # ─── ADMIN/GIAO_VU VIEW: list-based management ───
        # Day tab selection
        selected_day_str = request.GET.get('day', '')
        if selected_day_str:
            try:
                selected_day = datetime.strptime(selected_day_str, '%Y-%m-%d').date()
            except ValueError:
                selected_day = hom_nay
        else:
            selected_day = hom_nay if (dau_tuan <= hom_nay <= cuoi_tuan) else dau_tuan

        # Count per day for tabs
        for d_info in ds_ngay:
            d_info['count'] = lich_hocs.filter(ngay_hoc=d_info['ngay']).count()

        # Get schedules for selected day
        day_qs = lich_hocs.filter(ngay_hoc=selected_day).order_by('tiet_bat_dau')

        # SEARCH & FILTERS
        search_mon = request.GET.get('mon', '')
        search_gv = request.GET.get('gv', '')
        search_phong = request.GET.get('phong', '')
        search_lop = request.GET.get('lop', '')
        
        if search_mon:
            day_qs = day_qs.filter(
                Q(mon_hoc__ten_mon__icontains=search_mon) |
                Q(mon_hoc__ma_mon__icontains=search_mon)
            )
        if search_gv:
            day_qs = day_qs.filter(giang_vien__ho_ten__icontains=search_gv)
        if search_phong:
            day_qs = day_qs.filter(phong_hoc__ma_phong__icontains=search_phong)
        if search_lop:
            day_qs = day_qs.filter(Q(lop_hoc__ten_lop__icontains=search_lop) | Q(ma_lop__icontains=search_lop))

        day_active = day_qs.filter(trang_thai='hoat_dong')
        day_cancelled = day_qs.filter(trang_thai='da_huy')

        # Stats
        day_stats = {
            'total': day_qs.count(),
            'rooms': day_active.values('phong_hoc_id').distinct().count(),
            'gvs': day_active.values('giang_vien_id').distinct().count(),
            'cancelled': day_cancelled.count(),
        }

        # List mode
        list_mode = request.GET.get('view', 'all')
        if list_mode not in ['all', 'rooms', 'teachers', 'cancelled']:
            list_mode = 'all'

        if list_mode == 'rooms':
            room_rows = []
            for row in day_active.values('phong_hoc__ma_phong').annotate(so_lich=Count('id')).order_by('phong_hoc__ma_phong'):
                room_rows.append({
                    'ma_phong': row['phong_hoc__ma_phong'],
                    'so_lich': row['so_lich'],
                })
            list_items = room_rows
        elif list_mode == 'teachers':
            teacher_rows = []
            for row in day_active.values('giang_vien__ho_ten').annotate(so_lich=Count('id')).order_by('giang_vien__ho_ten'):
                teacher_rows.append({
                    'ho_ten': row['giang_vien__ho_ten'],
                    'so_lich': row['so_lich'],
                })
            list_items = teacher_rows
        elif list_mode == 'cancelled':
            list_items = day_cancelled
        else:
            list_items = day_qs

        paginator = Paginator(list_items, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        cho_duyet = YeuCauDoiLich.objects.filter(trang_thai='cho_duyet').count()

        grid_rows = []
        template_name = 'LichHoc/ThoiKhoaBieuTuanAdmin.html'

    context = {
        'ds_ngay': ds_ngay, 'ds_tiet': ds_tiet, 'grid_rows': grid_rows,
        'khung_gio': KHUNG_GIO_TIET, 'dau_tuan': dau_tuan, 'cuoi_tuan': cuoi_tuan,
        'tuan_truoc': tuan_truoc, 'tuan_sau': tuan_sau, 'hom_nay': hom_nay,
        'is_personal': is_personal, 'row_h': 48,
        # Admin-only
        'selected_day': locals().get('selected_day'),
        'page_obj': locals().get('page_obj'),
        'list_mode': locals().get('list_mode', 'all'),
        'day_stats': locals().get('day_stats', {}),
        'cho_duyet': locals().get('cho_duyet', 0),
        'search_mon': locals().get('search_mon', ''),
        'search_gv': locals().get('search_gv', ''),
        'search_phong': locals().get('search_phong', ''),
        'search_lop': locals().get('search_lop', ''),
    }
    return render(request, template_name, context)


# ══════════════════════════════════════════════════════════
# YÊU CẦU ĐỔI LỊCH
# ══════════════════════════════════════════════════════════

@login_required
def tao_yeu_cau_doi_lich(request, lich_pk):
    """GV tạo yêu cầu đổi lịch."""
    lich = get_object_or_404(LichHoc, pk=lich_pk)
    if not request.user.la_giang_vien:
        messages.error(request, 'Chỉ giảng viên mới có quyền gửi yêu cầu đổi lịch.')
        return redirect('danh_sach_lich')
    if lich.giang_vien != request.user:
        messages.error(request, 'Bạn chỉ có thể yêu cầu đổi lịch dạy của mình.')
        return redirect('danh_sach_lich')

    if request.method == 'POST':
        loai = request.POST.get('loai_yeu_cau', '')
        ly_do = request.POST.get('ly_do', '')
        phong_moi_id = request.POST.get('phong_moi', '')
        ngay_moi = request.POST.get('ngay_moi', '')
        tiet_bd = request.POST.get('tiet_moi_bat_dau', '')
        tiet_kt = request.POST.get('tiet_moi_ket_thuc', '')

        if not loai or not ly_do:
            messages.error(request, 'Vui lòng chọn loại yêu cầu và nhập lý do.')
            return redirect('tao_yeu_cau_doi_lich', lich_pk=lich.pk)

        yc = YeuCauDoiLich(
            lich_hoc=lich, nguoi_yeu_cau=request.user,
            loai_yeu_cau=loai, ly_do=ly_do,
        )
        # Validate phòng mới nếu đổi phòng
        if loai == 'doi_phong' and phong_moi_id:
            phong = PhongHoc.objects.filter(pk=phong_moi_id).first()
            if phong:
                trung = LichHoc.kiem_tra_trung_phong(
                    phong.id, lich.ngay_hoc, lich.tiet_bat_dau, lich.tiet_ket_thuc, lich.pk
                )
                if trung:
                    messages.error(request, f'Phòng {phong.ma_phong} đã có lịch trùng. Vui lòng chọn phòng khác.')
                    return redirect('tao_yeu_cau_doi_lich', lich_pk=lich.pk)
                yc.phong_moi = phong
        # Thông tin đổi giờ
        if loai == 'doi_gio':
            if ngay_moi:
                yc.ngay_moi = ngay_moi
            if tiet_bd:
                yc.tiet_moi_bat_dau = int(tiet_bd)
            if tiet_kt:
                yc.tiet_moi_ket_thuc = int(tiet_kt)
            # Validate
            if yc.ngay_moi and yc.tiet_moi_bat_dau and yc.tiet_moi_ket_thuc:
                trung_phong = LichHoc.kiem_tra_trung_phong(
                    lich.phong_hoc_id, yc.ngay_moi, yc.tiet_moi_bat_dau, yc.tiet_moi_ket_thuc, lich.pk
                )
                trung_gv = LichHoc.kiem_tra_trung_giang_vien(
                    lich.giang_vien_id, yc.ngay_moi, yc.tiet_moi_bat_dau, yc.tiet_moi_ket_thuc, lich.pk
                )
                if trung_phong:
                    messages.warning(request, 'Lưu ý: Phòng hiện tại bị trùng ở thời gian mới. Giáo vụ sẽ xem xét.')
                if trung_gv:
                    messages.warning(request, 'Lưu ý: Bạn có lịch trùng ở thời gian mới.')

        yc.save()
        messages.success(request, 'Đã gửi yêu cầu đổi lịch. Vui lòng chờ giáo vụ duyệt.')
        return redirect('lich_su_thay_doi')

    # GET: Hiển thị form
    phong_trong = PhongHoc.objects.exclude(trang_thai='bao_tri').order_by('ma_phong')
    return render(request, 'LichHoc/TaoYeuCauDoiLich.html', {
        'lich': lich, 'phong_trong': phong_trong,
    })


@login_required
def yeu_cau_hoan_lich(request, pk):
    """Giảng viên gửi yêu cầu hoàn lại lịch đã hủy."""
    lich = get_object_or_404(LichHoc, pk=pk)
    
    if not request.user.la_giang_vien or lich.giang_vien != request.user:
        messages.error(request, 'Bạn không có quyền thực hiện thao tác này.')
        return redirect('danh_sach_lich')
    
    if lich.trang_thai != 'da_huy':
        messages.warning(request, 'Lịch học này không ở trạng thái đã hủy.')
        return redirect('danh_sach_lich')
        
    # Kiểm tra xem đã có yêu cầu tương tự đang chờ duyệt chưa
    exists = YeuCauDoiLich.objects.filter(lich_hoc=lich, loai_yeu_cau='hoan_lich', trang_thai='cho_duyet').exists()
    if exists:
        messages.info(request, 'Yêu cầu hoàn lại lịch này đang chờ giáo vụ duyệt.')
        return redirect('danh_sach_lich')

    if request.method == 'POST':
        ly_do = request.POST.get('ly_do', '')
        if not ly_do:
            messages.error(request, 'Vui lòng nhập lý do khôi phục lịch.')
        else:
            YeuCauDoiLich.objects.create(
                lich_hoc=lich,
                nguoi_yeu_cau=request.user,
                loai_yeu_cau='hoan_lich',
                ly_do=ly_do
            )
            messages.success(request, 'Đã gửi yêu cầu hoàn lại lịch học. Vui lòng chờ giáo vụ duyệt.')
            return redirect('danh_sach_lich')
            
    return render(request, 'LichHoc/XacNhanHoanLich.html', {'lich': lich})


@login_required
def danh_sach_yeu_cau(request):
    """DS yêu cầu đổi lịch — Admin/GV duyệt, GV xem của mình."""
    # 1. Xác định ngày lọc
    hom_nay = timezone.localdate()
    ngay_loc = request.GET.get('ngay', '')
    if ngay_loc:
        try:
            ngay_hien_tai = datetime.strptime(ngay_loc, '%Y-%m-%d').date()
        except ValueError:
            ngay_hien_tai = hom_nay
    else:
        ngay_hien_tai = None # Mặc định không lọc ngày nếu chưa chọn

    # 2. Khởi tạo queryset theo vai trò
    if request.user.la_quan_tri or request.user.la_giao_vu:
        queryset = YeuCauDoiLich.objects.select_related(
            'lich_hoc', 'lich_hoc__mon_hoc', 'lich_hoc__phong_hoc', 'lich_hoc__giang_vien',
            'lich_hoc__lop_hoc', 'nguoi_yeu_cau', 'phong_moi', 'nguoi_duyet'
        ).all()
    elif request.user.la_giang_vien:
        queryset = YeuCauDoiLich.objects.filter(
            nguoi_yeu_cau=request.user
        ).select_related(
            'lich_hoc', 'lich_hoc__mon_hoc', 'lich_hoc__phong_hoc', 'nguoi_duyet', 'phong_moi'
        )
    else:
        messages.error(request, 'Bạn không có quyền truy cập.')
        return redirect('dashboard')

    # 3. Filters
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(
            Q(lich_hoc__mon_hoc__ten_mon__icontains=tu_khoa) |
            Q(lich_hoc__mon_hoc__ma_mon__icontains=tu_khoa) |
            Q(nguoi_yeu_cau__ho_ten__icontains=tu_khoa)
        )

    trang_thai_loc = request.GET.get('trang_thai', '')
    if trang_thai_loc:
        queryset = queryset.filter(trang_thai=trang_thai_loc)
    
    loai_loc = request.GET.get('loai', '')
    if loai_loc:
        queryset = queryset.filter(loai_yeu_cau=loai_loc)

    if ngay_hien_tai:
        queryset = queryset.filter(lich_hoc__ngay_hoc=ngay_hien_tai)

    queryset = queryset.order_by('-ngay_tao')

    # 4. Dữ liệu cho week selector
    day_for_week = ngay_hien_tai or hom_nay
    dau_tuan = day_for_week - timedelta(days=day_for_week.weekday())
    cuoi_tuan = dau_tuan + timedelta(days=6)
    tuan_truoc = dau_tuan - timedelta(days=7)
    tuan_sau = dau_tuan + timedelta(days=7)

    thu_map = {0: 'Thứ 2', 1: 'Thứ 3', 2: 'Thứ 4', 3: 'Thứ 5', 4: 'Thứ 6', 5: 'Thứ 7', 6: 'CN'}
    ds_ngay = []
    for offset in range(7):
        ngay = dau_tuan + timedelta(days=offset)
        ds_ngay.append({
            'ngay': ngay,
            'ten_thu': thu_map.get(ngay.weekday(), ''),
            'is_today': ngay == hom_nay,
            'is_selected': ngay == ngay_hien_tai,
        })

    paginator = Paginator(queryset, 15)
    trang = request.GET.get('page')
    yeu_caus = paginator.get_page(trang)

    # Stats
    cho_duyet_count = YeuCauDoiLich.objects.filter(trang_thai='cho_duyet').count()

    return render(request, 'LichHoc/DanhSachYeuCau.html', {
        'yeu_caus': yeu_caus, 
        'trang_thai_loc': trang_thai_loc,
        'loai_loc': loai_loc, 
        'cho_duyet': cho_duyet_count,
        'tu_khoa': tu_khoa,
        'ds_ngay': ds_ngay,
        'dau_tuan': dau_tuan,
        'cuoi_tuan': cuoi_tuan,
        'tuan_truoc': tuan_truoc,
        'tuan_sau': tuan_sau,
        'ngay_hien_tai': ngay_hien_tai,
        'hom_nay': hom_nay,
    })


@login_required
def chinh_sua_yeu_cau(request, pk):
    """Giảng viên chỉnh sửa yêu cầu của mình khi còn chờ duyệt."""
    yc = get_object_or_404(YeuCauDoiLich, pk=pk, nguoi_yeu_cau=request.user, trang_thai='cho_duyet')
    
    if request.method == 'POST':
        # Cập nhật thông tin từ form
        yc.loai_yeu_cau = request.POST.get('loai_yeu_cau', yc.loai_yeu_cau)
        
        phong_id = request.POST.get('phong_moi')
        if phong_id: yc.phong_moi_id = phong_id
            
        ngay_moi = request.POST.get('ngay_moi')
        if ngay_moi:
            yc.ngay_moi = datetime.strptime(ngay_moi, '%Y-%m-%d').date()
            
        tiet_bat_dau = request.POST.get('tiet_moi_bat_dau')
        if tiet_bat_dau: yc.tiet_moi_bat_dau = int(tiet_bat_dau)
            
        tiet_ket_thuc = request.POST.get('tiet_moi_ket_thuc')
        if tiet_ket_thuc: yc.tiet_moi_ket_thuc = int(tiet_ket_thuc)
            
        yc.ly_do = request.POST.get('ly_do', yc.ly_do)
        yc.save()
        
        messages.success(request, 'Đã cập nhật yêu cầu thành công.')
        return redirect('danh_sach_yeu_cau')

    from apps.PhongHoc.models import PhongHoc
    ds_phong = PhongHoc.objects.filter(trang_thai='trong')
    return render(request, 'LichHoc/ChinhSuaYeuCau.html', {
        'yc': yc, 
        'ds_phong': ds_phong,
        'khung_gio': KHUNG_GIO_TIET
    })


@kiem_tra_quyen_lich
def duyet_yeu_cau(request, pk):
    """Admin/GV duyệt hoặc từ chối yêu cầu đổi lịch."""
    yc = get_object_or_404(YeuCauDoiLich.objects.select_related(
        'lich_hoc', 'lich_hoc__mon_hoc', 'lich_hoc__phong_hoc', 'lich_hoc__giang_vien',
        'lich_hoc__lop_hoc', 'nguoi_yeu_cau', 'phong_moi',
    ), pk=pk)

    if request.method == 'POST':
        hanh_dong = request.POST.get('hanh_dong', '')
        ghi_chu = request.POST.get('ghi_chu_duyet', '')

        if hanh_dong == 'duyet':
            yc.trang_thai = 'da_duyet'
            yc.nguoi_duyet = request.user
            yc.ghi_chu_duyet = ghi_chu
            yc.ngay_duyet = timezone.now()
            yc.save()

            # Áp dụng thay đổi vào lịch gốc
            lich = yc.lich_hoc
            if yc.loai_yeu_cau == 'doi_phong' and yc.phong_moi:
                lich.phong_hoc = yc.phong_moi
                lich.save()
            elif yc.loai_yeu_cau == 'doi_gio':
                if yc.ngay_moi:
                    lich.ngay_hoc = yc.ngay_moi
                if yc.tiet_moi_bat_dau:
                    lich.tiet_bat_dau = yc.tiet_moi_bat_dau
                if yc.tiet_moi_ket_thuc:
                    lich.tiet_ket_thuc = yc.tiet_moi_ket_thuc
                lich.save()
            elif yc.loai_yeu_cau == 'huy_buoi':
                lich.trang_thai = 'da_huy'
                lich.save()
            elif yc.loai_yeu_cau == 'hoan_lich':
                lich.trang_thai = 'hoat_dong'
                lich.save()

            # Thông báo cho GV
            from apps.ThongBao.models import ThongBao
            ThongBao.objects.create(
                tieu_de=f'Yêu cầu đã được duyệt: {yc.get_loai_yeu_cau_display()}',
                noi_dung=f'Yêu cầu {yc.get_loai_yeu_cau_display()} cho môn {lich.mon_hoc} đã được duyệt.{" Ghi chú: " + ghi_chu if ghi_chu else ""}',
                loai='doi_lich', nguoi_tao=request.user, nguoi_nhan=yc.nguoi_yeu_cau,
            )
            messages.success(request, 'Đã duyệt yêu cầu và áp dụng thay đổi.')

        elif hanh_dong == 'tu_choi':
            yc.trang_thai = 'tu_choi'
            yc.nguoi_duyet = request.user
            yc.ghi_chu_duyet = ghi_chu
            yc.ngay_duyet = timezone.now()
            yc.save()

            from apps.ThongBao.models import ThongBao
            ThongBao.objects.create(
                tieu_de=f'Yêu cầu bị từ chối: {yc.get_loai_yeu_cau_display()}',
                noi_dung=f'Yêu cầu {yc.get_loai_yeu_cau_display()} cho môn {yc.lich_hoc.mon_hoc} đã bị từ chối.{" Lý do: " + ghi_chu if ghi_chu else ""}',
                loai='doi_lich', nguoi_tao=request.user, nguoi_nhan=yc.nguoi_yeu_cau,
            )
            messages.info(request, 'Đã từ chối yêu cầu.')

        return redirect('danh_sach_yeu_cau')

    return render(request, 'LichHoc/DuyetYeuCau.html', {'yc': yc})


@login_required
def lich_su_thay_doi(request):
    """Log lịch sử thay đổi — tất cả role có thể xem."""
    hom_nay = timezone.localdate()
    ngay_loc = request.GET.get('ngay', '')
    if ngay_loc:
        try:
            ngay_hien_tai = datetime.strptime(ngay_loc, '%Y-%m-%d').date()
        except ValueError:
            ngay_hien_tai = hom_nay
    else:
        ngay_hien_tai = hom_nay

    if request.user.la_sinh_vien:
        # SV xem log các lớp HP mình đăng ký
        lop_ids = DangKyHocPhan.objects.filter(
            sinh_vien=request.user
        ).values_list('lop_hoc_id', flat=True)
        queryset = YeuCauDoiLich.objects.filter(
            lich_hoc__lop_hoc_id__in=lop_ids
        ).exclude(trang_thai='cho_duyet')
    elif request.user.la_giang_vien:
        queryset = YeuCauDoiLich.objects.filter(nguoi_yeu_cau=request.user)
    else:
        queryset = YeuCauDoiLich.objects.all()

    # Lọc theo ngày hiện tại đang chọn
    queryset = queryset.filter(lich_hoc__ngay_hoc=ngay_hien_tai).order_by('-ngay_tao')

    # Thống kê nhanh theo trạng thái (sau khi lọc ngày)
    thong_ke = {
        'tong': queryset.count(),
        'cho_duyet': queryset.filter(trang_thai='cho_duyet').count(),
        'da_duyet': queryset.filter(trang_thai='da_duyet').count(),
        'tu_choi': queryset.filter(trang_thai='tu_choi').count(),
    }

    queryset = queryset.select_related(
        'lich_hoc', 'lich_hoc__mon_hoc', 'lich_hoc__phong_hoc', 'lich_hoc__giang_vien',
        'nguoi_yeu_cau', 'phong_moi', 'nguoi_duyet'
    )

    # Dữ liệu tuần hiện tại để hiển thị nút thứ
    dau_tuan = ngay_hien_tai - timedelta(days=ngay_hien_tai.weekday())
    cuoi_tuan = dau_tuan + timedelta(days=6)
    tuan_truoc = dau_tuan - timedelta(days=7)
    tuan_sau = dau_tuan + timedelta(days=7)

    thu_map = {0: 'Thứ 2', 1: 'Thứ 3', 2: 'Thứ 4', 3: 'Thứ 5', 4: 'Thứ 6', 5: 'Thứ 7', 6: 'CN'}
    ds_ngay = []
    for offset in range(7):
        ngay = dau_tuan + timedelta(days=offset)
        ds_ngay.append({
            'ngay': ngay,
            'ten_thu': thu_map.get(ngay.weekday(), ''),
            'is_today': ngay == hom_nay,
            'is_selected': ngay == ngay_hien_tai,
        })

    paginator = Paginator(queryset, 20)
    trang = request.GET.get('page')
    logs = paginator.get_page(trang)

    context = {
        'logs': logs,
        'thong_ke': thong_ke,
        'dau_tuan': dau_tuan,
        'cuoi_tuan': cuoi_tuan,
        'tuan_truoc': tuan_truoc,
        'tuan_sau': tuan_sau,
        'ds_ngay': ds_ngay,
        'ngay_hien_tai': ngay_hien_tai,
        'hom_nay': hom_nay,
    }
    return render(request, 'LichHoc/LichSuThayDoi.html', context)
