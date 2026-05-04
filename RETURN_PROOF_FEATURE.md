# Tính Năng Upload Ảnh/Video Bằng Chứng Trả Hàng

## 🎯 Tổng Quan
Khách hàng **bắt buộc** phải upload ảnh hoặc video sản phẩm trả hàng khi yêu cầu trả hàng. Cả khách hàng và chủ cửa hàng (admin) đều có thể xem được bằng chứng này.

---

## 📝 Các Thay Đổi Được Thực Hiện

### 1. **Database Model** (`store/models.py`)
- Field `customer_return_proof` đã được thêm vào model `ReturnRequest`
- Migration: `0009_returnrequest_customer_return_proof.py` (đã tồn tại)
- Loại file: `FileField` - hỗ trợ ảnh (JPG, PNG, WebP) và video (MP4, MOV)
- Upload folder: `/media/customer_return_proofs/`

### 2. **Frontend - Khách Hàng** (`templates/store/order_list.html`)
- ✅ Thêm section upload file trong modal "Yêu cầu trả hàng & hoàn tiền"
- ✅ Input file bắt buộc (required): `<input type="file" ... required>`
- ✅ Hỗ trợ định dạng: `accept="image/*,video/*"`
- ✅ Form sử dụng `enctype="multipart/form-data"`
- ✅ UI thân thiện: Background xanh lá, icon, hướng dẫn rõ ràng

### 3. **Backend - View** (`store/views.py`)
```python
def return_request(request, order_code):
    # ✅ Bắt buộc validate file upload
    if 'customer_return_proof' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Vui lòng upload ảnh hoặc video...'})
    
    # ✅ Lưu file trực tiếp khi tạo ReturnRequest
    return_req = ReturnRequest.objects.create(
        ...
        customer_return_proof=request.FILES['customer_return_proof'],
    )
```

### 4. **Admin Panel** (`templates/admin_panel/xu_ly_yeu_cau.html`)
- ✅ Hiển thị bằng chứng khách hàng trong modal chi tiết trả hàng
- ✅ Tự động detect loại file: Hiển thị ảnh hoặc video player
- ✅ Click để xem kích thước đầy đủ (open in new tab)
- ✅ Section riêng: "Bằng chứng khách hàng cung cấp"

### 5. **Media Folder**
- ✅ Folder `/media/customer_return_proofs/` đã được tạo
- ✅ Cấu hình trong `settings.py`: `MEDIA_URL = '/media/'` và `MEDIA_ROOT = BASE_DIR / 'media'`

---

## 🔄 Quy Trình Sử Dụng

### **Từ Phía Khách Hàng:**
1. Vào "Đơn hàng của tôi" → tab "Hoàn thành"
2. Click "Trả hàng" trên đơn hàng
3. Modal hiện ra, nhập thông tin:
   - Họ tên & SĐT
   - Chọn lý do trả hàng
   - Nhập ghi chú (tùy chọn)
   - Điền thông tin ngân hàng
   - **⭐ UPLOAD ẢNH/VIDEO (BẮT BUỘC)** ← NEW!
4. Click "XÁC NHẬN GỬI"

### **Từ Phía Admin:**
1. Vào "Xử lý yêu cầu trả hàng" (Admin Panel)
2. Click nút "Xem" trên yêu cầu
3. Modal chi tiết hiện ra, tại section **"Bằng chứng khách hàng cung cấp"**:
   - Nếu là ảnh: Hiển thị thumbnail
   - Nếu là video: Video player với controls
   - Click để xem kích thước đầy đủ
4. Admin duyệt hoặc từ chối dựa trên bằng chứng

---

## 🎨 Giao Diện

### **Khách Hàng - Input Upload**
```
┌────────────────────────────────────────┐
│ 🖼️  UPLOAD ẢNH/VIDEO BẰNG CHỨNG         │
│ * Bắt buộc upload ảnh hoặc video sản   │
│   phẩm trả hàng để chứng minh tình trạng│
│ [📁 Chọn tệp...]                       │
│ Hỗ trợ: ảnh (JPG, PNG, WebP) và video │
│ (MP4, MOV). Tối đa 50MB.               │
└────────────────────────────────────────┘
```

### **Admin - Hiển Thị Bằng Chứng**
```
┌────────────────────────────────────────┐
│ 📋 Bằng chứng khách hàng cung cấp      │
│                                        │
│ ┌──────────────────────────────────┐  │
│ │ [🖼️  Ảnh sản phẩm trả]          │  │
│ │ hoặc                             │  │
│ │ [▶️  Video player]               │  │
│ └──────────────────────────────────┘  │
│ (Nhấp vào để xem kích thước đầy đủ)   │
└────────────────────────────────────────┘
```

---

## 📁 Cấu Trúc Folder
```
media/
├── avatars/              (Ảnh hồ sơ user)
├── payment_proofs/       (Biên lai chuyển khoản)
├── products/            (Ảnh sản phẩm)
├── refund_proofs/       (Biên lai hoàn tiền)
└── customer_return_proofs/  ✨ NEW - Ảnh/video trả hàng từ khách
    ├── DH1714826534AB12_photo.jpg
    ├── DH1714826534CD34_video.mp4
    └── ...
```

---

## ✅ Checklist Xác Nhận

- [x] Model có field `customer_return_proof`
- [x] Migration đã được tạo (0009)
- [x] Frontend: Input file upload (required)
- [x] Form: `enctype="multipart/form-data"`
- [x] Backend: Validate bắt buộc upload
- [x] Admin: Hiển thị ảnh/video
- [x] Media folder tạo sẵn
- [x] UI/UX: Thân thiện, rõ ràng

---

## 🔗 Các Files Chỉnh Sửa

| File | Thay Đổi |
|------|---------|
| `store/models.py` | ✅ (Đã tồn tại, không cần chỉnh) |
| `store/views.py` | ✅ Thêm validation bắt buộc upload |
| `templates/store/order_list.html` | ✅ Thêm input file + enctype |
| `templates/admin_panel/xu_ly_yeu_cau.html` | ✅ (Đã tồn tại, hiển thị đúng) |
| `settings.py` | ✅ (Media config đã tồn tại) |
| `media/customer_return_proofs/` | ✅ Folder tạo mới |

---

## 🚀 Testing

### Test Khách Hàng Upload:
1. Vào /orders/ → tìm đơn hoàn thành
2. Click "Trả hàng"
3. **Không** chọn file → Submit → Lỗi: "Vui lòng upload ảnh hoặc video..."
4. Chọn file ảnh/video → Submit → ✅ "Gửi yêu cầu thành công!"

### Test Admin Xem:
1. Vào Admin Panel → "Xử lý yêu cầu trả hàng"
2. Click "Xem" trên yêu cầu
3. Tìm section "Bằng chứng khách hàng cung cấp"
4. Xem ảnh hoặc video được upload

---

## 💡 Ghi Chú

- Giới hạn file: 50MB (có thể điều chỉnh trong `settings.py` nếu cần)
- File được lưu với tên: `customer_return_proofs/[tên file gốc]`
- Khách hàng và Admin cùng có thể xem được file
- Video được phát trực tiếp (MP4, MOV) hoặc ảnh hiển thị thumbnail

