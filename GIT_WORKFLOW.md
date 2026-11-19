# Quy Trình Quản Lý Git & Tiêu Chuẩn Commit Cho Nhóm
> **Dự án:** AI Smart Soil System  
> **Điều phối & Quản lý:** Do Team Lead (An) trực tiếp phân công công việc linh hoạt cho từng thành viên theo từng giai đoạn.  
> **Mô hình Git:** Không gian làm việc cá nhân riêng biệt (Personal Workspaces) kết hợp Đánh giá mã nguồn (Pull Request Review) trước khi gộp vào `main`.

---

## 1. Triết Lý Quản Lý Git (Git Philosophy)
* **Nguyên tử (Atomic Commits):** Mỗi commit chỉ làm đúng một việc rõ ràng, hoàn chỉnh và có thể kiểm chứng được.
* **Lịch sử tuyến tính & rõ ràng (Clean History):** Tránh các commit rác như "fix", "update", "test 123", tránh merge commit chằng chịt không kiểm soát.
* **Bảo mật tuyệt đối:** Tuyệt đối không commit token bí mật, mật khẩu Wi-Fi thật, API key riêng tư, hoặc file cấu hình nhạy cảm (`.env`, `config.h` chứa thông tin thực tế) lên repository công khai.

---

## 2. Quy Ước Đặt Tên Commit (Conventional Commits)

Bất kỳ thành viên nào khi thực hiện công việc được giao đều phải tuân thủ chuẩn **Conventional Commits** kèm **Scope** tương ứng với phần việc mình đang làm.

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

### Các Scope (Phạm vi module) trong dự án:
*(Thành viên chọn scope tương ứng với thư mục mã nguồn mà mình đang code theo nhiệm vụ được giao)*

| Scope | Thư mục & Module tương ứng | Mục đích |
| :--- | :--- | :--- |
| `firmware` | Mã nguồn ESP32 PlatformIO (`firmware-esp32/`) | Lập trình phần cứng, đọc cảm biến, kết nối mạng |
| `mobile` | Ứng dụng Flutter di động & web (`mobile-app/`) | Giao diện người dùng, hiển thị biểu đồ, kết nối API |
| `backend` | Server FastAPI, SQLite WAL (`backend/`) | Xử lý dữ liệu cảm biến, lưu trữ cơ sở dữ liệu, API |
| `ai` | Module đánh giá độ phì, thuật toán khuyến nghị dinh dưỡng | Phân tích nông học, cảnh báo ngưỡng đất |
| `config` | Cấu hình dự án, PlatformIO environment, gitignore | Cài đặt môi trường chung của dự án |
| `docs` | Tài liệu hướng dẫn, sơ đồ mạch, sơ đồ luồng dữ liệu | Viết tài liệu báo cáo, giải thích hệ thống |

### Ví dụ Commit Chuẩn theo từng Module:
* **Khi làm việc với Firmware:**
  * `feat(firmware): add median filter algorithm for 7-in-1 soil sensor`
  * `fix(firmware): resolve rs485 modbus timeout on esp32 doit devkit v1`
  * `chore(firmware): update platformio library dependencies`
* **Khi làm việc với Mobile App:**
  * `feat(mobile): build real-time soil telemetry dashboard screen`
  * `fix(mobile): handle null values when sensor is offline`
  * `refactor(mobile): optimize color-coded alert widgets for soil metrics`
* **Khi làm việc với Backend & AI:**
  * `feat(backend): add telemetry ingestion and latest status api endpoints`
  * `feat(ai): integrate npk fertility rating and npk deficiency warnings`
* **Khi làm việc với Tài liệu & Cấu hình:**
  * `docs(workflow): supplement conventional commit standards and branch guide`
  * `chore(config): ignore temporary build and cache directories`

---

## 3. Mô Hình Phân Nhánh Cho Dự Án (Personal Workspaces)

Mỗi thành viên có **một không gian làm việc riêng (nhánh cá nhân)** để nhận và xử lý bất kỳ công việc nào do Team Lead phân công:

```text
       (Thành viên làm việc trên nhánh riêng)
       dev-khiem ──●──────●──────● ───┐ (Gửi Pull Request)
                                      │
  main ───────────────────────────────▼───● (An Review & Merge) ──● (Deploy VPS)
                                      ▲
       dev-tri   ──●──────●──────● ───┘ (Gửi Pull Request)
       (Thành viên làm việc trên nhánh riêng)
```

| Nhánh | Chủ sở hữu | Quyền hạn & Mục đích |
| :--- | :--- | :--- |
| **`main`** | **Cả nhóm (An bảo vệ)** | • Nhánh chính thức (Production).<br/>• Kết nối trực tiếp với VPS `221.121.4.208` và chạy demo hội đồng/thầy cô.<br/>• **Chỉ có An mới có quyền duyệt và gộp (Merge) code vào nhánh này.** |
| **`dev-an`** | **An** | Không gian làm việc riêng của An. |
| **`dev-tri`** | **Trí** | Không gian làm việc riêng của Trí. |
| **`dev-khiem`** | **Khiêm** | Không gian làm việc riêng của Khiêm. |

### Cấu trúc mã nguồn của dự án:
```text
AI-Smart-Soil-System/
├── firmware-esp32/   ---> Mã nguồn nhúng ESP32 & Cảm biến RS485 Modbus RTU
├── mobile-app/       ---> Ứng dụng di động (Android/iOS) & Dashboard Flutter
├── backend/          ---> API Server FastAPI, SQLite WAL, Telemetry & AI
├── README.md         ---> Tài liệu tổng quan dự án
└── GIT_WORKFLOW.md   ---> Quy chuẩn Git & Hướng dẫn phối hợp nhóm
```

