from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import NguoiDung
from .forms import FormDangNhap, FormNguoiDung


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
    for i in range(7):
        ngay = hom_nay + timedelta(days=i)
        count = LichHoc.objects.filter(ngay_hoc=ngay, trang_thai='hoat_dong').count()
        chart_data.append(count)

    context = {
        'tong_tai_khoan': NguoiDung.objects.count(),
        'tong_phong': PhongHoc.objects.count(),
        'phong_bao_tri': PhongHoc.objects.filter(trang_thai='bao_tri').count(),
        'thiet_bi_hong': ThietBi.objects.filter(trang_thai='hong').count(),
        'recent_users': NguoiDung.objects.order_by('-date_joined')[:5],
        'recent_notifications': ThongBao.objects.order_by('-ngay_tao')[:5],
        'chart_data': chart_data,
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
    for i in range(7):
        ngay = hom_nay + timedelta(days=i)
        count = LichHoc.objects.filter(ngay_hoc=ngay, trang_thai='hoat_dong').count()
        chart_data.append(count)

    context = {
        'lich_hom_nay': LichHoc.objects.filter(ngay_hoc=hom_nay, trang_thai='hoat_dong').count(),
        'phong_trong': PhongHoc.objects.filter(trang_thai='trong').count(),
        'phong_dang_dung': PhongHoc.objects.filter(trang_thai='dang_su_dung').count(),
        'tong_phong': PhongHoc.objects.count(),
        'yeu_cau_cho': YeuCauDoiLich.objects.filter(trang_thai='cho_duyet').count(),
        'recent_requests': YeuCauDoiLich.objects.order_by('-ngay_tao')[:5],
        'chart_data': chart_data,
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
    """Danh sách tài khoản người dùng."""
    queryset = NguoiDung.objects.all()

    # Tìm kiếm
    tu_khoa = request.GET.get('q', '')
    if tu_khoa:
        queryset = queryset.filter(ho_ten__icontains=tu_khoa)

    # Lọc theo vai trò
    vai_tro_loc = request.GET.get('vai_tro', '')
    if vai_tro_loc:
        queryset = queryset.filter(vai_tro=vai_tro_loc)

    paginator = Paginator(queryset, 15)
    trang = request.GET.get('page')
    nguoi_dungs = paginator.get_page(trang)

    context = {
        'nguoi_dungs': nguoi_dungs,
        'tu_khoa': tu_khoa,
        'vai_tro_loc': vai_tro_loc,
        'vai_tro_choices': NguoiDung.VaiTro.choices,
    }
    return render(request, 'NguoiDung/DanhSach.html', context)


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
