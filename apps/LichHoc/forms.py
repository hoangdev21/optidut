from django import forms

from apps.NguoiDung.models import NguoiDung
from apps.PhongHoc.models import PhongHoc

from .models import LichHoc, LopHoc, MonHoc


class MonHocChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.ma_mon} - {obj.ten_mon}"


class FormLopHoc(forms.ModelForm):
    ma_mon = forms.CharField(
        label="Mã học phần",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "VD: IT001"}),
    )
    ten_mon = forms.CharField(
        label="Tên môn học",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "VD: Nhập môn Lập trình"}),
    )

    class Meta:
        model = LopHoc
        fields = ["ten_lop", "khoa", "nien_khoa", "giang_vien"]
        widgets = {
            "ten_lop": forms.TextInput(attrs={"class": "form-input", "placeholder": "VD: 21TCLC_DT1"}),
            "khoa": forms.TextInput(attrs={"class": "form-input", "placeholder": "VD: CNTT"}),
            "nien_khoa": forms.TextInput(attrs={"class": "form-input", "placeholder": "VD: 2024-2025"}),
            "giang_vien": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["giang_vien"].queryset = NguoiDung.objects.filter(vai_tro="giang_vien", is_active=True)
        self.fields["giang_vien"].empty_label = "--- Chọn giảng viên (tùy chọn) ---"
        if self.instance.pk and self.instance.mon_hoc_id:
            self.fields["ma_mon"].initial = self.instance.mon_hoc.ma_mon
            self.fields["ten_mon"].initial = self.instance.mon_hoc.ten_mon

    def clean_ma_mon(self):
        return self.cleaned_data["ma_mon"].strip().upper()

    def clean_ten_mon(self):
        return self.cleaned_data["ten_mon"].strip()

    def save(self, commit=True):
        ma_mon = self.cleaned_data["ma_mon"]
        ten_mon = self.cleaned_data["ten_mon"]
        mon_hoc, created = MonHoc.objects.get_or_create(
            ma_mon=ma_mon,
            defaults={"ten_mon": ten_mon},
        )
        if not created and mon_hoc.ten_mon != ten_mon:
            mon_hoc.ten_mon = ten_mon
            mon_hoc.save(update_fields=["ten_mon"])

        instance = super().save(commit=False)
        instance.mon_hoc = mon_hoc
        if commit:
            instance.save()
        return instance


class FormLichHoc(forms.ModelForm):
    mon_hoc = MonHocChoiceField(
        queryset=MonHoc.objects.all(),
        empty_label="Tìm và chọn môn học",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = LichHoc
        fields = [
            "mon_hoc",
            "lop_hoc",
            "giang_vien",
            "phong_hoc",
            "ngay_hoc",
            "tiet_bat_dau",
            "tiet_ket_thuc",
            "si_so",
            "ghi_chu",
        ]
        widgets = {
            "lop_hoc": forms.Select(attrs={"class": "form-select"}),
            "giang_vien": forms.Select(attrs={"class": "form-select"}),
            "phong_hoc": forms.Select(attrs={"class": "form-select"}),
            "ngay_hoc": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "tiet_bat_dau": forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 14}),
            "tiet_ket_thuc": forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 14}),
            "si_so": forms.NumberInput(attrs={"class": "form-input"}),
            "ghi_chu": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["mon_hoc"].queryset = MonHoc.objects.order_by("ma_mon", "ten_mon")
        self.fields["lop_hoc"].queryset = LopHoc.objects.select_related("mon_hoc").order_by("ten_lop")
        self.fields["lop_hoc"].empty_label = "Tìm và chọn lớp học phần"
        self.fields["giang_vien"].queryset = NguoiDung.objects.filter(vai_tro="giang_vien", is_active=True)
        self.fields["giang_vien"].empty_label = "Tìm và chọn giảng viên"
        self.fields["phong_hoc"].queryset = PhongHoc.objects.exclude(trang_thai="bao_tri").order_by("ma_phong")
        self.fields["phong_hoc"].empty_label = "Tìm và chọn phòng học"

    def clean(self):
        cleaned = super().clean()
        mon_hoc = cleaned.get("mon_hoc")
        lop_hoc = cleaned.get("lop_hoc")
        tiet_bd = cleaned.get("tiet_bat_dau")
        tiet_kt = cleaned.get("tiet_ket_thuc")
        phong = cleaned.get("phong_hoc")
        gv = cleaned.get("giang_vien")
        ngay = cleaned.get("ngay_hoc")

        if tiet_bd and tiet_kt and tiet_bd >= tiet_kt:
            raise forms.ValidationError("Tiet bat dau phai nho hon tiet ket thuc.")

        if lop_hoc and lop_hoc.mon_hoc_id and mon_hoc and lop_hoc.mon_hoc_id != mon_hoc.id:
            raise forms.ValidationError("Môn học phải khớp với lớp học phần đã chọn.")

        exclude_id = self.instance.pk if self.instance.pk else None

        if phong and ngay and tiet_bd and tiet_kt:
            if LichHoc.kiem_tra_trung_phong(phong.id, ngay, tiet_bd, tiet_kt, exclude_id):
                raise forms.ValidationError(f"Phong {phong.ma_phong} da co lich trong khoang thoi gian nay.")

        if gv and ngay and tiet_bd and tiet_kt:
            if LichHoc.kiem_tra_trung_giang_vien(gv.id, ngay, tiet_bd, tiet_kt, exclude_id):
                raise forms.ValidationError(f"Giang vien {gv.ho_ten} da co lich day trong khoang thoi gian nay.")

        return cleaned
