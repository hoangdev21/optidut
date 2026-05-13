from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import NguoiDung, LopSinhHoat


class FormLopSinhHoat(forms.ModelForm):
    """Form quản lý lớp sinh hoạt."""
    class Meta:
        model = LopSinhHoat
        fields = ['ten_lop', 'khoa_hoc', 'khoa_quan_ly']
        widgets = {
            'ten_lop': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ví dụ: 21TCLC_DT1'}),
            'khoa_hoc': forms.NumberInput(attrs={'class': 'form-input'}),
            'khoa_quan_ly': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ví dụ: Công nghệ thông tin'}),
        }


class FormDangNhap(AuthenticationForm):
    """Form đăng nhập hệ thống."""
    username = forms.CharField(
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nhập tên đăng nhập',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nhập mật khẩu',
        }),
    )


class FormNguoiDung(forms.ModelForm):
    """Form thêm/sửa người dùng."""
    password_raw = forms.CharField(
        label='Mật khẩu',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nhập mật khẩu (để trống nếu không đổi)',
        }),
    )

    class Meta:
        model = NguoiDung
        fields = ['username', 'ho_ten', 'ma_so', 'email', 'vai_tro', 'lop_sinh_hoat', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'ho_ten': forms.TextInput(attrs={'class': 'form-input'}),
            'ma_so': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'vai_tro': forms.Select(attrs={'class': 'form-select'}),
            'lop_sinh_hoat': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password_raw')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
