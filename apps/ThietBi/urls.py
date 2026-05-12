from django.urls import path
from . import views

urlpatterns = [
    path('', views.danh_sach_thiet_bi, name='danh_sach_thiet_bi'),
    path('add/', views.them_thiet_bi, name='them_thiet_bi'),
    path('<int:pk>/edit/', views.chinh_sua_thiet_bi, name='chinh_sua_thiet_bi'),
    path('<int:pk>/delete/', views.xoa_thiet_bi, name='xoa_thiet_bi'),
    path('reports/', views.danh_sach_bao_hong, name='danh_sach_bao_hong'),
    path('reports/<int:pk>/status/', views.cap_nhat_trang_thai_bao_hong, name='cap_nhat_trang_thai_bao_hong'),
    path('report-issue/', views.bao_hong, name='bao_hong'),
]
