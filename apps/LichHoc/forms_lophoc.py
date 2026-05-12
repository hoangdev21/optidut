from django import forms
from .models import LopHoc

class FormLopHoc(forms.ModelForm):
    class Meta:
        model = LopHoc
        fields = ['ten_lop', 'khoa', 'nien_khoa']
        widgets = {
            'ten_lop': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ví dụ: 21TCLC_DT1'}),
            'khoa': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ví dụ: Công nghệ thông tin'}),
            'nien_khoa': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ví dụ: 2021-2025'}),
        }
