from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
import io
import csv

from .models import NguoiDung, LopSinhHoat
from .forms import FormDangNhap, FormNguoiDung, FormLopSinhHoat


# ──────────────────────────────────────
# XÁC THỰC
# ──────────────────────────────────────

def dang_nhap(request):
    """Xử lý đăng nhập."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = FormDangNhap(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Chào mừng {user.ho_ten}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    else:
        form = FormDangNhap()
    return render(request, 'NguoiDung/DangNhap.html', {'form': form})


def dang_xuat(request):
    """Xử lý đăng xuất."""
    logout(request)
    messages.info(request, 'Đã đăng xuất thành công.')
    return redirect('dang_nhap')


# ──────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────

@login_required
def dashboard(request):
    """Redirect đến dashboard theo vai trò."""
    user = request.user
    if user.la_quan_tri:
        return redirect('dashboard_quan_tri')
    elif user.la_giao_vu:
        return redirect('dashboard_giao_vu')
    elif user.la_giang_vien:
        return redirect('dashboard_giang_vien')
    else:
        return redirect('dashboard_sinh_vien')


@login_required
def dashboard_quan_tri(request):
    from apps.PhongHoc.models import PhongHoc
    from apps.ThietBi.models import ThietBi
    from apps.ThongBao.models import ThongBao
    from apps.LichHoc.models import LichHoc
    from django.utils import timezone
    from datetime import timedelta
    
    hom_nay = timezone.now().date()
    # Thống kê mật độ lịch học (7 ngày tới)
    chart_data = []
    chart_labels = []
    thu_map = {0: 'Thứ 2', 1: 'Thứ 3', 2: 'Thứ 4', 3: 'Thứ 5', 4: 'Thứ 6', 5: 'Thứ 7', 6: 'CN'}
    for i in range(7):
        ngay = hom_nay + timedelta(days=i)
        count = LichHoc.objects.filter(ngay_hoc=ngay, trang_thai='hoat_dong').count()
        chart_data.append(count)
        if i == 0:
            chart_labels.append("Hôm nay")
        else:
            chart_labels.append(thu_map[ngay.weekday()])

    context = {
        'tong_tai_khoan': NguoiDung.objects.count(),
        'tong_phong': PhongHoc.objects.count(),
        'phong_bao_tri': PhongHoc.objects.filter(trang_thai='bao_tri').count(),
        'thiet_bi_hong': ThietBi.objects.filter(trang_thai='hong').count(),
        'recent_users': NguoiDung.objects.order_by('-date_joined')[:5],
        'recent_notifications': ThongBao.objects.order_by('-ngay_tao')[:5],
        'chart_data': chart_data,
        'chart_labels': chart_labels,
        'today': hom_nay,
    }
    return render(request, 'Dashboard/QuanTriVien.html', context)


@login_required
def dashboard_giao_vu(request):
    """Dashboard cho giáo vụ."""
    from apps.PhongHoc.models import PhongHoc
    from apps.LichHoc.models import LichHoc, YeuCauDoiLich
    from django.utils import timezone
    from datetime import timedelta
    
    hom_nay = timezone.now().date()
    
    # Thống kê lịch dạy trong 7 ngày tới
    chart_data = []
    chart_labels = []
    thu_map = {0: 'Thứ 2', 1: 'Thứ 3', 2: 'Thứ 4', 3: 'Thứ 5', 4: 'Thứ 6', 5: 'Thứ 7', 6: 'CN'}
    for i in range(7):
        ngay = hom_nay + timedelta(days=i)
        count = LichHoc.objects.filter(ngay_hoc=ngay, trang_thai='hoat_dong').count()
        chart_data.append(count)
        if i == 0:
            chart_labels.append("Hôm nay")
        else:
            chart_labels.append(thu_map[ngay.weekday()])

    phong_dang_dung = PhongHoc.objects.filter(trang_thai='dang_su_dung').count()
    tong_phong = PhongHoc.objects.count()
    phong_pct = (phong_dang_dung * 100 // tong_phong) if tong_phong > 0 else 0

    context = {
        'lich_hom_nay': LichHoc.objects.filter(ngay_hoc=hom_nay, trang_thai='hoat_dong').count(),
        'phong_trong': PhongHoc.objects.filter(trang_thai='trong').count(),
        'phong_dang_dung': phong_dang_dung,
        'tong_phong': tong_phong,
        'phong_pct': phong_pct,
        'yeu_cau_cho': YeuCauDoiLich.objects.filter(trang_thai='cho_duyet').count(),
        'recent_requests': YeuCauDoiLich.objects.order_by('-ngay_tao')[:5],
        'chart_data': chart_data,
        'chart_labels': chart_labels,
        'today': hom_nay,
    }
    return render(request, 'Dashboard/GiaoVu.html', context)


@login_required
def dashboard_giang_vien(request):
    """Dashboard cho giảng viên."""
    from apps.LichHoc.models import LichHoc, YeuCauDoiLich
    from apps.ThongBao.models import ThongBao
    from django.utils import timezone
    from datetime import timedelta
    
    hom_nay = timezone.now().date()
    dau_tuan = hom_nay - timedelta(days=hom_nay.weekday())
    cuoi_tuan = dau_tuan + timedelta(days=6)
    
    # 1. Lịch dạy hôm nay
    lich_day = LichHoc.objects.filter(
        giang_vien=request.user,
        ngay_hoc=hom_nay,
        trang_thai='hoat_dong',
    ).select_related('phong_hoc', 'lop_hoc').order_by('tiet_bat_dau')
    
    # 2. Thông báo mới
    thong_bao = ThongBao.objects.filter(
        nguoi_nhan=request.user
    ).order_by('-ngay_tao')[:5]
    thong_bao_moi = ThongBao.objects.filter(nguoi_nhan=request.user, da_doc=False).count()
    
    # 3. Yêu cầu đổi lịch gần đây
    lich_su_yeu_cau = YeuCauDoiLich.objects.filter(
        nguoi_yeu_cau=request.user
    ).order_by('-ngay_tao')[:5]
    yeu_cau_cho = YeuCauDoiLich.objects.filter(nguoi_yeu_cau=request.user, trang_thai='cho_duyet').count()
    
    # 4. Thống kê tiết dạy trong tuần
    lich_tuan = LichHoc.objects.filter(
        giang_vien=request.user,
        ngay_hoc__range=[dau_tuan, cuoi_tuan],
        trang_thai='hoat_dong'
    )
    tong_tiet_tuan = 0
    for l in lich_tuan:
        tong_tiet_tuan += (l.tiet_ket_thuc - l.tiet_bat_dau + 1)
        
    # Chart data (tổng tiết mỗi ngày trong tuần)
    chart_data = []
    for i in range(7):
        ngay = dau_tuan + timedelta(days=i)
        tiet_ngay = sum((l.tiet_ket_thuc - l.tiet_bat_dau + 1) for l in lich_tuan if l.ngay_hoc == ngay)
        chart_data.append(tiet_ngay)

    context = {
        'lich_day': lich_day,
        'thong_bao': thong_bao,
        'thong_bao_moi': thong_bao_moi,
        'lich_su_yeu_cau': lich_su_yeu_cau,
        'yeu_cau_cho': yeu_cau_cho,
        'tong_tiet_tuan': tong_tiet_tuan,
        'chart_data': chart_data,
        'today': hom_nay,
    }
    return render(request, 'Dashboard/GiangVien.html', context)


@login_required
def dashboard_sinh_vien(request):
    """Dashboard cho sinh viên."""
    from apps.LichHoc.models import LichHoc, DangKyHocPhan
    from apps.ThongBao.models import ThongBao
    from django.utils import timezone
    from datetime import timedelta
    
    hom_nay = timezone.now().date()
    dau_tuan = hom_nay - timedelta(days=hom_nay.weekday())
    cuoi_tuan = dau_tuan + timedelta(days=6)
    
    # Lấy danh sách lớp HP mà SV đã đăng ký
    lop_ids = DangKyHocPhan.objects.filter(
        sinh_vien=request.user
    ).values_list('lop_hoc_id', flat=True)
    
    if not lop_ids:
        return render(request, 'Dashboard/SinhVien.html', {
            'lich_hoc': [], 
            'chua_dang_ky': True,
            'today': hom_nay
        })
    
    # 1. Lịch học hôm nay
    lich_hoc = LichHoc.objects.filter(
        ngay_hoc=hom_nay,
        trang_thai='hoat_dong',
        lop_hoc_id__in=lop_ids,
    ).select_related('phong_hoc', 'giang_vien', 'lop_hoc').order_by('tiet_bat_dau')
    
    # 2. Thông báo mới nhất
    thong_bao = ThongBao.objects.filter(
        nguoi_nhan=request.user
    ).order_by('-ngay_tao')[:5]
    thong_bao_moi = ThongBao.objects.filter(nguoi_nhan=request.user, da_doc=False).count()
    
    # 3. Thống kê học tập trong tuần
    lich_tuan = LichHoc.objects.filter(
        lop_hoc_id__in=lop_ids,
        ngay_hoc__range=[dau_tuan, cuoi_tuan],
        trang_thai='hoat_dong'
    )
    tong_tiet_tuan = sum((l.tiet_ket_thuc - l.tiet_bat_dau + 1) for l in lich_tuan)
    
    # Dữ liệu biểu đồ (số tiết học mỗi ngày)
    chart_data = []
    for i in range(7):
        ngay = dau_tuan + timedelta(days=i)
        tiet_ngay = sum((l.tiet_ket_thuc - l.tiet_bat_dau + 1) for l in lich_tuan if l.ngay_hoc == ngay)
        chart_data.append(tiet_ngay)
        
    context = {
        'lich_hoc': lich_hoc,
        'thong_bao': thong_bao,
        'thong_bao_moi': thong_bao_moi,
        'tong_tiet_tuan': tong_tiet_tuan,
        'chart_data': chart_data,
        'today': hom_nay,
        'tong_mon': len(lop_ids),
    }
    return render(request, 'Dashboard/SinhVien.html', context)


# ──────────────────────────────────────
# QUẢN LÝ TÀI KHOẢN (Admin only)
# ──────────────────────────────────────

@login_required
def thong_tin_ca_nhan(request):
    """Trang thông tin cá nhân của người dùng hiện tại."""
    user = request.user
    from apps.LichHoc.models import LichHoc, DangKyHocPhan, YeuCauDoiLich
    
    # Thống kê bổ sung cho profile
    stats = {
        'ngay_tham_gia': user.date_joined.date(),
    }
    
    if user.la_sinh_vien:
        stats['tong_mon'] = DangKyHocPhan.objects.filter(sinh_vien=user).count()
        stats['lich_tuan_nay'] = LichHoc.objects.filter(
            lop_hoc_id__in=DangKyHocPhan.objects.filter(sinh_vien=user).values_list('lop_hoc_id', flat=True),
            ngay_hoc__range=[timezone.now().date(), timezone.now().date() + timedelta(days=7)]
        ).count()
    elif user.la_giang_vien:
        stats['tong_lich'] = LichHoc.objects.filter(giang_vien=user).count()
        stats['yeu_cau_cho'] = YeuCauDoiLich.objects.filter(nguoi_yeu_cau=user, trang_thai='cho_duyet').count()
    elif user.la_giao_vu or user.la_quan_tri:
        stats['tong_yeu_cau_cho'] = YeuCauDoiLich.objects.filter(trang_thai='cho_duyet').count()
        stats['he_thong_mon'] = LichHoc.objects.count()

    if request.method == 'POST':
        # Cho phép cập nhật thông tin cơ bản
        ho_ten = request.POST.get('ho_ten')
        email = request.POST.get('email')
        if ho_ten:
            user.ho_ten = ho_ten
        if email is not None:
            user.email = email
        user.save()
        messages.success(request, 'Cập nhật thông tin thành công.')
        return redirect('thong_tin_ca_nhan')
        
    return render(request, 'NguoiDung/ThongTinCaNhan.html', {'user': user, 'stats': stats})

def kiem_tra_quan_tri(view_func):
    """Decorator kiểm tra quyền quản trị viên."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.la_quan_tri:
            messages.error(request, 'Bạn không có quyền truy cập.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@kiem_tra_quan_tri
def danh_sach_nguoi_dung(request):
    """Danh sách người dùng với phân trang linh hoạt."""
    queryset = NguoiDung.objects.all().select_related('lop_sinh_hoat').order_by('-date_joined')
    
    # Tìm kiếm
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(
            Q(ho_ten__icontains=tu_khoa) | 
            Q(ma_so__icontains=tu_khoa) | 
            Q(username__icontains=tu_khoa)
        )
        
    # Lọc vai trò
    vai_tro_loc = request.GET.get('vai_tro', '')
    if vai_tro_loc:
        queryset = queryset.filter(vai_tro=vai_tro_loc)
        
    # Số lượng phân trang
    per_page = request.GET.get('per_page', '20')
    try:
        per_page = int(per_page)
    except:
        per_page = 20

    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'nguoi_dungs': page_obj,
        'tu_khoa': tu_khoa,
        'vai_tro_loc': vai_tro_loc,
        'per_page': per_page,
        'vai_tro_choices': NguoiDung.VaiTro.choices
    }
    return render(request, 'NguoiDung/DanhSach.html', context)


