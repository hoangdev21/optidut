-- 1. Tạo Database
CREATE DATABASE IF NOT EXISTS optidut_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE optidut_db;

-- 2. Bảng Người dùng (Kế thừa từ Django AbstractUser)
CREATE TABLE IF NOT EXISTS nguoi_dung (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME,
    is_superuser BOOLEAN NOT NULL DEFAULT 0,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    email VARCHAR(254),
    is_staff BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    date_joined DATETIME NOT NULL,
    ho_ten VARCHAR(100),
    vai_tro ENUM('quan_tri', 'giao_vu', 'giang_vien', 'sinh_vien') DEFAULT 'sinh_vien',
    ma_so VARCHAR(20)
) ENGINE=InnoDB;

-- 3. Bảng Phòng học
CREATE TABLE IF NOT EXISTS phong_hoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_phong VARCHAR(20) NOT NULL UNIQUE,
    ten_phong VARCHAR(100) NOT NULL,
    toa_nha VARCHAR(50) NOT NULL,
    suc_chua INT UNSIGNED DEFAULT 30,
    loai_phong ENUM('ly_thuyet', 'thuc_hanh', 'hoi_truong') DEFAULT 'ly_thuyet',
    trang_thai ENUM('trong', 'dang_su_dung', 'bao_tri') DEFAULT 'trong',
    ghi_chu TEXT,
    ngay_tao DATETIME NOT NULL,
    ngay_cap_nhat DATETIME NOT NULL
) ENGINE=InnoDB;

-- 4. Bảng Thiết bị
CREATE TABLE IF NOT EXISTS thiet_bi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ten_thiet_bi VARCHAR(100) NOT NULL,
    phong_hoc_id INT NOT NULL,
    trang_thai ENUM('hoat_dong', 'hong', 'bao_tri') DEFAULT 'hoat_dong',
    so_luong INT UNSIGNED DEFAULT 1,
    ghi_chu TEXT,
    ngay_tao DATETIME NOT NULL,
    FOREIGN KEY (phong_hoc_id) REFERENCES phong_hoc(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Bảng Lịch học
CREATE TABLE IF NOT EXISTS lich_hoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mon_hoc VARCHAR(100) NOT NULL,
    ma_lop VARCHAR(20) NOT NULL,
    giang_vien_id INT NOT NULL,
    phong_hoc_id INT NOT NULL,
    ngay_hoc DATE NOT NULL,
    tiet_bat_dau INT UNSIGNED NOT NULL,
    tiet_ket_thuc INT UNSIGNED NOT NULL,
    si_so INT UNSIGNED DEFAULT 30,
    trang_thai ENUM('hoat_dong', 'da_huy') DEFAULT 'hoat_dong',
    ghi_chu TEXT,
    ngay_tao DATETIME NOT NULL,
    FOREIGN KEY (giang_vien_id) REFERENCES nguoi_dung(id) ON DELETE CASCADE,
    FOREIGN KEY (phong_hoc_id) REFERENCES phong_hoc(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Bảng Báo hỏng
CREATE TABLE IF NOT EXISTS bao_hong (
    id INT AUTO_INCREMENT PRIMARY KEY,
    thiet_bi_id INT NOT NULL,
    nguoi_bao_id INT NOT NULL,
    mo_ta TEXT NOT NULL,
    trang_thai ENUM('cho_xu_ly', 'dang_su_dua', 'da_sua') DEFAULT 'cho_xu_ly',
    ngay_bao DATETIME NOT NULL,
    FOREIGN KEY (thiet_bi_id) REFERENCES thiet_bi(id) ON DELETE CASCADE,
    FOREIGN KEY (nguoi_bao_id) REFERENCES nguoi_dung(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Bảng Thông báo
CREATE TABLE IF NOT EXISTS thong_bao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tieu_de VARCHAR(200) NOT NULL,
    noi_dung TEXT NOT NULL,
    loai ENUM('doi_phong', 'doi_lich', 'huy_lich', 'bao_tri') DEFAULT 'doi_lich',
    nguoi_tao_id INT NOT NULL,
    da_doc BOOLEAN DEFAULT 0,
    ngay_tao DATETIME NOT NULL,
    FOREIGN KEY (nguoi_tao_id) REFERENCES nguoi_dung(id) ON DELETE CASCADE
) ENGINE=InnoDB;
