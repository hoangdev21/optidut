from django.urls import path
from . import views

urlpatterns = [
    path('danh-sach/', views.danh_sach_lich, name='danh_sach_lich'),
    path('them-moi/', views.them_lich, name='them_lich'),
    path('them-moi-hang-loat/', views.them_lich_hang_loat, name='them_lich_hang_loat'),
    path('chinh-sua/<int:pk>/', views.chinh_sua_lich, name='chinh_sua_lich'),
    path('huy-lich/<int:pk>/', views.huy_lich, name='huy_lich'),
    path('xoa-lich/<int:pk>/', views.xoa_lich, name='xoa_lich'),
    path('tra-cuu/', views.tra_cuu_phong, name='tra_cuu_phong'),
    path('goi-y-phong/', views.goi_y_phong_toi_uu, name='goi_y_phong'),
    path('api/loc-lop-theo-mon/', views.api_loc_lop_theo_mon, name='api_loc_lop_theo_mon'),
    # Khung giờ & Thời khóa biểu
    path('khung-gio/', views.khung_gio_hoc, name='khung_gio_hoc'),
    path('thoi-khoa-bieu/', views.thoi_khoa_bieu_tuan, name='thoi_khoa_bieu_tuan'),
    # Quản lý lớp học
    path('lop/danh-sach/', views.danh_sach_lop, name='danh_sach_lop'),
    path('lop/import-progress/', views.lay_tien_do_nhap_lop_csv, name='lay_tien_do_nhap_lop_csv'),
    path('lop/import-csv/', views.nhap_lop_hoc_csv, name='nhap_lop_hoc_csv'),
    path('lop/export-csv/', views.xuat_lop_hoc_csv, name='xuat_lop_hoc_csv'),
    path('lop/them-moi/', views.them_lop, name='them_lop'),
    path('lop/chinh-sua/<int:pk>/', views.chinh_sua_lop, name='chinh_sua_lop'),
    # Quản lý SV trong lớp HP
    path('lop/<int:pk>/sinh-vien/', views.danh_sach_sv_lop, name='danh_sach_sv_lop'),
    path('lop/<int:pk>/them-sv/', views.them_sv_vao_lop, name='them_sv_vao_lop'),
    path('lop/<int:pk>/xoa-sv/<int:sv_id>/', views.xoa_sv_khoi_lop, name='xoa_sv_khoi_lop'),
    # Yêu cầu đổi lịch
    path('yeu-cau/tao/<int:lich_pk>/', views.tao_yeu_cau_doi_lich, name='tao_yeu_cau_doi_lich'),
    path('yeu-cau/hoan-lich/<int:pk>/', views.yeu_cau_hoan_lich, name='yeu_cau_hoan_lich'),
    path('yeu-cau/danh-sach/', views.danh_sach_yeu_cau, name='danh_sach_yeu_cau'),
    path('yeu-cau/chinh-sua/<int:pk>/', views.chinh_sua_yeu_cau, name='chinh_sua_yeu_cau'),
    path('yeu-cau/duyet/<int:pk>/', views.duyet_yeu_cau, name='duyet_yeu_cau'),
    path('lich-su-thay-doi/', views.lich_su_thay_doi, name='lich_su_thay_doi'),
]
