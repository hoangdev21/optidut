from apps.PhongHoc.models import PhongHoc
from .models import LichHoc, LopHoc

def algorithm_room_scoring(ngay, tiet_bd, tiet_kt, si_so, khoa_id=None, lop_id=None):
    """
    Thuật toán Heuristic Scoring (Rule-based Greedy)
    Dùng để tìm và xếp hạng phòng học tối ưu cho một lớp học phần.
    Cách hoạt động:
    1. Lọc: Loại bỏ các phòng đã bận hoặc đang bảo trì.
    2. Lọc: Chỉ giữ các phòng có sức chứa >= sĩ số lớp.
    3. Chấm điểm (Scoring):
       - Điểm gốc: 100 điểm.
       - Phạt sức chứa (Capacity Penalty): Tránh lãng phí phòng lớn cho lớp nhỏ.
       - Cộng điểm vị trí (Location Bonus): Ưu tiên tòa nhà gần khoa quản lý.
       - Cộng điểm thiết bị (Feature Bonus): Ưu tiên phòng có điều hòa/thiết bị tốt.
    4. Sắp xếp: Trả về danh sách phòng theo thứ tự điểm từ cao xuống thấp.
    """
    # 1. Tìm danh sách phòng bận
    phong_ban_ids = LichHoc.objects.filter(
        ngay_hoc=ngay,
        tiet_bat_dau__lte=tiet_kt,
        tiet_ket_thuc__gte=tiet_bd,
        trang_thai='hoat_dong'
    ).values_list('phong_hoc_id', flat=True)
    # 2. Lấy phòng trống và đủ sức chứa (loại trừ Khu A hành chính)
    phong_trong = PhongHoc.objects.exclude(id__in=phong_ban_ids).filter(
        suc_chua__gte=si_so,
        trang_thai='trong'
    ).exclude(
        toa_nha__icontains='Tòa A'
    ).exclude(
        toa_nha__icontains='Khu A'
    ).exclude(
        ma_phong__istartswith='A'
    )
    # Lấy danh sách tòa nhà khoa này hay dùng nhất (Top 2) - Chỉ truy vấn 1 lần duy nhất
    toa_nha_uu_tien = []
    if khoa_id:
        from django.db.models import Count
        toa_nha_uu_tien = list(LichHoc.objects.filter(lop_hoc__khoa=khoa_id)
            .values_list('phong_hoc__toa_nha', flat=True)
            .annotate(count=Count('id'))
            .order_by('-count')[:2])
    ket_qua = []
    for phong in phong_trong:
        # Điểm cơ bản
        score = 100
        # Tiêu chí 1: Tối ưu sức chứa (Best-fit Heuristic)
        # Càng gần sĩ số thực tế càng tốt. Mỗi chỗ trống dư ra trừ 2 điểm.
        chenh_lech = phong.suc_chua - si_so
        score -= (chenh_lech * 2)
        # Tiêu chí 2: Ưu tiên khu vực
        if phong.toa_nha in toa_nha_uu_tien:
            score += 40
        # Tiêu chí 3: Tiện nghi 
        if phong.ghi_chu and "Điều hòa" in phong.ghi_chu:
            score += 15
        # Đảm bảo không bị điểm âm quá thấp
        score = max(0, score)
        ket_qua.append({
            'phong_obj': phong,
            'score': score,
            'ma_phong': phong.ma_phong,
            'toa_nha': phong.toa_nha,
            'suc_chua': phong.suc_chua,
            'ly_do': f"Sức chứa phù hợp ({phong.suc_chua}), " + 
                     ("Có điều hòa, " if "Điều hòa" in (phong.ghi_chu or "") else "") +
                     (f"Gần khu vực {phong.toa_nha}" if score > 100 else "")
        })
    # Sắp xếp theo điểm giảm dần
    ket_qua = sorted(ket_qua, key=lambda x: x['score'], reverse=True)
    return ket_qua


