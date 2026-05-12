from django.db import models
from django.conf import settings


# Khung giờ tiết học theo quy định ĐH Bách Khoa Đà Nẵng
KHUNG_GIO_TIET = {
    1:  {'bat_dau': '07:00', 'ket_thuc': '07:50', 'buoi': 'Buổi Sáng'},
    2:  {'bat_dau': '08:00', 'ket_thuc': '08:50', 'buoi': 'Buổi Sáng'},
    3:  {'bat_dau': '09:00', 'ket_thuc': '09:50', 'buoi': 'Buổi Sáng'},
    4:  {'bat_dau': '10:00', 'ket_thuc': '10:50', 'buoi': 'Buổi Sáng'},
    5:  {'bat_dau': '11:00', 'ket_thuc': '11:50', 'buoi': 'Buổi Sáng'},
    6:  {'bat_dau': '12:30', 'ket_thuc': '13:20', 'buoi': 'Buổi Chiều'},
    7:  {'bat_dau': '13:30', 'ket_thuc': '14:20', 'buoi': 'Buổi Chiều'},
    8:  {'bat_dau': '14:30', 'ket_thuc': '15:20', 'buoi': 'Buổi Chiều'},
    9:  {'bat_dau': '15:30', 'ket_thuc': '16:20', 'buoi': 'Buổi Chiều'},
    10: {'bat_dau': '16:30', 'ket_thuc': '17:20', 'buoi': 'Buổi Chiều'},
    11: {'bat_dau': '17:30', 'ket_thuc': '18:15', 'buoi': 'Buổi Tối'},
    12: {'bat_dau': '18:15', 'ket_thuc': '19:00', 'buoi': 'Buổi Tối'},
    13: {'bat_dau': '19:10', 'ket_thuc': '19:55', 'buoi': 'Buổi Tối'},
    14: {'bat_dau': '19:55', 'ket_thuc': '20:40', 'buoi': 'Buổi Tối'},
}


class LopHoc(models.Model):
    """Model quản lý lớp sinh viên (ví dụ: 21TCLC_DT1)."""
    ten_lop = models.CharField('Tên lớp', max_length=50, unique=True)
    khoa = models.CharField('Khoa', max_length=100, blank=True)
    nien_khoa = models.CharField('Niên khóa', max_length=20, blank=True)

    class Meta:
        db_table = 'lop_hoc'
        verbose_name = 'Lớp học'
        verbose_name_plural = 'Lớp học'

    def __str__(self):
        return self.ten_lop


class LichHoc(models.Model):
    """Model lịch học."""

    class TrangThai(models.TextChoices):
        HOAT_DONG = 'hoat_dong', 'Hoạt động'
        DA_HUY = 'da_huy', 'Đã hủy'

    mon_hoc = models.CharField('Môn học', max_length=100)
    lop_hoc = models.ForeignKey(
        'LopHoc',
        on_delete=models.CASCADE,
        related_name='lich_hocs',
        verbose_name='Lớp học',
        null=True
    )
    ma_lop = models.CharField('Mã lớp (Hiển thị)', max_length=20, blank=True)
    giang_vien = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lich_day',
        verbose_name='Giảng viên',
        limit_choices_to={'vai_tro': 'giang_vien'},
    )
    phong_hoc = models.ForeignKey(
        'PhongHoc.PhongHoc',
        on_delete=models.CASCADE,
        related_name='lich_hocs',
        verbose_name='Phòng học',
    )
    ngay_hoc = models.DateField('Ngày học')
    tiet_bat_dau = models.PositiveIntegerField('Tiết bắt đầu')
    tiet_ket_thuc = models.PositiveIntegerField('Tiết kết thúc')
    si_so = models.PositiveIntegerField('Sĩ số', default=30)
    trang_thai = models.CharField(
        'Trạng thái',
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.HOAT_DONG,
    )
    ghi_chu = models.TextField('Ghi chú', blank=True)
    ngay_tao = models.DateTimeField('Ngày tạo', auto_now_add=True)

    class Meta:
        db_table = 'lich_hoc'
        verbose_name = 'Lịch học'
        verbose_name_plural = 'Lịch học'
        ordering = ['ngay_hoc', 'tiet_bat_dau']

    def __str__(self):
        return f'{self.mon_hoc} - {self.ma_lop} ({self.ngay_hoc})'

    @staticmethod
    def kiem_tra_trung_phong(phong_hoc_id, ngay_hoc, tiet_bat_dau, tiet_ket_thuc, exclude_id=None):
        """Kiểm tra xem phòng có bị trùng lịch không."""
        qs = LichHoc.objects.filter(
            phong_hoc_id=phong_hoc_id,
            ngay_hoc=ngay_hoc,
            trang_thai='hoat_dong',
            tiet_bat_dau__lt=tiet_ket_thuc,
            tiet_ket_thuc__gt=tiet_bat_dau,
        )
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    @staticmethod
    def kiem_tra_trung_giang_vien(giang_vien_id, ngay_hoc, tiet_bat_dau, tiet_ket_thuc, exclude_id=None):
        """Kiểm tra xem giảng viên có bị trùng lịch không."""
        qs = LichHoc.objects.filter(
            giang_vien_id=giang_vien_id,
            ngay_hoc=ngay_hoc,
            trang_thai='hoat_dong',
            tiet_bat_dau__lt=tiet_ket_thuc,
            tiet_ket_thuc__gt=tiet_bat_dau,
        )
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()


