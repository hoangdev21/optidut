from django.urls import path
from . import views

urlpatterns = [
    path('', views.tong_quan, name='thong_ke_tong_quan'),
    path('export/', views.xuat_bao_cao, name='xuat_bao_cao'),
]
