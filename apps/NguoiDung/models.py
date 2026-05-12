from django.contrib.auth.models import AbstractUser
from django.db import models


class NguoiDung(AbstractUser):
    """Model người dùng mở rộng từ AbstractUser."""

    class VaiTro(models.TextChoices):
        QUAN_TRI = 'quan_tri', 'Quản trị viên'
        GIAO_VU = 'giao_vu', 'Giáo vụ'
        GIANG_VIEN = 'giang_vien', 'Giảng viên'
        SINH_VIEN = 'sinh_vien', 'Sinh viên'

    ho_ten = models.CharField('Họ và tên', max_length=100, blank=True)
    ma_so = models.CharField('Mã số (MSSV/MGV)', max_length=20, blank=True)
    vai_tro = models.CharField(
        'Vai trò',
        max_length=20,
        choices=VaiTro.choices,
        default=VaiTro.SINH_VIEN,
    )

    class Meta:
        db_table = 'nguoi_dung'
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
        ordering = ['ho_ten']

    def __str__(self):
        return f'{self.ho_ten} ({self.get_vai_tro_display()})'

    @property
    def la_quan_tri(self):
        return self.vai_tro == self.VaiTro.QUAN_TRI

    @property
    def la_giao_vu(self):
        return self.vai_tro == self.VaiTro.GIAO_VU

    @property
    def la_giang_vien(self):
        return self.vai_tro == self.VaiTro.GIANG_VIEN

    @property
    def la_sinh_vien(self):
        return self.vai_tro == self.VaiTro.SINH_VIEN
