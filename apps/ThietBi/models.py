from django.db import models
from django.conf import settings


class ThietBi(models.Model):
    """Model thiết bị phòng học."""

    class TrangThai(models.TextChoices):
        HOAT_DONG = 'hoat_dong', 'Hoạt động'
        HONG = 'hong', 'Hỏng'
        BAO_TRI = 'bao_tri', 'Bảo trì'

    ten_thiet_bi = models.CharField('Tên thiết bị', max_length=100)
    phong_hoc = models.ForeignKey(
        'PhongHoc.PhongHoc',
        on_delete=models.CASCADE,
        verbose_name='Phòng học',
    )
    trang_thai = models.CharField(
        'Trạng thái',
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.HOAT_DONG,
    )
    so_luong = models.PositiveIntegerField('Số lượng', default=1)
    ghi_chu = models.TextField('Ghi chú', blank=True)
    ngay_tao = models.DateTimeField('Ngày tạo', auto_now_add=True)

    class Meta:
        db_table = 'thiet_bi'
        verbose_name = 'Thiết bị'
        verbose_name_plural = 'Thiết bị'
        ordering = ['phong_hoc', 'ten_thiet_bi']

    def __str__(self):
        return f'{self.ten_thiet_bi} - {self.phong_hoc.ma_phong}'


class BaoHong(models.Model):
    """Model báo hỏng thiết bị."""

    class TrangThai(models.TextChoices):
        CHO_XU_LY = 'cho_xu_ly', 'Chờ xử lý'
        DANG_SUA = 'dang_sua', 'Đang sửa'
        DA_SUA = 'da_sua', 'Đã sửa'

    thiet_bi = models.ForeignKey(ThietBi, on_delete=models.CASCADE, verbose_name='Thiết bị')
    nguoi_bao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Người báo',
    )
    mo_ta = models.TextField('Mô tả lỗi')
    trang_thai = models.CharField(
        'Trạng thái',
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.CHO_XU_LY,
    )
    ngay_bao = models.DateTimeField('Ngày báo', auto_now_add=True)

    class Meta:
        db_table = 'bao_hong'
        verbose_name = 'Báo hỏng'
        verbose_name_plural = 'Báo hỏng'
        ordering = ['-ngay_bao']

    def __str__(self):
        return f'Báo hỏng: {self.thiet_bi.ten_thiet_bi}'
