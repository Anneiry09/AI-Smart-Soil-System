# Quy Trình Quản Lý Git & Tiêu Chuẩn Commit Chuẩn
> **Dự án:** AI Smart Soil System (nongthinh.vn)  
> **Mục tiêu:** Giữ lịch sử Git sạch (clean history), dễ truy vết, chuyên nghiệp, bảo mật và cộng tác hiệu quả giữa 3 thành viên: **An (Lead)**, **Trí (Firmware)**, **Khiêm (Mobile)**.

---

## 1. Triết Lý Quản Lý Git (Git Philosophy)
* **Nguyên tử (Atomic Commits):** Mỗi commit chỉ làm đúng một việc rõ ràng, hoàn chỉnh và có thể kiểm chứng được.
* **Lịch sử tuyến tính & rõ ràng (Clean History):** Tránh các commit rác như "fix", "update", "test 123", tránh merge commit chằng chịt không kiểm soát.
* **Bảo mật tuyệt đối:** Tuyệt đối không commit token bí mật, mật khẩu Wi-Fi thật, API key riêng tư, hoặc file cấu hình nhạy cảm (`.env`, `config.h` chứa thông tin thực tế) lên repository công khai.

---

## 2. Quy Ước Đặt Tên Commit (Conventional Commits)

Toàn bộ thành viên (An, Trí, Khiêm) đều phải tuân thủ chuẩn **Conventional Commits** kèm **Scope** tương ứng với module mình phụ trách.

### Cú pháp:
```text
<type>(<scope>): <mô tả ngắn gọn bằng tiếng Anh hoặc tiếng Việt rõ nghĩa>

[Mô tả chi tiết nếu cần]
```

### Các Type (Loại commit) hợp lệ:
| Type | Ý nghĩa & Khi nào dùng |
| :--- | :--- |
| `feat` | Thêm tính năng mới (Feature) |
| `fix` | Sửa lỗi chương trình (Bug fix) |
| `docs` | Thêm hoặc cập nhật tài liệu (`README.md`, `GIT_WORKFLOW.md`, `docs/`) |
| `refactor` | Tối ưu hóa, sắp xếp lại mã nguồn (không đổi logic hay tính năng) |
| `chore` | Cập nhật cấu hình build, dependency, thư viện, `.gitignore` |
| `test` | Viết hoặc cập nhật unit test, widget test |

### Các Scope (Phạm vi) trong dự án:
| Scope | Thư mục & Module tương ứng | Phụ trách chính |
| :--- | :--- | :--- |
| `firmware` | Mã nguồn ESP32 PlatformIO (`firmware-esp32/`) | **Trí** |
| `mobile` | Ứng dụng Flutter di động & web (`mobile-app/`) | **Khiêm** |
| `backend` | Server FastAPI, SQLite WAL, Telemetry APIs (`backend/`) | **An** |
| `ai` | Module đánh giá độ phì, thuật toán khuyến nghị dinh dưỡng | **An** |
| `config` | Cấu hình dự án, PlatformIO environment, gitignore | Cả nhóm |
| `docs` | Tài liệu hướng dẫn, sơ đồ mạch, sơ đồ luồng dữ liệu | Cả nhóm |

### Ví dụ Commit Chuẩn:
* **Firmware (Trí):**
  * `feat(firmware): add median filter algorithm for 7-in-1 soil sensor`
  * `fix(firmware): resolve rs485 modbus timeout on esp32 doit devkit v1`
  * `chore(firmware): update platformio library dependencies`
* **Mobile (Khiêm):**
  * `feat(mobile): build real-time soil telemetry dashboard screen`
  * `fix(mobile): handle null values when sensor is offline`
  * `refactor(mobile): optimize color-coded alert widgets for soil metrics`
* **Backend & AI (An):**
  * `feat(backend): add telemetry ingestion and latest status api endpoints`
  * `feat(ai): integrate npk fertility rating and npk deficiency warnings`
  * `docs(workflow): supplement 3-member git workflow and conventional commit rules`

