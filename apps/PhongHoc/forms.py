from django import forms
from .models import PhongHoc


class FormPhongHoc(forms.ModelForm):
    """Form thêm/sửa phòng học."""

    class Meta:
        model = PhongHoc
        fields = ['ma_phong', 'ten_phong', 'toa_nha', 'suc_chua', 'loai_phong', 'trang_thai', 'ghi_chu']
        widgets = {
            'ma_phong': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'VD: A101'}),
            'ten_phong': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tên phòng'}),
            'toa_nha': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tòa nhà'}),
            'suc_chua': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Sức chứa', 'min': 1}),
            'loai_phong': forms.Select(attrs={'class': 'form-select'}),
            'trang_thai': forms.Select(attrs={'class': 'form-select'}),
            'ghi_chu': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Ghi chú...'}),
        }
