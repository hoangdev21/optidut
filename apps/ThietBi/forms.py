from django import forms
from .models import ThietBi, BaoHong


class FormThietBi(forms.ModelForm):
    """Form thêm/sửa thiết bị."""

    class Meta:
        model = ThietBi
        fields = ['ten_thiet_bi', 'phong_hoc', 'so_luong', 'trang_thai', 'ghi_chu']
        widgets = {
            'ten_thiet_bi': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tên thiết bị'}),
            'phong_hoc': forms.Select(attrs={'class': 'form-select'}),
            'so_luong': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'trang_thai': forms.Select(attrs={'class': 'form-select'}),
            'ghi_chu': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }


class FormBaoHong(forms.ModelForm):
    """Form báo hỏng thiết bị."""

    class Meta:
        model = BaoHong
        fields = ['thiet_bi', 'mo_ta']
        widgets = {
            'thiet_bi': forms.Select(attrs={'class': 'form-select'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Mô tả lỗi thiết bị...'}),
        }
