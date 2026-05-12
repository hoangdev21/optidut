from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import NguoiDung


@admin.register(NguoiDung)
class NguoiDungAdmin(UserAdmin):
    list_display = ('username', 'ho_ten', 'email', 'vai_tro', 'is_active')
    list_filter = ('vai_tro', 'is_active')
    search_fields = ('username', 'ho_ten', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin bổ sung', {'fields': ('ho_ten', 'vai_tro', 'ma_so')}),
    )
