# Quy Trình Quản Lý Git Cho Nhóm 3 Người (Team Git Workflow)
> **Dự án:** AI Smart Soil System (nongthinh.vn)  
> **Mô hình:** 3 Nhánh Cá Nhân Cố Định (Fixed Member Workspaces)  
> **Thành viên:** An (Team Lead / Reviewer), Trí (Developer), Khiêm (Developer)

---

## 1. Sơ Đồ 4 Nhánh Cố Định Của Toàn Bộ Dự Án

Dự án chỉ duy trì **đúng 4 nhánh cố định** trên GitHub, không sinh thêm nhánh con và không xóa nhánh:

| Nhánh | Chủ sở hữu | Quyền hạn & Mục đích |
| :--- | :--- | :--- |
| **`main`** | **Cả nhóm (An bảo vệ)** | • Nhánh chính thức (Production).<br/>• Kết nối trực tiếp với VPS `221.121.4.208` và chạy demo.<br/>• **Chỉ có An mới có quyền duyệt và gộp (Merge) code vào nhánh này.** |
| **`dev-an`** | **An** | Không gian làm việc riêng của An (Backend, Database, Hạ tầng VPS). |
| **`dev-tri`** | **Trí** | Không gian làm việc riêng của Trí (Firmware ESP32, Cảm biến RS485). |
| **`dev-khiem`** | **Khiêm** | Không gian làm việc riêng của Khiêm (Giao diện Mobile App / Web Flutter). |

---

## 2. Phân Chia Phạm Vi Làm Việc (Tránh Xung Đột Code 100%)

Vì mỗi thành viên phụ trách một thư mục độc lập trong dự án, nhóm sẽ **không bao giờ bị lỗi xung đột (conflict)** khi merge vào `main`:

```text
AI-Smart-Soil-System/
├── firmware-esp32/   ---> 🔧 TRÍ quản lý & lập trình
├── mobile-app/       ---> 📱 KHIÊM quản lý & lập trình
├── backend/          ---> ⚙️ AN quản lý & triển khai VPS
└── README.md
```

---

## 3. Hướng Dẫn Chi Tiết Cho TRÍ (hoặc KHIÊM)

### Bước 1: Khi mới tải dự án về máy (Làm 1 lần đầu)
```bash
# Clone dự án về máy
git clone https://github.com/Anneiry09/AI-Smart-Soil-System.git
cd AI-Smart-Soil-System

# Chuyển sang không gian làm việc riêng của mình
git checkout dev-tri     # (Đối với Khiêm thì gõ: git checkout dev-khiem)
```

### Bước 2: Hàng ngày làm việc & Đẩy code lên nhánh riêng
Trí/Khiêm chỉ cần làm việc bình thường trong thư mục của mình. Cuối ngày hoặc khi code xong thì đẩy lên nhánh cá nhân:
```bash
git add .
git commit -m "feat(firmware): noi dung da lam"
git push origin dev-tri  # (Đối với Khiêm: git push origin dev-khiem)
```

### Bước 3: Khi hoàn thành một tính năng $\rightarrow$ Báo An review
1. Lên trình duyệt vào: [https://github.com/Anneiry09/AI-Smart-Soil-System/pulls](https://github.com/Anneiry09/AI-Smart-Soil-System/pulls)
2. Bấm nút **New pull request**:
   * Nhánh đích (**base**): chọn **`main`**
   * Nhánh nguồn (**compare**): chọn **`dev-tri`** *(hoặc `dev-khiem`)*
3. Bấm **Create pull request**, điền tóm tắt công việc đã làm và báo cho An qua Zalo/Facebook: *"An ơi, mình xong phần này rồi, vào review giúp mình nhé!"*

### Bước 4: Sau khi An đã duyệt và gộp vào `main`
Để kéo những tính năng mới nhất mà cả nhóm đã làm về lại máy của mình:
```bash
# Đang đứng ở nhánh của mình, chỉ cần gõ 1 lệnh duy nhất:
git pull origin main
```
*(Xong bước này, Trí/Khiêm lại tiếp tục code bình thường trên nhánh của mình mà không cần tạo nhánh mới nào cả!)*

---

## 4. Hướng Dẫn Chi Tiết Cho AN (Team Lead / Reviewer)

Khi Trí hoặc Khiêm gửi Pull Request:

1. **Vào kiểm tra:** Vào tab **Pull requests** trên GitHub của dự án.
2. **Review Code:** Bấm vào PR đó $\rightarrow$ Chuyển sang tab **Files changed**:
   * Xem Trí/Khiêm đã sửa những file nào (màu xanh là code thêm mới, màu đỏ là xóa).
   * Đảm bảo không có commit nhầm mật khẩu nhạy cảm hoặc sửa nhầm file ngoài phạm vi.
3. **Gộp vào `main` (Merge):**
   * Khi code đạt chuẩn: Bấm nút **Merge pull request** (hoặc chọn mũi tên xổ xuống chọn **Squash and merge**).
   * Bấm **Confirm merge**.
4. **Lưu ý quan trọng:** Không bấm nút *"Delete branch"* sau khi merge, vì nhánh `dev-tri` và `dev-khiem` là nhánh cố định để các bạn tiếp tục làm việc!

---

## 5. Cài Đặt Khóa Bảo Vệ Nhánh `main` Trên GitHub (Làm 1 lần)

Để tránh việc thành viên gõ nhầm lệnh đè code lên nhánh chính `main`, An hãy cài đặt khóa bảo vệ:

1. Vào repo trên web GitHub: [Settings](https://github.com/Anneiry09/AI-Smart-Soil-System/settings)
2. Chọn mục **Branches** ở menu bên trái.
3. Bấm **Add branch protection rule**:
   * **Branch name pattern:** gõ chữ `main`
   * Tích chọn ô: **Require a pull request before merging**
   * Tích chọn ô: **Require approvals** (chọn số lượng là `1` - chỉ cần An duyệt là được).
4. Kéo xuống cuối trang bấm **Create** (hoặc Save changes).