def optimize_classroom_allocation(lich_hocs):
    """
    Thuật toán tối ưu hóa phân bổ phòng học hàng loạt.
    Tối ưu hóa sức chứa, giảm thiểu thời gian di chuyển của sinh viên và loại trừ khu A.
    """
    from django.db.models import Count
    from apps.PhongHoc.models import PhongHoc
    
    # 1. Lấy tất cả phòng học đủ điều kiện (loại trừ Tòa A, Khu A và không bảo trì)
    rooms = list(PhongHoc.objects.exclude(trang_thai='bao_tri')
                 .exclude(toa_nha__icontains='Tòa A')
                 .exclude(toa_nha__icontains='Khu A')
                 .exclude(ma_phong__istartswith='A'))

    # 2. Phân nhóm các lịch học theo ngày
    schedules_by_date = {}
    for lh in lich_hocs:
        date_key = lh.ngay_hoc
        if date_key not in schedules_by_date:
            schedules_by_date[date_key] = []
        schedules_by_date[date_key].append(lh)

    results = []

    # Duyệt qua từng ngày học riêng biệt
    for ngay_hoc, lh_list in schedules_by_date.items():
        # Lấy tất cả các lịch học KHÁC đang diễn ra trong ngày học này để xác định thời gian bận của các phòng
        # (những lịch này không nằm trong danh sách xếp phòng tự động hiện tại nên được coi là cố định)
        selected_ids = [lh.id for lh in lh_list]
        other_schedules = list(LichHoc.objects.filter(ngay_hoc=ngay_hoc, trang_thai='hoat_dong')
                               .exclude(id__in=selected_ids)
                               .select_related('phong_hoc'))

        # Khởi tạo ma trận bận của phòng trong ngày:
        # room_occupancy[room_id] = list of (tiet_bd, tiet_kt)
        room_occupancy = {}
        for os in other_schedules:
            rid = os.phong_hoc_id
            if rid not in room_occupancy:
                room_occupancy[rid] = []
            room_occupancy[rid].append((os.tiet_bat_dau, os.tiet_ket_thuc))

        # Phân nhóm lịch cần xếp của ngày này theo lớp học học phần (để tối ưu hóa di chuyển của lớp)
        class_groups = {}
        for lh in lh_list:
            class_key = lh.lop_hoc_id or lh.ma_lop
            if class_key not in class_groups:
                class_groups[class_key] = []
            class_groups[class_key].append(lh)

        # Sắp xếp các lớp học phần theo sĩ số tối đa giảm dần để ưu tiên xếp các lớp đông sinh viên trước
        sorted_classes = []
        for class_key, lh_group in class_groups.items():
            lh_group_sorted = sorted(lh_group, key=lambda x: x.tiet_bat_dau)
            max_si_so = max(lh.si_so for lh in lh_group)
            sorted_classes.append((class_key, lh_group_sorted, max_si_so))

        sorted_classes = sorted(sorted_classes, key=lambda x: x[2], reverse=True)

        # Lưu trữ phân bổ phòng tạm thời trong ngày này cho các lịch học mới:
        # temporary_allocations[room_id] = list of (tiet_bd, tiet_kt)
        temporary_allocations = {}

        # Hàm kiểm tra xem phòng học có rảnh trong khoảng tiết học hay không
        def is_room_free(room_id, tiet_bd, tiet_kt):
            # Kiểm tra lịch cố định khác
            for o_bd, o_kt in room_occupancy.get(room_id, []):
                if not (tiet_kt < o_bd or tiet_bd > o_kt):
                    return False
            # Kiểm tra lịch tạm thời vừa được phân bổ
            for t_bd, t_kt in temporary_allocations.get(room_id, []):
                if not (tiet_kt < t_bd or tiet_bd > t_kt):
                    return False
            return True

        # Tiến hành phân bổ phòng cho từng nhóm lớp
        for class_key, lh_group, max_si_so in sorted_classes:
            previous_allocated_room = None
            
            # Lấy tòa nhà ưu tiên cho khoa quản lý của lớp học phần này (nếu có khoa)
            toa_nha_uu_tien = []
            first_lh = lh_group[0]
            if first_lh.lop_hoc and first_lh.lop_hoc.khoa:
                toa_nha_uu_tien = list(LichHoc.objects.filter(lop_hoc__khoa=first_lh.lop_hoc.khoa)
                    .values_list('phong_hoc__toa_nha', flat=True)
                    .annotate(count=Count('id'))
                    .order_by('-count')[:2])

            for lh in lh_group:
                # 3. Lọc phòng:
                # - Sức chứa >= Sĩ số lớp
                # - Rảnh trong khung giờ (tiet_bat_dau -> tiet_ket_thuc)
                eligible_rooms = []
                for room in rooms:
                    if room.suc_chua >= lh.si_so and is_room_free(room.id, lh.tiet_bat_dau, lh.tiet_ket_thuc):
                        eligible_rooms.append(room)

                if not eligible_rooms:
                    # Không tìm thấy phòng trống phù hợp
                    results.append({
                        'lich_obj': lh,
                        'success': False,
                        'room_allocated': None,
                        'score': 0,
                        'reason': 'Không có phòng học trống phù hợp với sức chứa và thời gian học.'
                    })
                    continue

                # 4. Chấm điểm các phòng đủ điều kiện
                scored_rooms = []
                for room in eligible_rooms:
                    score = 100
                    reasons = []

                    # Tiêu chí 1: Tối ưu sức chứa (Best-fit)
                    chenh_lech = room.suc_chua - lh.si_so
                    score -= (chenh_lech * 1) # Mỗi chỗ trống thừa trừ 1 điểm
                    reasons.append(f"Dư {chenh_lech} chỗ")

                    # Tiêu chí 2: Ưu tiên tòa nhà gần khoa
                    if room.toa_nha in toa_nha_uu_tien:
                        score += 30
                        reasons.append(f"Gần khoa {first_lh.lop_hoc.khoa}")

                    # Tiêu chí 3: Tối ưu di chuyển (so với tiết học trước của cùng lớp)
                    if previous_allocated_room:
                        if room.id == previous_allocated_room.id:
                            score += 80  # Ưu tiên cực lớn cho việc học cùng một phòng
                            reasons.append("Học cùng phòng với tiết trước")
                        elif room.toa_nha == previous_allocated_room.toa_nha:
                            score += 40  # Ưu tiên lớn cho việc học cùng tòa nhà
                            reasons.append("Học cùng tòa nhà với tiết trước")
                    
                    # Đảm bảo điểm số không âm
                    score = max(0, score)
                    scored_rooms.append((room, score, reasons))

                # Chọn phòng có điểm số cao nhất
                scored_rooms = sorted(scored_rooms, key=lambda x: x[1], reverse=True)
                best_room, best_score, best_reasons = scored_rooms[0]

                # Ghi nhận phân bổ tạm thời
                if best_room.id not in temporary_allocations:
                    temporary_allocations[best_room.id] = []
                temporary_allocations[best_room.id].append((lh.tiet_bat_dau, lh.tiet_ket_thuc))

                previous_allocated_room = best_room

                results.append({
                    'lich_obj': lh,
                    'success': True,
                    'room_allocated': best_room,
                    'score': best_score,
                    'reason': ", ".join(best_reasons)
                })

    return results
