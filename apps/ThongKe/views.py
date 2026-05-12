from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.PhongHoc.models import PhongHoc
from apps.LichHoc.models import LichHoc
from apps.ThietBi.models import ThietBi, BaoHong


def kiem_tra_quyen_thong_ke(view_func):
    """Decorator: chỉ quản trị viên và giáo vụ."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dang_nhap')
        if not (request.user.la_quan_tri or request.user.la_giao_vu):
            messages.error(request, 'Bạn không có quyền xem thống kê.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@kiem_tra_quyen_thong_ke
def tong_quan(request):
    """Trang thống kê tổng quan."""
    hom_nay = timezone.now().date()
    tuan_truoc = hom_nay - timedelta(days=7)

    # Thống kê phòng
    tong_phong = PhongHoc.objects.count()
    phong_trong = PhongHoc.objects.filter(trang_thai='trong').count()
    phong_dang_dung = PhongHoc.objects.filter(trang_thai='dang_su_dung').count()
    phong_bao_tri = PhongHoc.objects.filter(trang_thai='bao_tri').count()

    # Thống kê lịch học tuần này
    lich_tuan_nay = LichHoc.objects.filter(
        ngay_hoc__gte=tuan_truoc,
        ngay_hoc__lte=hom_nay,
        trang_thai='hoat_dong',
    ).count()

    # Phòng sử dụng nhiều nhất
    phong_nhieu_nhat = PhongHoc.objects.annotate(
        so_lan_dung=Count('lich_hocs', filter=Q(lich_hocs__trang_thai='hoat_dong'))
    ).order_by('-so_lan_dung')[:10]

    # Phòng ít sử dụng
    phong_it_dung = PhongHoc.objects.annotate(
        so_lan_dung=Count('lich_hocs', filter=Q(lich_hocs__trang_thai='hoat_dong'))
    ).order_by('so_lan_dung')[:10]

    # Thiết bị hỏng
    thiet_bi_hong = ThietBi.objects.filter(trang_thai='hong').select_related('phong_hoc')

    context = {
        'tong_phong': tong_phong,
        'phong_trong': phong_trong,
        'phong_dang_dung': phong_dang_dung,
        'phong_bao_tri': phong_bao_tri,
        'lich_tuan_nay': lich_tuan_nay,
        'phong_nhieu_nhat': phong_nhieu_nhat,
        'phong_it_dung': phong_it_dung,
        'thiet_bi_hong': thiet_bi_hong,
    }
    return render(request, 'ThongKe/TongQuan.html', context)


@kiem_tra_quyen_thong_ke
def xuat_bao_cao(request):
    """Xuất báo cáo CSV."""
    import csv
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="bao_cao_phong_hoc.csv"'
    response.write('\ufeff')  # BOM for Excel UTF-8

    writer = csv.writer(response)
    writer.writerow(['Mã phòng', 'Tên phòng', 'Tòa nhà', 'Sức chứa', 'Loại phòng', 'Trạng thái', 'Số lần sử dụng'])

    phongs = PhongHoc.objects.annotate(
        so_lan_dung=Count('lich_hocs', filter=Q(lich_hocs__trang_thai='hoat_dong'))
    ).order_by('toa_nha', 'ma_phong')

    for p in phongs:
        writer.writerow([
            p.ma_phong, p.ten_phong, p.toa_nha, p.suc_chua,
            p.get_loai_phong_display(), p.get_trang_thai_display(), p.so_lan_dung
        ])

    return response