---

## 4. Hướng Dẫn Quy Trình Cho Thành Viên (Developer)

### Bước 1: Lấy dự án về máy (Chỉ làm 1 lần đầu)
```bash
# Clone dự án về máy
git clone https://github.com/Anneiry09/AI-Smart-Soil-System.git
cd AI-Smart-Soil-System

# Chuyển sang không gian làm việc riêng của mình (ví dụ Trí: dev-tri, Khiêm: dev-khiem)
git checkout dev-tri
```

### Bước 2: Thực hiện công việc được giao & Đẩy code lên nhánh riêng
Thành viên làm các tác vụ theo phân công của Team Lead An. Khi hoàn thành một phần việc, commit và đẩy lên nhánh cá nhân:
```bash
# 1. Kiểm tra file đã sửa
git status

# 2. Thêm file thay đổi
git add .

# 3. Commit theo chuẩn Conventional Commit tương ứng với module vừa làm
git commit -m "feat(firmware): implement auto reconnect wifi for esp32"
# hoặc: git commit -m "feat(mobile): display npk chart on dashboard"

# 4. Đẩy code lên GitHub nhánh của mình
git push origin dev-tri  # (Đối với Khiêm: git push origin dev-khiem)
```

### Bước 3: Khi hoàn thành một mốc công việc $\rightarrow$ Báo An Review
1. Truy cập vào: [https://github.com/Anneiry09/AI-Smart-Soil-System/pulls](https://github.com/Anneiry09/AI-Smart-Soil-System/pulls)
2. Bấm nút **New pull request**:
   * Nhánh đích (**base**): chọn **`main`**
   * Nhánh nguồn (**compare**): chọn nhánh của mình (ví dụ `dev-tri` hoặc `dev-khiem`)
3. Bấm **Create pull request**, điền tóm tắt nội dung công việc đã làm và báo cho An:  
   *"An ơi, mình làm xong phần việc được giao rồi, vào review và merge giúp mình nhé!"*

### Bước 4: Sau khi An đã duyệt và gộp vào `main`
Để kéo những thay đổi mới nhất của cả nhóm về lại máy của mình:
```bash
# Đang đứng ở nhánh riêng của mình, chỉ cần gõ:
git pull origin main
```
*(Sau lệnh này, bạn tiếp tục thực hiện các nhiệm vụ tiếp theo trên nhánh của mình mà không cần tạo nhánh mới).*

---

## 5. Hướng Dẫn Quy Trình Cho AN (Team Lead / Reviewer)

1. **Giao việc:** An linh hoạt phân công nhiệm vụ cụ thể cho từng thành viên theo từng giai đoạn của dự án.
2. **Kiểm tra khi có Pull Request:** Truy cập tab **Pull requests** trên GitHub của dự án.
3. **Review Code (Soát lỗi):** Bấm vào PR đó $\rightarrow$ Chuyển sang tab **Files changed**:
   * Kiểm tra nội dung mã nguồn thay đổi.
   * Đảm bảo không có thông tin nhạy cảm (mật khẩu Wi-Fi thật, API key, token bí mật).
   * Đảm bảo thông điệp commit tuân thủ chuẩn Conventional Commits.
4. **Gộp vào `main` (Merge):**
   * Bấm nút **Merge pull request** (khuyên dùng **Squash and merge** để gộp các commit nhỏ thành 1 commit ngắn gọn trên nhánh `main`).
   * Bấm **Confirm merge**.
5. **Lưu ý quan trọng:** **KHÔNG bấm nút *"Delete branch"*** sau khi merge, vì các nhánh `dev-*` là không gian làm việc cố định lâu dài của các thành viên.

---

## 6. Cài Đặt Khóa Bảo Vệ Nhánh `main` Trên GitHub (Làm 1 lần)

Để tránh trường hợp ai đó lỡ gõ nhầm lệnh đẩy trực tiếp đè lên nhánh chính `main`, An cài đặt bảo vệ:

1. Vào repo trên GitHub: [Settings](https://github.com/Anneiry09/AI-Smart-Soil-System/settings)
2. Chọn mục **Branches** ở cột bên trái.
3. Bấm **Add branch protection rule**:
   * **Branch name pattern:** gõ chữ `main`
   * Tích chọn ô: **Require a pull request before merging**
   * Tích chọn ô: **Require approvals** (chọn số lượng là `1` - chỉ cần An duyệt là được).
4. Kéo xuống cuối trang bấm **Create** (hoặc Save changes).

---

## 7. Danh Sách Kiểm Tra "Clean Git" Trước Khi Push (Pre-push Checklist)

Trước khi gõ `git push`, mỗi thành viên hãy tự kiểm tra:
- [ ] **Không có file rác:** Không commit các thư mục tạm (`.pio/`, `__pycache__/`, `.dart_tool/`, `build/`, `.vscode/`).
- [ ] **Không có thông tin nhạy cảm:** Không để mật khẩu Wi-Fi thực tế, token, credential trong code.
- [ ] **Code kiểm tra chạy tốt:** Build hoặc chạy thử không phát sinh lỗi cú pháp trước khi đẩy.
- [ ] **Commit message chuẩn:** Tuân thủ đúng cú pháp `<type>(<scope>): <mô tả ngắn>`.
