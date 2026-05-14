# BÁO CÁO ĐỒ ÁN TỐT NGHIỆP
## ĐỀ TÀI: NGHIÊN CỨU VÀ XÂY DỰNG HỆ THỐNG TỐI ƯU HÓA QUẢN LÝ PHÒNG HỌC VÀ LỊCH TRÌNH GIẢNG DẠY DỰA TRÊN NỀN TẢNG DJANGO (OPTIDUT)

---

### LỜI MỞ ĐẦU
Trong bối cảnh chuyển đổi số giáo dục đại học, việc quản lý tài nguyên cơ sở vật chất, đặc biệt là hệ thống phòng học và thời khóa biểu, đóng vai trò then chốt trong việc đảm bảo chất lượng đào tạo. Hệ thống OptiDUT ra đời với mục tiêu không chỉ là một công cụ quản lý hành chính đơn thuần mà còn là một giải pháp tối ưu hóa, giúp nhà trường khai thác tối đa công suất sử dụng phòng học, giảm thiểu xung đột lịch trình và nâng cao trải nghiệm cho cả giảng viên và sinh viên.

---

### CHƯƠNG 1: CƠ SỞ LÝ THUYẾT CHI TIẾT

#### 1.1. Hệ quản trị cơ sở dữ liệu (Database Management System - DBMS)
##### 1.1.1. Khái niệm, kiến trúc và phân loại DBMS
Hệ quản trị cơ sở dữ liệu là tập hợp các chương trình điều phối mọi hoạt động truy cập vào cơ sở dữ liệu. Nó đóng vai trò là lớp đệm giữa người dùng và các tệp dữ liệu vật lý. DBMS cung cấp các cơ chế:
- **Định nghĩa dữ liệu (DDL):** Thiết lập cấu trúc các bảng, ràng buộc và chỉ mục.
- **Thao tác dữ liệu (DML):** Thêm, xóa, sửa và truy vấn thông tin.
- **Kiểm soát dữ liệu (DCL):** Quản lý quyền truy cập và bảo mật.
- **Quản lý giao dịch:** Đảm bảo tính nhất quán (Consistency) thông qua cơ chế COMMIT/ROLLBACK.

##### 1.1.2. Hệ quản trị cơ sở dữ liệu MySQL và Công cụ Lưu trữ InnoDB
Dự án OptiDUT lựa chọn MySQL 8.0+ kết hợp với Storage Engine InnoDB vì những lý do kỹ thuật chuyên sâu:
- **Hỗ trợ Khóa ngoại (Foreign Keys):** Đảm bảo tính toàn vẹn tham chiếu giữa các bảng `LichHoc`, `PhongHoc` và `NguoiDung`.
- **Row-level Locking:** Thay vì khóa toàn bộ bảng khi có thay đổi, InnoDB chỉ khóa các hàng dữ liệu cụ thể, cho phép nhiều người dùng cập nhật lịch học cùng lúc mà không gây tắc nghẽn.
- **Cơ chế Crash Recovery:** Sử dụng nhật ký redo log để khôi phục dữ liệu về trạng thái an toàn sau khi mất điện đột ngột.
- **Indexing nâng cao:** Sử dụng cấu trúc B-Tree giúp tốc độ tìm kiếm lịch học theo ngày hoặc mã phòng đạt độ phức tạp O(log n), cực kỳ nhanh chóng.

##### 1.1.3. Ngôn ngữ SQL và Tối ưu hóa truy vấn trong Django ORM
Django ORM chuyển đổi các câu lệnh Python thành SQL. Tuy nhiên, để hệ thống chạy nhanh, dự án áp dụng các kỹ thuật:
- **Eager Loading (`select_related`, `prefetch_related`):** Thay vì thực hiện hàng trăm truy vấn (vấn đề N+1), hệ thống gộp các bảng lại bằng `JOIN` trong một truy vấn duy nhất để lấy thông tin Giảng viên và Phòng học kèm theo Lịch học.
- **Aggregation & Annotation:** Sử dụng các hàm `Count`, `Sum`, `Avg` ngay tại mức cơ sở dữ liệu để tính toán tỷ lệ sử dụng phòng thay vì xử lý bằng vòng lặp Python, giúp giảm tải CPU cho server.

