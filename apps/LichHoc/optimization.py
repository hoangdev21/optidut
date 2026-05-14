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
        tiet_bat_dau__lt=tiet_kt,
        tiet_ket_thuc__gt=tiet_bd,
        trang_thai='hoat_dong'
    ).values_list('phong_hoc_id', flat=True)
    # 2. Lấy phòng trống và đủ sức chứa
    phong_trong = PhongHoc.objects.exclude(id__in=phong_ban_ids).filter(
        suc_chua__gte=si_so,
        trang_thai='trong'
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