class DangKyHocPhan(models.Model):
    """Model đăng ký học phần — liên kết SV với lớp học phần."""
    sinh_vien = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dang_ky_hoc_phans',
        verbose_name='Sinh viên',
        limit_choices_to={'vai_tro': 'sinh_vien'},
    )
    lop_hoc = models.ForeignKey(
        'LopHoc',
        on_delete=models.CASCADE,
        related_name='dang_ky_hoc_phans',
        verbose_name='Lớp học phần',
    )
    ngay_dang_ky = models.DateTimeField('Ngày đăng ký', auto_now_add=True)

    class Meta:
        db_table = 'dang_ky_hoc_phan'
        verbose_name = 'Đăng ký học phần'
        verbose_name_plural = 'Đăng ký học phần'
        unique_together = ['sinh_vien', 'lop_hoc']
        ordering = ['-ngay_dang_ky']

    def __str__(self):
        return f'{self.sinh_vien.ho_ten} - {self.lop_hoc.ten_lop}'


class YeuCauDoiLich(models.Model):
    """Yêu cầu đổi lịch — GV gửi, Admin/GV duyệt."""
    LOAI_CHOICES = [
        ('doi_phong', 'Đổi phòng học'),
        ('doi_gio', 'Đổi giờ/tiết học'),
        ('huy_buoi', 'Hủy buổi học'),
        ('khac', 'Khác'),
    ]
    TRANG_THAI_CHOICES = [
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('tu_choi', 'Từ chối'),
    ]

    lich_hoc = models.ForeignKey(
        'LichHoc', on_delete=models.CASCADE,
        related_name='yeu_cau_doi_lichs', verbose_name='Lịch học gốc',
    )
    nguoi_yeu_cau = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='yeu_cau_gui', verbose_name='Người yêu cầu',
    )
    loai_yeu_cau = models.CharField('Loại yêu cầu', max_length=20, choices=LOAI_CHOICES)
    ly_do = models.TextField('Lý do yêu cầu')

    # Thông tin mới (nếu đổi phòng/giờ)
    phong_moi = models.ForeignKey(
        'PhongHoc.PhongHoc', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='yeu_cau_doi_phongs',
        verbose_name='Phòng mới (nếu đổi phòng)',
    )
    ngay_moi = models.DateField('Ngày mới', null=True, blank=True)
    tiet_moi_bat_dau = models.IntegerField('Tiết bắt đầu mới', null=True, blank=True)
    tiet_moi_ket_thuc = models.IntegerField('Tiết kết thúc mới', null=True, blank=True)

    # Duyệt
    trang_thai = models.CharField('Trạng thái', max_length=20, choices=TRANG_THAI_CHOICES, default='cho_duyet')
    nguoi_duyet = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='yeu_cau_duyet',
        verbose_name='Người duyệt',
    )
    ghi_chu_duyet = models.TextField('Ghi chú duyệt', blank=True)
    ngay_duyet = models.DateTimeField('Ngày duyệt', null=True, blank=True)
    ngay_tao = models.DateTimeField('Ngày tạo', auto_now_add=True)

    class Meta:
        db_table = 'yeu_cau_doi_lich'
        verbose_name = 'Yêu cầu đổi lịch'
        verbose_name_plural = 'Yêu cầu đổi lịch'
        ordering = ['-ngay_tao']

    def __str__(self):
        return f'[{self.get_trang_thai_display()}] {self.get_loai_yeu_cau_display()} - {self.lich_hoc.mon_hoc}'
