from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.NguoiDung.urls')),
    path('dashboard/', include('apps.NguoiDung.urls_dashboard')),
    path('rooms/', include('apps.PhongHoc.urls')),
    path('schedules/', include('apps.LichHoc.urls')),
    path('equipment/', include('apps.ThietBi.urls')),
    path('statistics/', include('apps.ThongKe.urls')),
    path('notifications/', include('apps.ThongBao.urls')),
    path('', include('apps.NguoiDung.urls_dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
