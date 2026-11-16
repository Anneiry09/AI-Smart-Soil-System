# Quy Trình Quản Lý Git Chuẩn (Git Workflow)
> **Dự án:** AI Smart Soil System (nongthinh.vn)  
> **Mục tiêu:** Giữ lịch sử Git sạch (clean history), dễ truy vết, chuyên nghiệp và chuẩn mực cho dự án đa thành phần (Firmware, Backend, Mobile App).

---

## 1. Triết lý Quản Lý Git (Git Philosophy)
* **Nguyên tử (Atomic Commits):** Mỗi commit chỉ làm đúng một việc rõ ràng và có thể kiểm chứng được.
* **Lịch sử tuyến tính (Linear & Clean History):** Tránh các commit rác như "fix", "update", "test 123", tránh merge commit chằng chịt.
* **Bảo mật tuyệt đối:** Tuyệt đối không commit token, mật khẩu Wi-Fi, file môi trường (`.env`, `config.h` chứa thông tin thực tế) lên repository.

---

## 2. Chiến lược Phân Nhánh (Branching Strategy)

Dự án áp dụng mô hình **Feature Branch Workflow** tinh gọn:

* **`main`**: Nhánh chính (Production). Chỉ chứa mã nguồn đã kiểm thử và chạy ổn định.
* **`develop`** *(tùy chọn khi làm nhóm)*: Nhánh tích hợp các tính năng mới trước khi phát hành lên `main`.
* **Nhánh tính năng / sửa lỗi:** Tách từ `main` (hoặc `develop`), hoàn thành xong thì gộp lại qua Pull Request hoặc Fast-Forward/Squash Merge.

### Quy ước đặt tên nhánh:
```text
<loại>/<phạm_vi>-<mô_tả_ngắn>
```

| Loại nhánh | Mục đích | Ví dụ |
| :--- | :--- | :--- |
| `feat/` | Phát triển tính năng mới | `feat/firmware-median-filter` |
| `fix/` | Sửa lỗi (bug fix) | `fix/backend-telemetry-null-ec` |
| `docs/` | Cập nhật tài liệu kỹ thuật | `docs/modbus-specs-update` |
| `refactor/` | Tối ưu mã nguồn (không đổi logic) | `refactor/mobile-state-management` |
| `chore/` | Cấu hình build, CI/CD, dependency | `chore/update-platformio-deps` |

---

## 3. Quy ước Đặt Tên Commit (Conventional Commits)

Áp dụng chuẩn **Conventional Commits** kèm **Scope** tương ứng với cấu trúc thư mục của repo:

### Cú pháp:
```text
<type>(<scope>): <mô tả ngắn bằng tiếng Anh hoặc tiếng Việt rõ ràng>

[Mô tả chi tiết nếu cần]
```

### Các Scope hợp lệ trong dự án:
* `firmware`: Mã nguồn ESP32 PlatformIO (`firmware-esp32/`)
* `backend`: Server API, Database (`backend/`)
* `ai`: Module phân tích độ phì, mô hình AI (`backend/app/modules/soil_ai/`)
* `mobile`: Ứng dụng Flutter (`mobile-app/`)
* `docs`: Tài liệu, kế hoạch (`docs/`, `*.md`)
* `config`: Cấu hình dự án, gitignore, platformio.ini

### Ví dụ chuẩn:
* `feat(firmware): implement median filter for 7-in-1 soil sensor`
* `feat(backend): add telemetry ingestion API endpoint`
* `feat(mobile): create real-time soil telemetry dashboard screen`
* `fix(firmware): resolve rs485 timeout on doit devkit v1`
* `docs(git): create git workflow and commit guidelines`

---

## 4. Quy Trình Làm Việc Từng Bước (Daily Workflow)

### Bước 1: Đồng bộ nhánh chính trước khi làm việc
```bash
git checkout main
git pull origin main
```

### Bước 2: Tạo nhánh mới cho tác vụ cụ thể
```bash
# Ví dụ làm bộ lọc trung vị cho ESP32
git checkout -b feat/firmware-median-filter
```

### Bước 3: Code và Commit theo chuẩn
```bash
# Kiểm tra file thay đổi
git status

# Chỉ add đúng các file liên quan (không dùng git add . bừa bãi)
git add firmware-esp32/src/main.cpp firmware-esp32/include/config.h

# Commit với thông điệp rõ ràng
git commit -m "feat(firmware): add median filter algorithm for soil sensor readings"
```

### Bước 4: Đẩy nhánh lên Remote và Gộp (Merge)
```bash
git push -u origin feat/firmware-median-filter
```
* **Khi gộp vào `main`:** Khuyên dùng **Squash and Merge** trên GitHub để gộp toàn bộ commit nhỏ của nhánh thành 1 commit duy nhất, giữ cho nhánh `main` luôn thẳng tắp và đẹp.
* **Dọn dẹp:** Sau khi gộp xong, xóa nhánh feature cả ở local lẫn remote:
```bash
git checkout main
git pull origin main
git branch -d feat/firmware-median-filter
```

---

## 5. Danh Sách Kiểm Tra "Clean Git" Trước Khi Push (Pre-push Checklist)
- [ ] Không có file rác (`.pio/`, `__pycache__/`, `.dart_tool/`, `build/`, `.DS_Store`).
- [ ] Không có thông tin nhạy cảm (mật khẩu Wi-Fi thật, API key, file bí mật).
- [ ] Code biên dịch không lỗi (PlatformIO build thành công, backend không lỗi cú pháp, flutter analyze sạch sẽ).
- [ ] Lời nhắn commit tuân thủ định dạng `<type>(<scope>): <mô tả>`.
