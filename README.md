# Rabona Sport - Hướng dẫn cài đặt & chạy dự án

## Yêu cầu
- Python **3.10+**
- pip

---

## Các bước cài đặt

### 1. Clone / tải source code về máy

```bash
git clone <link-repo>
cd rabonastore
```

### 2. Tạo môi trường ảo (khuyến nghị)

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo:

- **Windows:**
  ```bash
  .venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 4. Tạo database & chạy migration

```bash
python manage.py migrate
```

### 5. Tạo tài khoản admin

```bash
python manage.py createsuperuser
```

Nhập username, email (có thể bỏ trống), password theo hướng dẫn.

### 6. Tạo dữ liệu mẫu (tuỳ chọn)

Tạo sản phẩm mẫu:
```bash
python tao_san_pham.py
```

Tạo đầy đủ dữ liệu (khách hàng, đơn hàng, v.v.):
```bash
python tao_du_lieu.py
```

### 7. Chạy server

```bash
python manage.py runserver
```

Mở trình duyệt vào: **http://127.0.0.1:8000**

---

## Tài khoản

| Loại | URL đăng nhập | Ghi chú |
|------|--------------|---------|
| Khách hàng | http://127.0.0.1:8000/login/ | Đăng ký tài khoản mới |
| Admin | http://127.0.0.1:8000/login/ | Dùng tài khoản superuser vừa tạo |

Sau khi đăng nhập bằng tài khoản superuser sẽ tự động chuyển vào trang quản trị: **http://127.0.0.1:8000/admin-panel/**

---

## Cấu trúc thư mục chính

```
rabonastore/
├── manage.py
├── requirements.txt
├── tao_san_pham.py       # Script tạo sản phẩm mẫu
├── tao_du_lieu.py        # Script tạo toàn bộ dữ liệu mẫu
├── db.sqlite3            # Database (tự sinh sau migrate)
├── rabonastore/          # Cấu hình Django (settings, urls)
├── store/                # App cửa hàng (models, views, urls)
├── admin_panel/          # App quản trị
├── templates/            # HTML templates
├── static/               # CSS, JS, ảnh tĩnh
└── media/                # Ảnh upload (tự sinh)
```

---

## Lưu ý

- File `db.sqlite3` **không nên** commit lên git (đã có trong `.gitignore`)
- Folder `media/` **không nên** commit lên git
- Mỗi thành viên tự chạy `migrate` và `createsuperuser` trên máy của mình
