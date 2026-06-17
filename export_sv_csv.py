import django, os, csv, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optidut.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.NguoiDung.models import NguoiDung

svs = NguoiDung.objects.filter(vai_tro='sinh_vien', is_active=True).order_by('ma_so')

with open('import_sv_mau.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['ma_so'])
    for sv in svs:
        w.writerow([sv.ma_so])

print(f'Da xuat {svs.count()} sinh vien ra file import_sv_mau.csv')
