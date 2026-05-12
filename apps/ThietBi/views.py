from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import ThietBi, BaoHong
from .forms import FormThietBi, FormBaoHong
from apps.NguoiDung.models import NguoiDung


def kiem_tra_quyen_thiet_bi(view_func):
    """Decorator: chỉ quản trị viên và giáo vụ."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dang_nhap')
        if not (request.user.la_quan_tri or request.user.la_giao_vu):
            messages.error(request, 'Bạn không có quyền truy cập.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def danh_sach_thiet_bi(request):
    """Danh sách thiết bị."""
    queryset = ThietBi.objects.select_related('phong_hoc').all()

    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(ten_thiet_bi__icontains=tu_khoa)

    trang_thai = request.GET.get('trang_thai', '')
    if trang_thai:
        queryset = queryset.filter(trang_thai=trang_thai)

    phong = request.GET.get('phong', '')
    if phong:
        queryset = queryset.filter(phong_hoc_id=phong)

    paginator = Paginator(queryset, 15)
    trang = request.GET.get('page')
    thiet_bis = paginator.get_page(trang)

    from apps.PhongHoc.models import PhongHoc
    context = {
        'thiet_bis': thiet_bis,
        'tu_khoa': tu_khoa,
        'trang_thai_loc': trang_thai,
        'phong_loc': phong,
        'trang_thai_choices': ThietBi.TrangThai.choices,
        'ds_phong': PhongHoc.objects.all(),
    }
    return render(request, 'ThietBi/DanhSach.html', context)


@kiem_tra_quyen_thiet_bi
def them_thiet_bi(request):
    """Thêm thiết bị mới."""
    if request.method == 'POST':
        form = FormThietBi(request.POST)
        if form.is_valid():
            tb = form.save()
            messages.success(request, f'Đã thêm thiết bị "{tb.ten_thiet_bi}".')
            return redirect('danh_sach_thiet_bi')
    else:
        form = FormThietBi()
    return render(request, 'ThietBi/ThemMoi.html', {'form': form})


@kiem_tra_quyen_thiet_bi
def chinh_sua_thiet_bi(request, pk):
    """Chỉnh sửa thiết bị."""
    tb = get_object_or_404(ThietBi, pk=pk)
    if request.method == 'POST':
        form = FormThietBi(request.POST, instance=tb)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật thiết bị "{tb.ten_thiet_bi}".')
            return redirect('danh_sach_thiet_bi')
    else:
        form = FormThietBi(instance=tb)
    return render(request, 'ThietBi/ChinhSua.html', {'form': form, 'thiet_bi': tb})


@kiem_tra_quyen_thiet_bi
def xoa_thiet_bi(request, pk):
    """Xóa thiết bị."""
    tb = get_object_or_404(ThietBi, pk=pk)
    if request.method == 'POST':
        ten = tb.ten_thiet_bi
        tb.delete()
        messages.success(request, f'Đã xóa thiết bị "{ten}".')
        return redirect('danh_sach_thiet_bi')
    return render(request, 'ThietBi/XacNhanXoa.html', {'thiet_bi': tb})


@login_required
def bao_hong(request):
    """Báo hỏng thiết bị - giảng viên, giáo vụ, quản trị."""
    if request.user.la_sinh_vien:
        messages.error(request, 'Sinh viên không có quyền báo hỏng.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = FormBaoHong(request.POST)
        if form.is_valid():
            bh = form.save(commit=False)
            bh.nguoi_bao = request.user
            bh.save()
            # Đánh dấu thiết bị hỏng
            bh.thiet_bi.trang_thai = 'hong'
            bh.thiet_bi.save()
            # Tạo thông báo
            from apps.ThongBao.models import ThongBao
            ds_nguoi_nhan = NguoiDung.objects.filter(
                vai_tro__in=[NguoiDung.VaiTro.QUAN_TRI, NguoiDung.VaiTro.GIAO_VU]
            )
            for nguoi in ds_nguoi_nhan:
                ThongBao.objects.create(
                    tieu_de=f'Báo hỏng: {bh.thiet_bi.ten_thiet_bi}',
                    noi_dung=f'{request.user.ho_ten} báo hỏng {bh.thiet_bi.ten_thiet_bi} '
                             f'tại phòng {bh.thiet_bi.phong_hoc.ma_phong}. Mô tả: {bh.mo_ta}',
                    loai='bao_tri',
                    nguoi_tao=request.user,
                    nguoi_nhan=nguoi,
                )
            messages.success(request, 'Đã gửi báo hỏng thành công.')
            return redirect('danh_sach_thiet_bi')
    else:
        form = FormBaoHong()
    return render(request, 'ThietBi/BaoHong.html', {'form': form})


@login_required
def danh_sach_bao_hong(request):
    """Danh sách báo hỏng."""
    if not (request.user.la_quan_tri or request.user.la_giao_vu):
        messages.error(request, 'Bạn không có quyền truy cập.')
        return redirect('dashboard')

    queryset = BaoHong.objects.select_related('thiet_bi', 'thiet_bi__phong_hoc', 'nguoi_bao').all()

    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(thiet_bi__ten_thiet_bi__icontains=tu_khoa)

    trang_thai = request.GET.get('trang_thai', '')
    if trang_thai:
        queryset = queryset.filter(trang_thai=trang_thai)

    phong = request.GET.get('phong', '')
    if phong:
        queryset = queryset.filter(thiet_bi__phong_hoc_id=phong)

    nguoi_bao = request.GET.get('nguoi_bao', '')
    if nguoi_bao:
        queryset = queryset.filter(nguoi_bao_id=nguoi_bao)

    thoi_gian = request.GET.get('thoi_gian', '')
    if thoi_gian:
        today = datetime.now().date()
        if thoi_gian == 'hom_nay':
            queryset = queryset.filter(ngay_bao__date=today)
        elif thoi_gian == 'hom_qua':
            queryset = queryset.filter(ngay_bao__date=today - timedelta(days=1))
        elif thoi_gian == 'tuan_nay':
            queryset = queryset.filter(ngay_bao__date__gte=today - timedelta(days=today.weekday()))

    tu_ngay = request.GET.get('tu_ngay', '')
    if tu_ngay:
        try:
            tu_ngay_date = datetime.strptime(tu_ngay, '%Y-%m-%d').date()
            queryset = queryset.filter(ngay_bao__date__gte=tu_ngay_date)
        except ValueError:
            tu_ngay = ''

    den_ngay = request.GET.get('den_ngay', '')
    if den_ngay:
        try:
            den_ngay_date = datetime.strptime(den_ngay, '%Y-%m-%d').date()
            queryset = queryset.filter(ngay_bao__date__lte=den_ngay_date)
        except ValueError:
            den_ngay = ''

    paginator = Paginator(queryset, 25)
    trang = request.GET.get('page')
    bao_hongs = paginator.get_page(trang)

    from apps.PhongHoc.models import PhongHoc
    ds_nguoi_bao = BaoHong.objects.values_list('nguoi_bao_id', 'nguoi_bao__ho_ten').distinct().order_by('nguoi_bao__ho_ten')
    thong_ke = {
        'tong': BaoHong.objects.count(),
        'cho_xu_ly': BaoHong.objects.filter(trang_thai='cho_xu_ly').count(),
        'dang_sua': BaoHong.objects.filter(trang_thai='dang_sua').count(),
        'da_sua': BaoHong.objects.filter(trang_thai='da_sua').count(),
    }

    context = {
        'bao_hongs': bao_hongs,
        'tu_khoa': tu_khoa,
        'trang_thai_loc': trang_thai,
        'phong_loc': phong,
        'nguoi_bao_loc': nguoi_bao,
        'thoi_gian_loc': thoi_gian,
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'ds_phong': PhongHoc.objects.all(),
        'ds_nguoi_bao': ds_nguoi_bao,
        'trang_thai_choices': BaoHong.TrangThai.choices,
        'thong_ke': thong_ke,
    }
    return render(request, 'ThietBi/DanhSachBaoHong.html', context)


@kiem_tra_quyen_thiet_bi
def cap_nhat_trang_thai_bao_hong(request, pk):
    """Cập nhật trạng thái báo hỏng."""
    bh = get_object_or_404(BaoHong, pk=pk)
    if request.method == 'POST':
        trang_thai = request.POST.get('trang_thai')
        if trang_thai in BaoHong.TrangThai.values:
            bh.trang_thai = trang_thai
            bh.save()
            
            # Cập nhật trạng thái thiết bị tương ứng
            if trang_thai == 'da_sua':
                bh.thiet_bi.trang_thai = 'hoat_dong'
            elif trang_thai == 'dang_sua':
                bh.thiet_bi.trang_thai = 'bao_tri'
            elif trang_thai == 'cho_xu_ly':
                bh.thiet_bi.trang_thai = 'hong'
            bh.thiet_bi.save()
            
            messages.success(request, f'Đã cập nhật trạng thái cho báo hỏng thiết bị "{bh.thiet_bi.ten_thiet_bi}".')
        else:
            messages.error(request, 'Trạng thái không hợp lệ.')
    return redirect('danh_sach_bao_hong')
