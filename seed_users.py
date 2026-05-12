import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optidut.settings')
django.setup()

from apps.NguoiDung.models import NguoiDung

def seed_users():
    users = [
        {'username': 'admin', 'vai_tro': NguoiDung.VaiTro.QUAN_TRI, 'ho_ten': 'Quản trị viên', 'ma_so': 'ADMIN'},
        {'username': 'giaovu', 'vai_tro': NguoiDung.VaiTro.GIAO_VU, 'ho_ten': 'Nguyễn Minh Hạnh', 'ma_so': 'GV01'},
        {'username': 'giangvien', 'vai_tro': NguoiDung.VaiTro.GIANG_VIEN, 'ho_ten': 'Nguyễn Văn Giảng', 'ma_so': 'GV02'},
        {'username': 'sinhvien', 'vai_tro': NguoiDung.VaiTro.SINH_VIEN, 'ho_ten': 'Trần Văn Sinh', 'ma_so': 'SV01'}
    ]

    for user_data in users:
        user, created = NguoiDung.objects.get_or_create(username=user_data['username'])
        user.ho_ten = user_data['ho_ten']
        user.vai_tro = user_data['vai_tro']
        user.ma_so = user_data['ma_so']
        user.set_password(user_data['username']) # Default password same as username
        
        if user.vai_tro == NguoiDung.VaiTro.QUAN_TRI:
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
            
        user.save()
        
    print("Seeding completed successfully.")

if __name__ == '__main__':
    seed_users()
