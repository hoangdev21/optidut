from django.db import models
from django.conf import settings


class ThongBao(models.Model):
    """Model thông báo hệ thống."""

    class Loai(models.TextChoices):
        DOI_PHONG = 'doi_phong', 'Đổi phòng'
        DOI_LICH = 'doi_lich', 'Đổi lịch'
        HUY_LICH = 'huy_lich', 'Hủy lịch'
        BAO_TRI = 'bao_tri', 'Bảo trì'

    tieu_de = models.CharField('Tiêu đề', max_length=200)
    noi_dung = models.TextField('Nội dung')
    loai = models.CharField(
        'Loại',
        max_length=20,
        choices=Loai.choices,
        default=Loai.DOI_LICH,
    )
    nguoi_tao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Người tạo',
        related_name='thong_bao_da_tao',
    )
    nguoi_nhan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Người nhận',
        related_name='thong_bao_cua_toi',
    )
    da_doc = models.BooleanField('Đã đọc', default=False)
    ngay_tao = models.DateTimeField('Ngày tạo', auto_now_add=True)

    class Meta:
        db_table = 'thong_bao'
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'
        ordering = ['-ngay_tao']

    def __str__(self):
        return self.tieu_de
