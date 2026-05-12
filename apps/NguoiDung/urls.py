from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.dang_nhap, name='dang_nhap'),
    path('logout/', views.dang_xuat, name='dang_xuat'),
    path('users/', views.danh_sach_nguoi_dung, name='danh_sach_nguoi_dung'),
    path('users/add/', views.them_nguoi_dung, name='them_nguoi_dung'),
    path('users/<int:pk>/edit/', views.chinh_sua_nguoi_dung, name='chinh_sua_nguoi_dung'),
    path('users/<int:pk>/delete/', views.xoa_nguoi_dung, name='xoa_nguoi_dung'),
    path('profile/', views.thong_tin_ca_nhan, name='thong_tin_ca_nhan'),
]
