from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from .models import ThongBao


@login_required
def danh_sach_thong_bao(request):
    """Danh sách thông báo của người dùng hiện tại."""
    hom_nay = timezone.localdate()
    ngay_loc = request.GET.get('ngay', '')
    
    # Chế độ "Gần đây" (hiển thị tất cả) hoặc lọc theo ngày cụ thể
    view_all = request.GET.get('all', '0') == '1'
    
    if ngay_loc:
        try:
            ngay_hien_tai = datetime.strptime(ngay_loc, '%Y-%m-%d').date()
        except ValueError:
            ngay_hien_tai = hom_nay
    else:
        ngay_hien_tai = hom_nay

    # Chỉ lấy thông báo gửi cho mình hoặc thông báo chung (null recipient)
    queryset = ThongBao.objects.filter(
        Q(nguoi_nhan=request.user) | Q(nguoi_nhan__isnull=True)
    ).select_related('nguoi_tao').order_by('-ngay_tao')

    # Nếu không phải chế độ "Xem tất cả", thì lọc theo ngày
    if not view_all:
        # Sử dụng range để lọc chính xác ngày (tránh lỗi múi giờ database)
        start_dt = timezone.make_aware(datetime.combine(ngay_hien_tai, datetime.min.time()))
        end_dt = timezone.make_aware(datetime.combine(ngay_hien_tai, datetime.max.time()))
        queryset = queryset.filter(ngay_tao__range=(start_dt, end_dt))

    # Lọc theo loại
    loai_loc = request.GET.get('loai', '')
    if loai_loc:
        queryset = queryset.filter(loai=loai_loc)

    # Dữ liệu cho week selector (Dựa trên ngày hiện tại hoặc ngày đang chọn)
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
            'is_selected': not view_all and ngay == ngay_hien_tai,
        })

    paginator = Paginator(queryset, 10)
    trang = request.GET.get('page')
    thong_baos = paginator.get_page(trang)

    return render(request, 'ThongBao/DanhSach.html', {
        'thong_baos': thong_baos,
        'ngay_hien_tai': ngay_hien_tai,
        'ds_ngay': ds_ngay,
        'dau_tuan': dau_tuan,
        'cuoi_tuan': cuoi_tuan,
        'tuan_truoc': tuan_truoc,
        'tuan_sau': tuan_sau,
        'hom_nay': hom_nay,
        'loai_loc': loai_loc,
        'view_all': view_all,
        'loai_choices': ThongBao.Loai.choices,
    })


@login_required
def danh_dau_da_doc(request, pk):
    """Đánh dấu thông báo của mình đã đọc."""
    tb = get_object_or_404(ThongBao, pk=pk, nguoi_nhan=request.user)
    tb.da_doc = True
    tb.save()
    return redirect('danh_sach_thong_bao')


@login_required
def doc_tat_ca(request):
    """Đánh dấu tất cả thông báo của mình đã đọc."""
    ThongBao.objects.filter(nguoi_nhan=request.user, da_doc=False).update(da_doc=True)
    return redirect('danh_sach_thong_bao')