---

## 3. Mô Hình 4 Nhánh Cố Định Cho Nhóm 3 Người

Để tránh việc phải tạo và xóa nhánh liên tục gây rối rắm, dự án áp dụng mô hình **Nhánh Không Gian Riêng (Personal Fixed Workspaces)**:

```text
       (Khiêm code mobile-app/)
       dev-khiem ──●──────●──────● ───┐ (Pull Request)
                                      │
  main ───────────────────────────────▼───● (An Review & Merge) ──● (Deploy VPS)
                                      ▲
       dev-tri   ──●──────●──────● ───┘ (Pull Request)
       (Trí code firmware-esp32/)
```

| Nhánh | Chủ sở hữu | Quyền hạn & Mục đích |
| :--- | :--- | :--- |
| **`main`** | **Cả nhóm (An bảo vệ)** | • Nhánh chính thức (Production).<br/>• Kết nối trực tiếp với VPS `221.121.4.208` và chạy demo hội đồng/thầy cô.<br/>• **Chỉ có An mới có quyền duyệt và gộp (Merge) code vào nhánh này.** |
| **`dev-an`** | **An** | Không gian làm việc riêng của An (Backend, Database, Hạ tầng VPS, AI). |
| **`dev-tri`** | **Trí** | Không gian làm việc riêng của Trí (Firmware ESP32, Cảm biến RS485). |
| **`dev-khiem`** | **Khiêm** | Không gian làm việc riêng của Khiêm (Giao diện Mobile App / Web Flutter). |

### Phân chia thư mục độc lập (Tránh xung đột code 100%):
```text
AI-Smart-Soil-System/
├── firmware-esp32/   ---> 🔧 TRÍ quản lý & lập trình
├── mobile-app/       ---> 📱 KHIÊM quản lý & lập trình
├── backend/          ---> ⚙️ AN quản lý & triển khai VPS
├── README.md         ---> 📖 Dùng chung
└── GIT_WORKFLOW.md   ---> 📖 Dùng chung
```

*(Tùy chọn mở rộng: Nếu sau này dự án có tính năng lớn cần thử nghiệm tách biệt hoàn toàn, thành viên có thể tạo nhánh phụ `feat/<tên-tính-năng>` từ nhánh của mình, sau khi xong thì gộp lại nhánh `dev-*` trước khi tạo PR vào `main`).*

---

## 4. Hướng Dẫn Quy Trình Cho TRÍ & KHIÊM

### Bước 1: Lấy dự án về máy (Chỉ làm 1 lần đầu)
```bash
# Clone dự án về máy
git clone https://github.com/Anneiry09/AI-Smart-Soil-System.git
cd AI-Smart-Soil-System

# Chuyển sang không gian làm việc riêng của mình
git checkout dev-tri     # (Đối với Khiêm thì gõ: git checkout dev-khiem)
```

### Bước 2: Hàng ngày làm việc & Đẩy code lên nhánh riêng
Trí/Khiêm chỉ cần làm việc bình thường trong thư mục của mình (`firmware-esp32/` hoặc `mobile-app/`). Khi code xong một phần việc thì commit và đẩy lên nhánh cá nhân:
```bash
# Kiểm tra file đã sửa
git status

# Thêm file thay đổi
git add .

# Commit theo chuẩn Conventional Commit
git commit -m "feat(firmware): implement auto reconnect wifi for esp32"
# hoặc: git commit -m "feat(mobile): display npk chart on dashboard"

# Đẩy lên GitHub nhánh của mình
git push origin dev-tri  # (Đối với Khiêm: git push origin dev-khiem)
```

