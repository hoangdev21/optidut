from django import forms
from .models import LichHoc
from apps.NguoiDung.models import NguoiDung
from apps.PhongHoc.models import PhongHoc
from .models import LopHoc

class FormLopHoc(forms.ModelForm):
    """Form thêm/sửa lớp học."""
    class Meta:
        model = LopHoc
        fields = ['ten_lop', 'khoa', 'nien_khoa']
        widgets = {
            'ten_lop': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'VD: 21TCLC_DT1'}),
            'khoa': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'VD: CNTT'}),
            'nien_khoa': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'VD: 2021-2026'}),
        }
class FormLichHoc(forms.ModelForm):
    """Form thêm/sửa lịch học."""

    class Meta:
        model = LichHoc
        fields = [
            'mon_hoc', 'lop_hoc', 'giang_vien', 'phong_hoc', 
            'ngay_hoc', 'tiet_bat_dau', 'tiet_ket_thuc', 'si_so', 'ghi_chu'
        ]
        widgets = {
            'mon_hoc': forms.TextInput(attrs={'class': 'form-input', 'list': 'mon_hoc_list', 'placeholder': 'Chọn từ danh sách hoặc nhập mới...'}),
            'lop_hoc': forms.Select(attrs={'class': 'form-select'}),
            'giang_vien': forms.Select(attrs={'class': 'form-select'}),
            'phong_hoc': forms.Select(attrs={'class': 'form-select'}),
            'ngay_hoc': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'tiet_bat_dau': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 14}),
            'tiet_ket_thuc': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 14}),
            'si_so': forms.NumberInput(attrs={'class': 'form-input'}),
            'ghi_chu': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['giang_vien'].queryset = NguoiDung.objects.filter(vai_tro='giang_vien', is_active=True)
        self.fields['giang_vien'].empty_label = "Tìm và chọn giảng viên..."
        self.fields['phong_hoc'].queryset = PhongHoc.objects.exclude(trang_thai='bao_tri')
        self.fields['phong_hoc'].empty_label = "Tìm và chọn phòng học..."
        self.fields['lop_hoc'].empty_label = "Tìm và chọn lớp học..."

    def clean(self):
        cleaned = super().clean()
        tiet_bd = cleaned.get('tiet_bat_dau')
        tiet_kt = cleaned.get('tiet_ket_thuc')
        phong = cleaned.get('phong_hoc')
        gv = cleaned.get('giang_vien')
        ngay = cleaned.get('ngay_hoc')

        if tiet_bd and tiet_kt and tiet_bd >= tiet_kt:
            raise forms.ValidationError('Tiết bắt đầu phải nhỏ hơn tiết kết thúc.')

        exclude_id = self.instance.pk if self.instance.pk else None

        if phong and ngay and tiet_bd and tiet_kt:
            if LichHoc.kiem_tra_trung_phong(phong.id, ngay, tiet_bd, tiet_kt, exclude_id):
                raise forms.ValidationError(f'Phòng {phong.ma_phong} đã có lịch trong khoảng thời gian này.')

        if gv and ngay and tiet_bd and tiet_kt:
            if LichHoc.kiem_tra_trung_giang_vien(gv.id, ngay, tiet_bd, tiet_kt, exclude_id):
                raise forms.ValidationError(f'Giảng viên {gv.ho_ten} đã có lịch dạy trong khoảng thời gian này.')

        return cleaned
