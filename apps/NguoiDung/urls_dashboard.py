from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin-panel/', views.dashboard_quan_tri, name='dashboard_quan_tri'),
    path('academic/', views.dashboard_giao_vu, name='dashboard_giao_vu'),
    path('lecturer/', views.dashboard_giang_vien, name='dashboard_giang_vien'),
    path('student/', views.dashboard_sinh_vien, name='dashboard_sinh_vien'),
]
