import os
import random
import django
import math
import argparse

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optidut.settings')
django.setup()

from apps.PhongHoc.models import PhongHoc
from apps.ThietBi.models import ThietBi

def get_realistic_note(ten_tb, trang_thai):
    notes_hoat_dong = [
        "Hoạt động tốt, đã được kiểm tra định kỳ.",
        "Tình trạng sử dụng ổn định, hiệu suất cao.",
        "Thiết bị mới, đang trong thời gian bảo hành.",
        "Đã được bảo dưỡng và vệ sinh sạch sẽ.",
        "Sẵn sàng phục vụ công tác giảng dạy.",
        "Chỉ số kỹ thuật đạt chuẩn, không có dấu hiệu bất thường.",
        "Kết nối ổn định, đã cấu hình tối ưu.",
    ]
    
    notes_hong = {
        "Điều hòa nhiệt độ": ["Hết gas, cần nạp bổ sung.", "Máy nén có tiếng kêu lạ, cần kiểm tra.", "Bị chảy nước ở dàn lạnh."],
        "Máy chiếu (Projector)": ["Bóng đèn máy chiếu đã hết tuổi thọ.", "Lỗi hệ thống màu (bị vàng màn hình).", "Không nhận tín hiệu từ cổng HDMI."],
        "Máy tính để bàn (Workstation)": ["Hỏng nguồn, không khởi động được.", "Lỗi ổ cứng, cần thay thế SSD.", "RAM bị lỗi, máy thường xuyên bị treo."],
        "Bộ phát WiFi (Access Point)": ["Hỏng cổng mạng LAN.", "Chip phát sóng yếu, cần thay mới.", "Lỗi firmware không thể reset."],
        "Micro không dây": ["Hỏng củ mic, âm thanh chập chờn.", "Mất kết nối với bộ thu.", "Pin bị rò rỉ làm hỏng mạch tiếp xúc."],
        "Màn chiếu điện": ["Kẹt motor, không thể cuộn lên/xuống.", "Vải màn bị rách, ảnh hưởng hiển thị.", "Hỏng bộ điều khiển từ xa."],
        "default": ["Gặp sự cố kỹ thuật, đang chờ kiểm tra.", "Lỗi phần cứng nghiêm trọng.", "Không đảm bảo an toàn khi sử dụng."]
    }
    
    notes_bao_tri = [
        "Đang bảo trì định kỳ theo kế hoạch quý.",
        "Đang vệ sinh và tra dầu máy.",
        "Cập nhật phần mềm và kiểm tra bảo mật.",
        "Thay thế linh kiện hao mòn định kỳ.",
        "Dự kiến hoàn thành bảo trì vào cuối tuần này.",
        "Kiểm tra tổng thể hệ thống dây dẫn và kết nối.",
    ]

    if trang_thai == ThietBi.TrangThai.HOAT_DONG:
        return random.choice(notes_hoat_dong)
    elif trang_thai == ThietBi.TrangThai.BAO_TRI:
        return random.choice(notes_bao_tri)
    else: # HONG
        potential_notes = notes_hong.get(ten_tb, notes_hong["default"])
        return random.choice(potential_notes)

def seed_thiet_bi(clear=False):
    if clear:
        print("Dang xoa du lieu thiet bi cu...")
        ThietBi.objects.all().delete()

    rooms = PhongHoc.objects.all()
    if not rooms.exists():
        print("Khong tim thay phong hoc nao trong database. Vui long seed phong hoc truoc.")
        return

    print(f"Dang seed thiet bi cho {rooms.count()} phong hoc...")

    thiet_bi_tao_moi = []
    
    for room in rooms:
        items = []
        
        # 1. Thiết bị chung
        num_ac = max(1, math.ceil(room.suc_chua / 30))
        items.append(("Điều hòa nhiệt độ", num_ac))
        items.append(("Bộ phát WiFi (Access Point)", 1))

        if room.loai_phong == PhongHoc.LoaiPhong.LY_THUYET:
            items.extend([
                ("Máy chiếu (Projector)", 1),
                ("Màn chiếu điện", 1),
                ("Bảng từ trắng", random.randint(1, 2)),
                ("Hệ thống loa treo tường", 1),
                ("Micro không dây", 1),
                ("Bàn ghế giáo viên", 1),
                ("Bàn ghế sinh viên (bộ)", room.suc_chua),
            ])
        
        elif room.loai_phong == PhongHoc.LoaiPhong.THUC_HANH:
            num_pc = room.suc_chua
            items.extend([
                ("Máy tính để bàn (Workstation)", num_pc),
                ("Máy chiếu (Projector)", 1),
                ("Màn chiếu điện", 1),
                ("Bộ chuyển mạch (Switch 24-port)", max(1, math.ceil(num_pc / 20))),
                ("Bảng từ trắng", 1),
                ("Tủ rack thiết bị", 1),
                ("UPS (Bộ lưu điện)", max(1, math.ceil(num_pc / 10))),
            ])
            
        elif room.loai_phong == PhongHoc.LoaiPhong.HOI_TRUONG:
            items.extend([
                ("Máy chiếu công suất lớn", 2),
                ("Màn chiếu kích thước lớn", 2),
                ("Hệ thống âm thanh hội trường", 1),
                ("Micro không dây cầm tay", 4),
                ("Micro cổ ngỗng (để bục)", 2),
                ("Camera quan sát PTZ", 2),
                ("Bàn trộn âm thanh (Mixer)", 1),
                ("Hệ thống đèn sân khấu", 1),
                ("Bàn ghế đại biểu (bộ)", 10),
                ("Ghế hội trường (cố định)", room.suc_chua),
            ])

        for ten, so_luong in items:
            rand = random.random()
            if rand < 0.03:
                trang_thai = ThietBi.TrangThai.HONG
            elif rand < 0.06:
                trang_thai = ThietBi.TrangThai.BAO_TRI
            else:
                trang_thai = ThietBi.TrangThai.HOAT_DONG

            ghi_chu = get_realistic_note(ten, trang_thai)

            thiet_bi_tao_moi.append(ThietBi(
                phong_hoc=room,
                ten_thiet_bi=ten,
                so_luong=so_luong,
                trang_thai=trang_thai,
                ghi_chu=ghi_chu
            ))

    ThietBi.objects.bulk_create(thiet_bi_tao_moi)
    print(f"Da hoan thanh seed {len(thiet_bi_tao_moi)} thiet bi cho {rooms.count()} phong.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--clear', action='store_true', help='Xoa du lieu cu truoc khi seed')
    args = parser.parse_args()
    
    seed_thiet_bi(clear=args.clear)
