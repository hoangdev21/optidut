# 📋 QUY TẮC PHÁT TRIỂN - HỆ THỐNG OPTIDUT
> Hệ thống tối ưu hóa sử dụng phòng học - Đại học Bách Khoa Đà Nẵng

---

## 1. CÔNG NGHỆ SỬ DỤNG

| Thành phần | Công nghệ |
|---|---|
| Backend | Python 3.11+, Django 5.x |
| Frontend | HTML5, CSS3 (Vanilla), JavaScript (ES6+) |
| Database | MySQL 8.x |
| Template Engine | Django Template Language |
| Auth | Django Authentication System |

---

## 2. QUY TẮC ĐẶT TÊN

### 2.1 Tên file & thư mục
- Đặt tên **tiếng Việt không dấu**, viết liền, **viết hoa chữ cái đầu mỗi từ** (PascalCase)
- Ví dụ: `NguoiDung.py`, `PhongHoc.py`, `LichHoc.py`, `ThietBi.py`
- File template HTML cũng tuân thủ: `DanhSachPhong.html`, `ChiTietLich.html`

### 2.2 Tên model/class
- PascalCase tiếng Việt không dấu: `NguoiDung`, `PhongHoc`, `LichHoc`, `ThietBi`

### 2.3 Tên biến & hàm
- snake_case tiếng Việt không dấu: `danh_sach_phong`, `tao_lich_hoc`, `cap_nhat_phong`

### 2.4 URL patterns
- Dùng kebab-case tiếng Anh ngắn gọn: `/rooms/`, `/schedules/`, `/equipment/`

---

## 3. QUY TẮC THIẾT KẾ UI/UX

### 3.1 Tone màu chủ đạo

```
Xanh dương chính:  #003366  (Header, sidebar, nút chính, tiêu đề)
Trắng nền:         #FFFFFF  (Nền trang, card, bảng)
Cam nhấn:          #FF6600  (Nút hành động, badge, cảnh báo, hover)
```

Màu phụ trợ:
```
Xám nhạt nền:      #F5F7FA  (Nền body, nền phụ)
Xám viền:          #DEE2E6  (Border bảng, divider)
Xám chữ phụ:       #6C757D  (Text phụ, placeholder)
Đen chữ chính:     #212529  (Text chính)
Xanh nhạt hover:   #004080  (Hover trên nút xanh)
Cam nhạt hover:    #E55A00  (Hover trên nút cam)
Xanh thành công:   #28A745  (Trạng thái hoạt động, thành công)
Đỏ cảnh báo:       #DC3545  (Xóa, lỗi, trạng thái hỏng)
Vàng chờ:          #FFC107  (Trạng thái bảo trì, chờ xử lý)
```

### 3.2 Quy tắc CSS bắt buộc

- **KHÔNG dùng gradient** (background, text, border - tất cả đều flat color)
- **Hạn chế border-radius**: chỉ dùng `2px` đến `4px` khi cần, KHÔNG dùng `border-radius` lớn (>6px)
- **KHÔNG dùng box-shadow quá đậm**: chỉ dùng shadow rất nhẹ `0 1px 3px rgba(0,0,0,0.1)` nếu cần
- Font chữ: `'Segoe UI', 'Roboto', sans-serif`
- Font-size cơ bản: `14px` cho body, `13px` cho bảng

### 3.3 Responsive Design

Hệ thống PHẢI responsive trên tất cả thiết bị:

```css
/* Mobile */
@media (max-width: 576px) { ... }
/* Tablet */
@media (max-width: 768px) { ... }
/* Tablet ngang */
@media (max-width: 992px) { ... }
/* Desktop */
@media (min-width: 993px) { ... }
```

Quy tắc responsive:
- Sidebar thu gọn thành hamburger menu trên mobile/tablet
- Bảng dữ liệu có scroll ngang trên mobile
- Form input full-width trên mobile
- Card layout chuyển từ grid sang stack trên mobile

---

## 4. CẤU TRÚC THƯ MỤC DỰ ÁN

```
dut-opti/
├── rules.md
├── requirements.txt
├── manage.py
├── optidut/                    # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── NguoiDung/              # Quản lý người dùng
│   │   ├── models.py, views.py, urls.py, forms.py, admin.py
│   ├── PhongHoc/               # Quản lý phòng học
│   │   ├── models.py, views.py, urls.py, forms.py
│   ├── LichHoc/                # Quản lý lịch học
│   │   ├── models.py, views.py, urls.py, forms.py
│   ├── ThietBi/                # Quản lý thiết bị
│   │   ├── models.py, views.py, urls.py, forms.py
│   ├── ThongKe/                # Thống kê, báo cáo
│   │   ├── views.py, urls.py, utils.py
│   └── ThongBao/               # Thông báo
│       ├── models.py, views.py, urls.py
├── templates/
│   ├── base.html
│   ├── components/             # Sidebar, Header, Pagination, Modal
│   ├── NguoiDung/              # DangNhap, DanhSach, ThemMoi, ChinhSua
│   ├── PhongHoc/               # DanhSach, ChiTiet, ThemMoi, ChinhSua
│   ├── LichHoc/                # DanhSach, ThemMoi, ChinhSua, TraCuu
│   ├── ThietBi/                # DanhSach, ThemMoi, BaoHong
│   ├── ThongKe/                # TongQuan, BaoCao
│   ├── ThongBao/               # DanhSach
│   └── Dashboard/              # QuanTriVien, GiaoVu, GiangVien, SinhVien
├── static/
│   ├── css/                    # base.css, components.css, forms.css, tables.css, responsive.css
│   ├── js/                     # main.js, LichHoc.js, PhongHoc.js, ThongKe.js
│   └── img/                    # logo-dut.png
└── media/
    └── exports/                # File báo cáo xuất ra
```

