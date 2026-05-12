from .models import ThongBao


def thong_bao_chua_doc(request):
    """Context processor: đếm thông báo chưa đọc cho header."""
    if request.user.is_authenticated:
        from django.db.models import Q
        user = request.user
        qs = ThongBao.objects.filter(Q(nguoi_nhan=user) | Q(nguoi_nhan__isnull=True), da_doc=False)
        so_chua_doc = qs.count()
        thong_bao_moi = qs.order_by('-ngay_tao')[:5]
        return {
            'so_thong_bao_chua_doc': so_chua_doc,
            'thong_bao_moi_nhat': thong_bao_moi,
        }
    return {}