@kiem_tra_quan_tri
def xoa_hang_loat_nguoi_dung(request):
    """Xóa nhiều người dùng cùng lúc."""
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        if user_ids:
            # Không cho phép tự xóa chính mình
            count, _ = NguoiDung.objects.filter(id__in=user_ids).exclude(id=request.user.id).delete()
            messages.success(request, f'Đã xóa thành công {count} tài khoản.')
        else:
            messages.warning(request, 'Vui lòng chọn ít nhất một tài khoản để xóa.')
    return redirect('danh_sach_nguoi_dung')


@kiem_tra_quan_tri
def them_nguoi_dung(request):
    """Thêm tài khoản mới."""
    if request.method == 'POST':
        form = FormNguoiDung(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password_raw')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, f'Đã thêm tài khoản "{user.ho_ten}" thành công.')
            return redirect('danh_sach_nguoi_dung')
    else:
        form = FormNguoiDung()
    return render(request, 'NguoiDung/ThemMoi.html', {'form': form})


@kiem_tra_quan_tri
def chinh_sua_nguoi_dung(request, pk):
    """Chỉnh sửa tài khoản."""
    nguoi_dung = get_object_or_404(NguoiDung, pk=pk)
    if request.method == 'POST':
        form = FormNguoiDung(request.POST, instance=nguoi_dung)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật tài khoản "{nguoi_dung.ho_ten}".')
            return redirect('danh_sach_nguoi_dung')
    else:
        form = FormNguoiDung(instance=nguoi_dung)
    return render(request, 'NguoiDung/ChinhSua.html', {'form': form, 'nguoi_dung': nguoi_dung})


@kiem_tra_quan_tri
def xoa_nguoi_dung(request, pk):
    """Xóa tài khoản."""
    nguoi_dung = get_object_or_404(NguoiDung, pk=pk)
    if request.method == 'POST':
        ten = nguoi_dung.ho_ten
        nguoi_dung.delete()
        messages.success(request, f'Đã xóa tài khoản "{ten}".')
        return redirect('danh_sach_nguoi_dung')
    return render(request, 'NguoiDung/XacNhanXoa.html', {'nguoi_dung': nguoi_dung})


@kiem_tra_quan_tri
def reset_mat_khau(request, pk):
    """Đặt lại mật khẩu nhanh cho người dùng."""
    nguoi_dung = get_object_or_404(NguoiDung, pk=pk)
    if request.method == 'POST':
        moi = request.POST.get('password')
        if moi:
            nguoi_dung.set_password(moi)
            nguoi_dung.save()
            messages.success(request, f'Đã đặt lại mật khẩu cho "{nguoi_dung.ho_ten}".')
        else:
            messages.error(request, 'Vui lòng nhập mật khẩu mới.')
    return redirect('danh_sach_nguoi_dung')


from django.core.cache import cache
import json
from django.http import JsonResponse

@kiem_tra_quan_tri
def lay_tien_do_nhap_csv(request):
    """Trả về tiến độ nhập CSV thực tế từ cache."""
    task_id = request.GET.get('task_id')
    progress = cache.get(f'import_progress_{task_id}', 0)
    status = cache.get(f'import_status_{task_id}', 'Đang xử lý...')
    return JsonResponse({'progress': progress, 'status': status})

@kiem_tra_quan_tri
@transaction.atomic
def nhap_nguoi_dung_csv(request):
    """Nhập danh sách người dùng từ file CSV với quy tắc kiểm soát nghiêm ngặt."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        try:
            # 1. Xử lý mã hóa đa nền tảng để hỗ trợ tiếng Việt tuyệt đối
            file_data = csv_file.read()
            encodings = ['utf-8-sig', 'utf-16', 'windows-1258', 'utf-8']
            decoded_file = None
            
            for enc in encodings:
                try:
                    decoded_file = file_data.decode(enc)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if not decoded_file:
                messages.error(request, 'Không thể nhận diện bảng mã của file. Vui lòng lưu file ở định dạng CSV UTF-8.')
                return redirect('danh_sach_nguoi_dung')
                
            io_string = io.StringIO(decoded_file)
            
            # Tự động nhận diện dấu ngăn cách (Phẩy , hoặc Chấm phẩy ;)
            try:
                dialect = csv.Sniffer().sniff(decoded_file[:2000], delimiters=',;')
                reader = list(csv.DictReader(io_string, dialect=dialect))
            except Exception:
                io_string.seek(0)
                reader = list(csv.DictReader(io_string))
            
            if not reader:
                messages.error(request, 'File CSV không có dữ liệu.')
                return redirect('danh_sach_nguoi_dung')

            errors = []
            seen_usernames = set()
            
            # PHASE 1: Kiểm tra tính hợp lệ sơ bộ
            ghi_de = request.POST.get('ghi_de') == 'on'
            
            for index, row in enumerate(reader, start=2):
                username = row.get('username', '').strip()
                ho_ten = row.get('ho_ten', '').strip()
                vai_tro = row.get('vai_tro', '').strip()
                
                if not username or not ho_ten or not vai_tro:
                    errors.append(f"Dòng {index}: Thiếu thông tin bắt buộc (username, ho_ten, vai_tro).")
                    continue
                
                if username in seen_usernames:
                    errors.append(f"Dòng {index}: Username '{username}' trùng lặp trong file.")
                seen_usernames.add(username)
                
                if not ghi_de and NguoiDung.objects.filter(username=username).exists():
                    errors.append(f"Dòng {index}: Username '{username}' đã tồn tại trong hệ thống.")

            if errors:
                messages.error(request, f'Lỗi dữ liệu CSV:<br>{"<br>".join(errors[:10])}')
                return redirect('danh_sach_nguoi_dung')

            # PHASE 2: Thực hiện Import với Transaction
            task_id = request.POST.get('task_id', 'manual')
            total_rows = len(reader)
            count_new = 0
            count_upd = 0
            
            with transaction.atomic():
                for index, row in enumerate(reader, start=1):
                    # Cập nhật tiến độ vào cache để polling
                    percent = int((index / total_rows) * 100)
                    cache.set(f'import_progress_{task_id}', percent, 300)
                    cache.set(f'import_status_{task_id}', f"Đang xử lý {index}/{total_rows}...", 300)
                    
                    username = row.get('username', '').strip()
                    password = row.get('password', '').strip()
                    ho_ten = row.get('ho_ten', '').strip()
                    ma_so = row.get('ma_so', '').strip()
                    vai_tro = row.get('vai_tro', 'sinh_vien').strip()
                    ten_lop = row.get('lop_sinh_hoat', '').strip().upper()
                    
                    lop_sh = None
                    if ten_lop and vai_tro == 'sinh_vien':
                        lop_sh, _ = LopSinhHoat.objects.get_or_create(ten_lop=ten_lop)
                        
                    user, created = NguoiDung.objects.get_or_create(username=username)
                    user.ho_ten = ho_ten
                    user.ma_so = ma_so
                    user.vai_tro = vai_tro
                    user.email = row.get('email', '').strip()
                    user.lop_sinh_hoat = lop_sh
                    
                    if password:
                        user.set_password(password)
                    elif created:
                        user.set_password('123456aA@') # Mật khẩu mặc định
                    
                    user.save()
                    if created: count_new += 1
                    else: count_upd += 1
                
                # Hoàn tất
                cache.delete(f'import_progress_{task_id}')
                cache.delete(f'import_status_{task_id}')
                messages.success(request, f'Nhập dữ liệu thành công: Thêm mới {count_new}, Cập nhật {count_upd} tài khoản.')
                
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống khi xử lý CSV: {str(e)}')
            
    return redirect('danh_sach_nguoi_dung')


@kiem_tra_quan_tri
def xuat_nguoi_dung_csv(request):
    """Xuất danh sách người dùng hiện tại ra file CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="danh_sach_nguoi_dung.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow(['Tên đăng nhập', 'Họ và tên', 'Mã số', 'Email', 'Lớp sinh hoạt', 'Vai trò', 'Ngày tham gia'])
    
    # Lấy lại queryset giống trang danh sách (có thể tối ưu bằng cách lưu session filter)
    queryset = NguoiDung.objects.all().select_related('lop_sinh_hoat')
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(Q(ho_ten__icontains=tu_khoa) | Q(ma_so__icontains=tu_khoa))
    vai_tro_loc = request.GET.get('vai_tro', '')
    if vai_tro_loc:
        queryset = queryset.filter(vai_tro=vai_tro_loc)
        
    for u in queryset:
        writer.writerow([
            u.username, u.ho_ten, u.ma_so, u.email,
            u.lop_sinh_hoat.ten_lop if u.lop_sinh_hoat else '-',
            u.get_vai_tro_display(), u.date_joined.strftime('%d/%m/%Y')
        ])
        
    return response


@kiem_tra_quan_tri
def danh_sach_lop_sinh_hoat(request):
    """Quản lý danh sách lớp sinh hoạt."""
    queryset = LopSinhHoat.objects.annotate(so_sv=Count('sinh_viens')).order_by('ten_lop')
    
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(Q(ten_lop__icontains=tu_khoa) | Q(khoa_quan_ly__icontains=tu_khoa))
    
    khoa_loc = request.GET.get('khoa', '')
    if khoa_loc:
        queryset = queryset.filter(khoa_quan_ly=khoa_loc)
        
    khoa_hoc_loc = request.GET.get('khoa_hoc', '')
    if khoa_hoc_loc:
        queryset = queryset.filter(khoa_hoc=khoa_hoc_loc)
        
    # Thống kê nhanh
    thong_ke = {
        'tong_lop': queryset.count(),
        'tong_sv': sum(l.so_sv for l in queryset)
    }
    
    # Danh sách khoa và khóa học duy nhất để làm filter
    ds_khoa = LopSinhHoat.objects.values_list('khoa_quan_ly', flat=True).distinct().order_by('khoa_quan_ly')
    ds_khoa_hoc = LopSinhHoat.objects.values_list('khoa_hoc', flat=True).distinct().order_by('-khoa_hoc')

    context = {
        'lops': queryset,
        'tu_khoa': tu_khoa,
        'khoa_loc': khoa_loc,
        'khoa_hoc_loc': khoa_hoc_loc,
        'ds_khoa': ds_khoa,
        'ds_khoa_hoc': ds_khoa_hoc,
        'thong_ke': thong_ke
    }
    return render(request, 'NguoiDung/LopSinhHoat/DanhSach.html', context)


@kiem_tra_quan_tri
def sua_lop_sinh_hoat(request, pk):
    """Chỉnh sửa thông tin lớp sinh hoạt."""
    lop = get_object_or_404(LopSinhHoat, pk=pk)
    if request.method == 'POST':
        form = FormLopSinhHoat(request.POST, instance=lop)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật thông tin lớp {lop.ten_lop}.')
            return redirect('danh_sach_lop_sinh_hoat')
    else:
        form = FormLopSinhHoat(instance=lop)
    return render(request, 'NguoiDung/LopSinhHoat/ChinhSua.html', {'form': form, 'lop': lop})


@kiem_tra_quan_tri
def xoa_lop_sinh_hoat(request, pk):
    """Xóa lớp sinh hoạt."""
    lop = get_object_or_404(LopSinhHoat, pk=pk)
    if request.method == 'POST':
        ten = lop.ten_lop
        lop.delete()
        messages.success(request, f'Đã xóa lớp {ten}.')
        return redirect('danh_sach_lop_sinh_hoat')
    return redirect('danh_sach_lop_sinh_hoat')
