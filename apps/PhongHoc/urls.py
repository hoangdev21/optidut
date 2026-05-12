from django.urls import path
from . import views

urlpatterns = [
    path('', views.danh_sach_phong, name='danh_sach_phong'),
    path('so-do/', views.so_do_phong, name='so_do_phong'),
    path('<int:pk>/', views.chi_tiet_phong, name='chi_tiet_phong'),
    path('add/', views.them_phong, name='them_phong'),
    path('<int:pk>/edit/', views.chinh_sua_phong, name='chinh_sua_phong'),
    path('<int:pk>/delete/', views.xoa_phong, name='xoa_phong'),
]
