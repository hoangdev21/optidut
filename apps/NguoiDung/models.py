from django.contrib.auth.models import AbstractUser
from django.db import models


class LopSinhHoat(models.Model):
    """Model Lớp sinh hoạt (ví dụ: 21TCLC_DT1)."""
    ten_lop = models.CharField('Tên lớp sinh hoạt', max_length=50, unique=True)
    khoa_hoc = models.IntegerField('Khóa học', default=2021)
    khoa_quan_ly = models.CharField('Khoa quản lý', max_length=100, blank=True)

    class Meta:
        db_table = 'lop_sinh_hoat'
        verbose_name = 'Lớp sinh hoạt'
        verbose_name_plural = 'Lớp sinh hoạt'

    def __str__(self):
        return self.ten_lop


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
    lop_sinh_hoat = models.ForeignKey(
        LopSinhHoat, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sinh_viens',
        verbose_name='Lớp sinh hoạt'
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
