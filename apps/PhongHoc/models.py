from django.db import models


class PhongHoc(models.Model):
    """Model phòng học."""

    class LoaiPhong(models.TextChoices):
        LY_THUYET = 'ly_thuyet', 'Lý thuyết'
        THUC_HANH = 'thuc_hanh', 'Thực hành'
        HOI_TRUONG = 'hoi_truong', 'Hội trường'

    class TrangThai(models.TextChoices):
        TRONG = 'trong', 'Trống'
        DANG_SU_DUNG = 'dang_su_dung', 'Đang sử dụng'
        BAO_TRI = 'bao_tri', 'Bảo trì'

    ma_phong = models.CharField('Mã phòng', max_length=20, unique=True)
    ten_phong = models.CharField('Tên phòng', max_length=100)
    toa_nha = models.CharField('Tòa nhà', max_length=50)
    suc_chua = models.PositiveIntegerField('Sức chứa', default=30)
    loai_phong = models.CharField(
        'Loại phòng',
        max_length=20,
        choices=LoaiPhong.choices,
        default=LoaiPhong.LY_THUYET,
    )
    trang_thai = models.CharField(
        'Trạng thái',
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.TRONG,
    )
    ghi_chu = models.TextField('Ghi chú', blank=True)
    ngay_tao = models.DateTimeField('Ngày tạo', auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField('Ngày cập nhật', auto_now=True)

    class Meta:
        db_table = 'phong_hoc'
        verbose_name = 'Phòng học'
        verbose_name_plural = 'Phòng học'
        ordering = ['toa_nha', 'ma_phong']

    def __str__(self):
        return f'{self.ma_phong} - {self.ten_phong}'
