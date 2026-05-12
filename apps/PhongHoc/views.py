from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import PhongHoc
from apps.LichHoc.models import LichHoc
from .forms import FormPhongHoc


def kiem_tra_quyen_phong(view_func):
    """Decorator: chỉ quản trị viên và giáo vụ mới được quản lý phòng."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dang_nhap')
        if not (request.user.la_quan_tri or request.user.la_giao_vu):
            messages.error(request, 'Bạn không có quyền truy cập.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def danh_sach_phong(request):
    """Danh sách phòng học - không cho sinh viên xem."""
    if request.user.la_sinh_vien:
        messages.error(request, 'Bạn không có quyền truy cập.')
        return redirect('dashboard')

    hom_nay = timezone.localdate()
    ngay_str = request.GET.get('ngay', '')
    if ngay_str:
        try:
            ngay_hien_tai = datetime.strptime(ngay_str, '%Y-%m-%d').date()
        except ValueError:
            ngay_hien_tai = hom_nay
    else:
        ngay_hien_tai = hom_nay

    dau_tuan = ngay_hien_tai - timedelta(days=ngay_hien_tai.weekday())
    cuoi_tuan = dau_tuan + timedelta(days=6)
    tuan_truoc = dau_tuan - timedelta(days=7)
    tuan_sau = dau_tuan + timedelta(days=7)

    # Cập nhật trạng thái phòng theo ngày đang xem
    phong_dang_dung_ids = LichHoc.objects.filter(
        ngay_hoc=ngay_hien_tai, trang_thai='hoat_dong'
    ).values_list('phong_hoc_id', flat=True).distinct()
    PhongHoc.objects.filter(id__in=phong_dang_dung_ids).exclude(
        trang_thai='bao_tri'
    ).update(trang_thai='dang_su_dung')
    PhongHoc.objects.exclude(id__in=phong_dang_dung_ids).exclude(
        trang_thai='bao_tri'
    ).update(trang_thai='trong')

    queryset = PhongHoc.objects.all()

    # Tìm kiếm
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(ma_phong__icontains=tu_khoa) | queryset.filter(ten_phong__icontains=tu_khoa)

    # Lọc
    toa_nha = request.GET.get('toa_nha', '')
    if toa_nha:
        queryset = queryset.filter(toa_nha=toa_nha)

    loai_phong = request.GET.get('loai_phong', '')
    if loai_phong:
        queryset = queryset.filter(loai_phong=loai_phong)

    trang_thai = request.GET.get('trang_thai', '')
    if trang_thai:
        queryset = queryset.filter(trang_thai=trang_thai)

    page_size = request.GET.get('page_size', '20')
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(queryset, page_size)
    trang = request.GET.get('page')
    phong_hocs = paginator.get_page(trang)

    # Lấy danh sách tòa nhà cho filter (clear default ordering to avoid duplicates)
    ds_toa_nha = PhongHoc.objects.order_by('toa_nha').values_list('toa_nha', flat=True).distinct()

    context = {
        'phong_hocs': phong_hocs,
        'tu_khoa': tu_khoa,
        'toa_nha_loc': toa_nha,
        'loai_phong_loc': loai_phong,
        'trang_thai_loc': trang_thai,
        'ngay_loc': ngay_hien_tai,
        'hom_nay': hom_nay,
        'hom_qua': hom_nay - timedelta(days=1),
        'hom_sau': hom_nay + timedelta(days=1),
        'ngay_truoc': ngay_hien_tai - timedelta(days=1),
        'ngay_sau': ngay_hien_tai + timedelta(days=1),
        'dau_tuan': dau_tuan,
        'cuoi_tuan': cuoi_tuan,
        'tuan_truoc': tuan_truoc,
        'tuan_sau': tuan_sau,
        'ds_toa_nha': ds_toa_nha,
        'loai_phong_choices': PhongHoc.LoaiPhong.choices,
        'trang_thai_choices': PhongHoc.TrangThai.choices,
    }
    return render(request, 'PhongHoc/DanhSach.html', context)


@login_required
def so_do_phong(request):
    """Trang xem sơ đồ phòng học của các tòa nhà."""
    return render(request, 'PhongHoc/SoDo.html')


@login_required
def chi_tiet_phong(request, pk):
    """Xem chi tiết phòng học + danh sách thiết bị."""
    phong = get_object_or_404(PhongHoc, pk=pk)
    thiet_bis = phong.thietbi_set.all()
    return render(request, 'PhongHoc/ChiTiet.html', {'phong': phong, 'thiet_bis': thiet_bis})


@kiem_tra_quyen_phong
def them_phong(request):
    """Thêm phòng học mới."""
    if request.method == 'POST':
        form = FormPhongHoc(request.POST)
        if form.is_valid():
            phong = form.save()
            messages.success(request, f'Đã thêm phòng "{phong.ma_phong}" thành công.')
            return redirect('danh_sach_phong')
    else:
        form = FormPhongHoc()
    return render(request, 'PhongHoc/ThemMoi.html', {'form': form})


@kiem_tra_quyen_phong
def chinh_sua_phong(request, pk):
    """Chỉnh sửa thông tin phòng học."""
    phong = get_object_or_404(PhongHoc, pk=pk)
    thiet_bis = phong.thietbi_set.all()
    if request.method == 'POST':
        form = FormPhongHoc(request.POST, instance=phong)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật phòng "{phong.ma_phong}".')
            return redirect('danh_sach_phong')
    else:
        form = FormPhongHoc(instance=phong)
    return render(request, 'PhongHoc/ChinhSua.html', {'form': form, 'phong': phong, 'thiet_bis': thiet_bis})


@kiem_tra_quyen_phong
def xoa_phong(request, pk):
    """Xóa phòng học."""
    phong = get_object_or_404(PhongHoc, pk=pk)
    if request.method == 'POST':
        ma = phong.ma_phong
        phong.delete()
        messages.success(request, f'Đã xóa phòng "{ma}".')
        return redirect('danh_sach_phong')
    return render(request, 'PhongHoc/XacNhanXoa.html', {'phong': phong})
