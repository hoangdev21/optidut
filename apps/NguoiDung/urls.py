from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.dang_nhap, name='dang_nhap'),
    path('logout/', views.dang_xuat, name='dang_xuat'),
    path('users/', views.danh_sach_nguoi_dung, name='danh_sach_nguoi_dung'),
    path('users/add/', views.them_nguoi_dung, name='them_nguoi_dung'),
    path('users/import-csv/', views.nhap_nguoi_dung_csv, name='nhap_nguoi_dung_csv'),
    path('users/import-progress/', views.lay_tien_do_nhap_csv, name='lay_tien_do_nhap_csv'),
    path('users/export-csv/', views.xuat_nguoi_dung_csv, name='xuat_nguoi_dung_csv'),
    path('users/<int:pk>/edit/', views.chinh_sua_nguoi_dung, name='chinh_sua_nguoi_dung'),
    path('users/<int:pk>/delete/', views.xoa_nguoi_dung, name='xoa_nguoi_dung'),
    path('users/<int:pk>/reset-password/', views.reset_mat_khau, name='reset_mat_khau'),
    path('users/bulk-delete/', views.xoa_hang_loat_nguoi_dung, name='xoa_hang_loat_nguoi_dung'),
    path('classes/', views.danh_sach_lop_sinh_hoat, name='danh_sach_lop_sinh_hoat'),
    path('classes/<int:pk>/edit/', views.sua_lop_sinh_hoat, name='sua_lop_sinh_hoat'),
    path('classes/<int:pk>/delete/', views.xoa_lop_sinh_hoat, name='xoa_lop_sinh_hoat'),
    path('profile/', views.thong_tin_ca_nhan, name='thong_tin_ca_nhan'),
]