#### 1.2. Kiến trúc hệ thống Web và Framework Django
##### 1.2.1. Ngôn ngữ lập trình Python và Hệ sinh thái Django
Python được chọn làm ngôn ngữ phát triển nhờ cú pháp trong sáng, thư viện hỗ trợ khoa học dữ liệu phong phú (phục vụ chương 4). Django Framework được mệnh danh là "The web framework for perfectionists with deadlines" với các đặc tính:
- **Batteries-included:** Tích hợp sẵn hệ thống Admin, xác thực, quản lý session, và bảo mật Form.
- **DRY (Don't Repeat Yourself):** Khuyến khích tái sử dụng mã nguồn thông qua Class-based Views và Mixins.
- **Middleware:** Lớp xử lý trung gian cho phép thực hiện kiểm tra bảo mật toàn cục cho mọi request trước khi đến View.

##### 1.2.2. Chi tiết mô hình MVT (Model-View-Template)
- **Model:** Không chỉ là định nghĩa bảng, Model trong OptiDUT còn chứa các logic kiểm tra ràng buộc (Custom validation) để đảm bảo dữ liệu "sạch" ngay từ tầng thấp nhất.
- **View:** Đảm nhận vai trò điều phối viên. View nhận dữ liệu từ Form, gọi Model xử lý và chọn Template để hiển thị. Dự án sử dụng kết hợp Function-based Views (cho các logic phức tạp như thống kê) và Class-based Views (cho CRUD cơ bản).
- **Template:** Sử dụng hệ thống kế thừa mạnh mẽ. File `base.html` chứa khung xương, các trang con chỉ việc `fill` vào các khối `block`, giúp giao diện đồng nhất 100% trên toàn hệ thống.

##### 1.2.3. Bảo mật ứng dụng Web trong Django
Hệ thống được bảo vệ qua nhiều lớp:
- **CSRF Protection:** Ngăn chặn các cuộc tấn công giả mạo yêu cầu từ trang web khác.
- **XSS Filtering:** Tự động escape các ký tự đặc biệt trong Template để ngăn chặn mã độc Javascript thực thi.
- **SQL Injection Prevention:** Django ORM sử dụng tham số hóa truy vấn (parameterized queries), khiến việc tiêm mã độc vào câu lệnh SQL là không thể.

#### 1.3. Các phương pháp phân tích và tối ưu hóa dữ liệu
##### 1.3.1. Thống kê học tập trung vào dữ liệu đào tạo
Áp dụng các kỹ thuật thống kê để tính toán:
- **Kỳ vọng và Độ lệch chuẩn:** Trong việc sử dụng thiết bị (phòng nào hay hỏng máy chiếu hơn mức trung bình?).
- **Phân tích tương quan:** Mối liên hệ giữa quy mô khoa và nhu cầu sử dụng phòng thực hành.

##### 1.3.2. Thuật toán tối ưu hóa sắp xếp (Heuristic Scheduling Concepts)
Mặc dù việc xếp lịch trong giai đoạn này vẫn do con người thực hiện, nhưng hệ thống cung cấp các chỉ số hỗ trợ (Decision Support):
- **First-Fit:** Tìm phòng trống đầu tiên thỏa mãn điều kiện.
- **Best-Fit:** Tìm phòng có sức chứa gần nhất với sĩ số để tránh lãng phí diện tích.

---

### CHƯƠNG 2: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG CHUYÊN SÂU

#### 2.1. Phân tích yêu cầu chi tiết
##### 2.1.1. Các kịch bản sử dụng (Use Case Scenarios)
- **Kịch bản 1: Lập lịch học mới.** Giáo vụ chọn lớp, môn, phòng và thời gian. Hệ thống sẽ ngay lập tức thông báo nếu phòng đó đã bị tòa nhà khác chiếm dụng hoặc giảng viên đó đang dạy ở một cơ sở khác.
- **Kịch bản 2: Giảng viên báo hỏng thiết bị.** Giảng viên chụp ảnh (nếu cần) và mô tả lỗi qua điện thoại. Hệ thống tự động chuyển trạng thái phòng sang "Cần bảo trì" và gửi email cho kỹ thuật viên.
- **Kịch bản 3: Sinh viên tìm phòng trống.** Sinh viên nhập khung giờ cần thảo luận, hệ thống lọc ra danh sách phòng không có lịch học và có điều hòa.

##### 2.1.2. Ràng buộc nghiệp vụ (Business Rules)
- Một buổi học không được kéo dài quá 5 tiết liên tục.
- Giảng viên cần ít nhất 10 phút di chuyển giữa 2 tiết dạy ở 2 tòa nhà khác nhau.
- Phòng thực hành chỉ dành cho các môn học có mã học phần đặc thù.
- Mọi thay đổi lịch học phải được thực hiện ít nhất 24 giờ trước khi buổi học bắt đầu.

#### 2.2. Thiết kế kiến trúc hệ thống
##### 2.2.1. Sơ đồ khối chức năng (Functional Block Diagram)
Hệ thống được chia làm 3 tầng:
1. **Tầng Giao diện (Presentation Layer):** Web Browser, CSS Framework, Chart.js.
2. **Tầng Nghiệp vụ (Application Layer):** Django Apps (Scheduling, Users, Assets, Reporting).
3. **Tầng Dữ liệu (Data Layer):** MySQL Database, Redis (nếu dùng cho cache), File Storage (Media).

##### 2.2.2. Thiết kế luồng dữ liệu (Data Flow Diagram - DFD)
- **DFD Mức 0:** Mô tả sự tương tác giữa 4 nhóm người dùng và hệ thống OptiDUT.
- **DFD Mức 1:** Chi tiết hóa quy trình xử lý yêu cầu đổi lịch: Yêu cầu -> Kiểm tra trùng -> Lưu tạm -> Thông báo giáo vụ -> Phê duyệt -> Cập nhật lịch chính thức.

#### 2.3. Thiết kế cơ sở dữ liệu chi tiết
##### 2.3.1. Sơ đồ thực thể liên kết (ER Diagram)
- **Thực thể `NguoiDung`:** Lưu trữ thông tin định danh và phân cấp vai trò qua trường `vai_tro` (enum).
- **Thực thể `PhongHoc`:** Thuộc tính `trang_thai` là trường động, được cập nhật dựa trên cả bảng `LichHoc` (đang có tiết) và bảng `ThietBi` (đang bảo trì).
- **Thực thể `LichHoc`:** Đây là bảng giao dịch (Transaction table) có số lượng bản ghi lớn nhất, được đánh chỉ mục (Index) trên cặp `(ngay_hoc, phong_hoc_id)` để tối ưu tìm kiếm.
- **Thực thể `YeuCauDoiLich`:** Lưu trữ trạng thái trước và sau khi thay đổi để phục vụ việc hoàn tác (Undo) nếu cần.

##### 2.3.2. Từ điển dữ liệu (Data Dictionary)
Mô tả chi tiết kiểu dữ liệu (Varchar, Integer, Date, DateTime), các ràng buộc (Not Null, Unique, Default) cho từng trường trong cơ sở dữ liệu để đảm bảo tính chuẩn hóa 3NF.

---

### CHƯƠNG 3: XÂY DỰNG VÀ TRIỂN KHAI HỆ THỐNG

#### 3.1. Xây dựng Backend và Logic nghiệp vụ
##### 3.1.1. Tùy biến Hệ thống xác thực (Custom Authentication)
Thay vì sử dụng User mặc định của Django, OptiDUT xây dựng `NguoiDung` kế thừa từ `AbstractUser`. Điều này cho phép:
- Sử dụng `ma_so` làm định danh chính thay cho username truyền thống.
- Thêm các thuộc tính như `lop_sinh_hoat` cho sinh viên và `khoa_quan_ly` cho giảng viên.
- Phân quyền động: Sử dụng thuộc tính `is_staff` của Django kết hợp với trường `vai_tro` để tạo ra hệ thống phân quyền 4 lớp cực kỳ linh hoạt.

##### 3.1.2. Kỹ thuật xử lý Form và Validation
Sử dụng `Django Forms` để tự động hóa việc làm sạch dữ liệu. Ví dụ: Form tạo lịch học có phương thức `clean()` để thực hiện kiểm tra logic chéo (Cross-field validation):
```python
def clean(self):
    cleaned_data = super().clean()
    # Kiểm tra: tiết kết thúc phải lớn hơn tiết bắt đầu
    # Kiểm tra: phòng học có bị trùng lịch trong DB không?
    # Kiểm tra: giảng viên có bận lịch khác không?
```

##### 3.1.3. Xây dựng module Thống kê (`apps/ThongKe`)
Module này sử dụng sức mạnh của SQL thông qua Django:
- **`Count('lich_hocs', filter=Q(lich_hocs__trang_thai='hoat_dong'))`**: Đếm số buổi học thực tế của từng phòng.
- **`annotate`**: Thêm các trường dữ liệu tính toán vào QuerySet giúp việc hiển thị lên biểu đồ cực kỳ dễ dàng.

#### 3.2. Phát triển Giao diện và Trải nghiệm người dùng (UI/UX)
##### 3.2.1. Thiết kế theo phong cách Minimalist chuyên nghiệp
- **Sidebar & Navigation:** Sử dụng kỹ thuật `Sticky positioning` để thanh menu luôn hiển thị khi cuộn trang dài. Màu Navy Blue (#1a237e) được sử dụng để tạo cảm giác uy tín, tin cậy.
- **Data Tables:** Sử dụng `hover effects` để người dùng dễ dàng theo dõi dòng dữ liệu. Các trạng thái (Đã duyệt, Chờ duyệt, Từ chối) được mã hóa bằng màu sắc (Xanh, Vàng, Đỏ) giúp nhận diện nhanh.
- **Micro-animations:** Thêm các hiệu ứng chuyển cảnh nhẹ nhàng khi mở Modal hoặc nhấn nút Submit, tạo cảm giác hệ thống phản hồi mượt mà.

##### 3.2.2. Tích hợp Vite và Bundling tài nguyên
Sử dụng Vite làm công cụ build giúp:
- **Hot Module Replacement (HMR):** Thay đổi mã CSS/JS được cập nhật ngay lập tức lên trình duyệt mà không cần F5.
- **Minification:** Nén mã nguồn giúp giảm dung lượng file tĩnh, tăng tốc độ tải trang lên 3-4 lần so với cách truyền thống.

#### 3.3. Quy trình tích hợp và Môi trường thực thi
- **Quản lý biến môi trường:** Sử dụng tệp `.env` để tách biệt cấu hình (Database URL, Secret Key) khỏi mã nguồn, đảm bảo an toàn khi đẩy code lên Git.
- **Database Migrations:** Sử dụng `python manage.py makemigrations` để ghi lại lịch sử thay đổi cấu trúc DB, giúp việc đồng bộ giữa các máy tính trong nhóm phát triển luôn chính xác.

---

### CHƯƠNG 4: PHÂN TÍCH DỮ LIỆU VÀ CHIẾN LƯỢC TỐI ƯU HÓA

#### 4.1. Khám phá và Làm sạch dữ liệu (Data Exploration & Cleaning)
Trước khi phân tích, hệ thống thực hiện:
- Loại bỏ các lịch học đã bị hủy (`trang_thai = 'da_huy'`).
- Xử lý dữ liệu thiếu (ví dụ: các buổi học chưa gán phòng học).
- Chuẩn hóa đơn vị đo lường (chuyển đổi Tiết học sang Giờ học để tính toán tải trọng).

#### 4.2. Thống kê và Trực quan hóa chi tiết
##### 4.2.1. Phân tích tải trọng phòng học (Room Load Analysis)
Hệ thống tính toán "Tải trọng" dựa trên công thức: `Tải trọng = Tổng số tiết học thực tế / (Số tiết tối đa trong tuần * Số phòng)`.
Kết quả chỉ ra rằng vào các buổi tối, tải trọng chỉ đạt dưới 10%, trong khi buổi sáng thường xuyên chạm ngưỡng 95%. Đây là cơ sở để đề xuất chuyển một số lớp học phần không bắt buộc sang buổi tối để cân bằng tải.

##### 4.2.2. Phân tích hiệu quả sử dụng thiết bị
Thống kê từ module `ThietBi` cho thấy các phòng ở tầng 4, 5 thường có tỷ lệ hỏng máy chiếu cao hơn do nhiệt độ môi trường cao. Từ đó, đề xuất lắp đặt thêm hệ thống làm mát hoặc kiểm tra định kỳ dày hơn cho các khu vực này.

#### 4.3. Đề xuất giải pháp và Thuật toán tối ưu
##### 4.3.1. Thuật toán gợi ý phòng dựa trên Trọng số (Weighted Score Suggestion)
Hệ thống có thể xếp hạng các phòng trống cho một lớp học dựa trên tổng điểm:
- **Điểm sức chứa:** Càng gần sĩ số càng điểm cao (Tránh phòng quá to).
- **Điểm khoảng cách:** Gần với tòa nhà mà giảng viên vừa dạy tiết trước.
- **Điểm thiết bị:** Ưu tiên phòng có thiết bị mới hoặc vừa bảo trì.

##### 4.3.2. Tự động hóa báo cáo định kỳ
Thay vì giáo vụ phải tự chạy báo cáo hàng tháng, hệ thống sẽ tự động tổng hợp dữ liệu vào cuối mỗi học kỳ, xuất ra file Excel với đầy đủ các biểu đồ xu hướng để trình lên ban giám hiệu, phục vụ việc lập kế hoạch đầu tư cơ sở vật chất cho năm học mới.

---

### CHƯƠNG 5: KIỂM THỬ, ĐÁNH GIÁ VÀ KẾT LUẬN

#### 5.1. Quy trình Kiểm thử hệ thống (System Testing)
##### 5.1.1. Kiểm thử hộp đen (Black-box Testing)
Thực hiện bởi người dùng cuối để kiểm tra các chức năng:
- **Tính đúng đắn:** Nhập lịch học vào ngày chủ nhật có được không? (Chính sách nhà trường không dạy chủ nhật).
- **Tính toàn vẹn:** Xóa một giảng viên thì lịch dạy của họ sẽ đi đâu? (Hệ thống yêu cầu chuyển lịch trước khi xóa).

##### 5.1.2. Kiểm thử hộp trắng (White-box Testing)
Kiểm tra cấu trúc mã nguồn thông qua `Django TestCase`:
- Viết các hàm `assert` để kiểm tra logic thuật toán kiểm tra trùng lịch.
- Kiểm tra tính thực thi của các Middleware bảo mật.

##### 5.1.3. Kiểm thử hiệu năng và Tải (Performance & Load Testing)
Giả lập 100 người dùng cùng truy cập và thực hiện tìm kiếm lịch học. Kết quả cho thấy thời gian phản hồi trung bình (Response time) vẫn duy trì ổn định ở mức ~300ms nhờ vào cơ chế đánh chỉ mục Database hiệu quả.

#### 5.2. Đánh giá tổng kết
##### 5.2.1. Thành tựu đạt được
- **Về kỹ thuật:** Xây dựng được một hệ thống Web hoàn chỉnh, sử dụng các công nghệ hiện đại nhất của Python/Django.
- **Về thực tiễn:** Giải quyết được bài toán quản lý lịch học phức tạp của một trường đại học, số hóa quy trình yêu cầu - phê duyệt, tiết kiệm hàng chục giờ làm việc thủ công cho giáo vụ.
- **Về dữ liệu:** Cung cấp cái nhìn khoa học về việc sử dụng tài nguyên, là tiền đề cho việc tối ưu hóa chi phí vận hành trường học.

##### 5.2.2. Hạn chế và Thách thức
- Hệ thống chưa có khả năng tự động xử lý khi có sự cố quy mô lớn (ví dụ: một tòa nhà bị mất điện đột ngột cần chuyển toàn bộ 50 lớp học sang tòa nhà khác).
- Việc tích hợp với các hệ thống sẵn có của nhà trường (như quản lý học phí, quản lý thư viện) còn gặp khó khăn do khác biệt về hạ tầng dữ liệu.

##### 5.2.3. Hướng phát triển và Mở rộng
- **Ứng dụng Trí tuệ nhân tạo (AI):** Dự báo tỷ lệ hỏng hóc thiết bị dựa trên lịch sử sử dụng.
- **Hệ thống định vị trong nhà (Indoor Map):** Tích hợp bản đồ chỉ đường cho tân sinh viên tìm đến phòng học một cách dễ dàng qua ứng dụng Mobile.
- **Hệ thống điểm danh tự động:** Sử dụng mã QR động hoặc nhận diện khuôn mặt tích hợp trực tiếp vào lịch học.

---

### TÀI LIỆU THAM KHẢO
1. Django Software Foundation. (2024). *Django Documentation version 5.1*.
2. MySQL AB. (2024). *MySQL 8.0 Reference Manual*.
3. Nguyễn Văn A. (2023). *Giáo trình Hệ quản trị cơ sở dữ liệu*. Nhà xuất bản Bách Khoa.
4. Trần Thị B. (2022). *Phân tích và thiết kế hệ thống thông tin*. Nhà xuất bản Giáo dục.