---

## 5. PHÂN QUYỀN THEO VAI TRÒ

| Chức năng | Quản trị viên | Giáo vụ | Giảng viên | Sinh viên |
|---|:---:|:---:|:---:|:---:|
| Quản lý tài khoản (CRUD) | ✅ | ❌ | ❌ | ❌ |
| Quản lý phòng học (CRUD) | ✅ | ✅ | ❌ | ❌ |
| Quản lý lịch học (CRUD) | ❌ | ✅ | ❌ | ❌ |
| Tra cứu phòng học | ✅ | ✅ | ✅ | ✅ |
| Xem lịch học | ✅ | ✅ | ✅ | ✅ |
| Quản lý thiết bị | ✅ | ✅ | ❌ | ❌ |
| Báo hỏng thiết bị | ✅ | ✅ | ✅ | ❌ |
| Xem thống kê / báo cáo | ✅ | ✅ | ❌ | ❌ |
| Xuất báo cáo | ✅ | ✅ | ❌ | ❌ |
| Nhận thông báo | ✅ | ✅ | ✅ | ✅ |

---

## 6. CƠ SỞ DỮ LIỆU - CÁC BẢNG CHÍNH

### NguoiDung
| Cột | Kiểu | Mô tả |
|---|---|---|
| id | INT PK AUTO | Mã người dùng |
| username | VARCHAR(50) | Tên đăng nhập |
| password | VARCHAR(255) | Mật khẩu (hash) |
| ho_ten | VARCHAR(100) | Họ tên đầy đủ |
| email | VARCHAR(100) | Email |
| vai_tro | ENUM | quan_tri, giao_vu, giang_vien, sinh_vien |
| is_active | BOOLEAN | Trạng thái hoạt động |

### PhongHoc
| Cột | Kiểu | Mô tả |
|---|---|---|
| id | INT PK AUTO | Mã tự tăng |
| ma_phong | VARCHAR(20) | Mã phòng (VD: A101) |
| ten_phong | VARCHAR(100) | Tên phòng |
| suc_chua | INT | Số chỗ ngồi |
| loai_phong | VARCHAR(50) | Lý thuyết / Thực hành / Hội trường |
| trang_thai | ENUM | trong, dang_su_dung, bao_tri |
| toa_nha | VARCHAR(50) | Tòa nhà |

### ThietBi
| Cột | Kiểu | Mô tả |
|---|---|---|
| id | INT PK AUTO | Mã thiết bị |
| ten_thiet_bi | VARCHAR(100) | Tên thiết bị |
| phong_hoc_id | FK -> PhongHoc | Phòng chứa thiết bị |
| trang_thai | ENUM | hoat_dong, hong, bao_tri |
| ghi_chu | TEXT | Ghi chú |

### LichHoc
| Cột | Kiểu | Mô tả |
|---|---|---|
| id | INT PK AUTO | Mã lịch học |
| mon_hoc | VARCHAR(100) | Tên môn học |
| ma_lop | VARCHAR(20) | Mã lớp |
| giang_vien_id | FK -> NguoiDung | Giảng viên |
| phong_hoc_id | FK -> PhongHoc | Phòng học |
| ngay_hoc | DATE | Ngày học |
| tiet_bat_dau | INT | Tiết bắt đầu |
| tiet_ket_thuc | INT | Tiết kết thúc |
| trang_thai | ENUM | hoat_dong, da_huy |

### ThongBao
| Cột | Kiểu | Mô tả |
|---|---|---|
| id | INT PK AUTO | Mã thông báo |
| tieu_de | VARCHAR(200) | Tiêu đề |
| noi_dung | TEXT | Nội dung |
| loai | ENUM | doi_phong, doi_lich, huy_lich, bao_tri |
| nguoi_tao_id | FK -> NguoiDung | Người tạo |
| ngay_tao | DATETIME | Ngày tạo |
| da_doc | BOOLEAN | Đã đọc chưa |

---

## 7. QUY TẮC VIẾT CODE

### Backend (Django)
- Mỗi app xử lý 1 module nghiệp vụ riêng biệt
- Dùng Class-Based Views cho CRUD, Function-Based Views cho logic đặc biệt
- Validate dữ liệu bằng Django Forms
- Dùng Django ORM, KHÔNG viết raw SQL
- Phân quyền bằng decorator `@login_required` và kiểm tra `vai_tro`
- Mỗi view phải kiểm tra quyền trước khi xử lý

### Frontend (Templates)
- Kế thừa từ `base.html` bằng `{% extends %}`
- Tái sử dụng component bằng `{% include %}`
- Tách CSS theo module, load bằng `{% block extra_css %}`
- JS đặt cuối body hoặc trong `{% block extra_js %}`
- KHÔNG dùng inline style, KHÔNG dùng inline JS

### CSS
- Dùng CSS Variables trong `:root` cho màu sắc và spacing
- Mobile-first approach
- KHÔNG gradient, hạn chế border-radius (max 4px)
- Flat design, clean, professional

---

## 8. QUY TRÌNH PHÁT TRIỂN

1. Tạo Django project `optidut` và cấu hình MySQL
2. Tạo các Django apps theo cấu trúc thư mục
3. Định nghĩa models và migrate database
4. Xây dựng `base.html` + CSS hệ thống (sidebar, header)
5. Triển khai module NguoiDung (đăng nhập, phân quyền)
6. Triển khai module PhongHoc
7. Triển khai module LichHoc
8. Triển khai module ThietBi
9. Triển khai module ThongKe
10. Triển khai module ThongBao
11. Test responsive trên các thiết bị
12. Tối ưu và hoàn thiện
