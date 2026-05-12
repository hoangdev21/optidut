from django.urls import path
from . import views

urlpatterns = [
    path('', views.danh_sach_thong_bao, name='danh_sach_thong_bao'),
    path('<int:pk>/read/', views.danh_dau_da_doc, name='danh_dau_da_doc'),
    path('read-all/', views.doc_tat_ca, name='doc_tat_ca'),
]