### Bước 3: Khi hoàn thành một mốc/tính năng $\rightarrow$ Báo An Review
1. Truy cập vào: [https://github.com/Anneiry09/AI-Smart-Soil-System/pulls](https://github.com/Anneiry09/AI-Smart-Soil-System/pulls)
2. Bấm nút **New pull request**:
   * Nhánh đích (**base**): chọn **`main`**
   * Nhánh nguồn (**compare**): chọn **`dev-tri`** *(hoặc `dev-khiem`)*
3. Bấm **Create pull request**, ghi tóm tắt những nội dung đã làm và báo cho An qua Zalo/Facebook:  
   *"An ơi, mình hoàn thành phần đọc cảm biến rồi, vào review và merge giúp mình nhé!"*

### Bước 4: Sau khi An đã duyệt và gộp vào `main`
Để kéo những tính năng mới nhất mà cả nhóm đã làm về lại máy của mình:
```bash
# Đang đứng ở nhánh riêng (dev-tri hoặc dev-khiem), chỉ cần gõ 1 lệnh:
git pull origin main
```
*(Xong bước này, Trí/Khiêm lại tiếp tục code bình thường trên nhánh của mình mà không cần tạo nhánh mới nào cả!)*

---

## 5. Hướng Dẫn Quy Trình Cho AN (Team Lead / Reviewer)

Khi Trí hoặc Khiêm gửi Pull Request về `main`:

1. **Vào kiểm tra:** Truy cập tab **Pull requests** trên GitHub của dự án.
2. **Review Code (Soát lỗi):** Bấm vào PR đó $\rightarrow$ Chuyển sang tab **Files changed**:
   * Xem Trí/Khiêm đã sửa những file nào (màu xanh là thêm mới, màu đỏ là xóa).
   * Đảm bảo không có commit nhầm mật khẩu nhạy cảm, API key bí mật, hoặc sửa nhầm file ngoài thư mục phụ trách.
   * Đảm bảo thông điệp commit tuân thủ định dạng Conventional Commits.
3. **Gộp vào `main` (Merge):**
   * Khi code đạt chuẩn: Bấm nút **Merge pull request** (hoặc chọn mũi tên xổ xuống chọn **Squash and merge** để gộp các commit nhỏ thành 1 commit gọn gàng).
   * Bấm **Confirm merge**.
4. **Lưu ý cực kỳ quan trọng:** **KHÔNG bấm nút *"Delete branch"*** sau khi merge, vì `dev-tri` và `dev-khiem` là nhánh làm việc cố định lâu dài của các bạn!

---

## 6. Cài Đặt Khóa Bảo Vệ Nhánh `main` Trên GitHub (Làm 1 lần)

Để tránh trường hợp thành viên lỡ gõ nhầm lệnh đẩy trực tiếp đè lên nhánh chính `main`, An cài đặt bảo vệ:

1. Vào repo trên web GitHub: [Settings](https://github.com/Anneiry09/AI-Smart-Soil-System/settings)
2. Chọn mục **Branches** ở cột bên trái.
3. Bấm **Add branch protection rule**:
   * **Branch name pattern:** gõ chữ `main`
   * Tích chọn ô: **Require a pull request before merging**
   * Tích chọn ô: **Require approvals** (chọn số lượng là `1` - chỉ cần An duyệt là được).
4. Kéo xuống cuối trang bấm **Create** (hoặc Save changes).

---

## 7. Danh Sách Kiểm Tra "Clean Git" Trước Khi Push (Pre-push Checklist)

Trước khi gõ `git push`, mỗi thành viên hãy tự kiểm tra 4 điều sau:
- [ ] **Không có file rác:** Không commit các thư mục build tạm thời (`.pio/`, `__pycache__/`, `.dart_tool/`, `build/`, `.vscode/`).
- [ ] **Không có thông tin nhạy cảm:** Không để mật khẩu Wi-Fi thực tế, token, credential trong code đẩy lên remote.
- [ ] **Code kiểm tra chạy tốt:**
  - Firmware: `pio run` build thành công không lỗi.
  - Backend: Chạy thử local hoặc test API thành công.
  - Mobile: `flutter analyze` không có lỗi đỏ (error).
- [ ] **Commit message chuẩn:** Tuân thủ đúng định dạng `<type>(<scope>): <mô tả ngắn>`.
