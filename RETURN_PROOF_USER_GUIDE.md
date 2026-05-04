# 📋 Hướng Dẫn Sử Dụng Tính Năng Upload Ảnh/Video Trả Hàng

## 🎯 Tính Năng Mới

Khi khách hàng yêu cầu trả hàng, **bắt buộc phải upload ảnh hoặc video** để chứng minh tình trạng sản phẩm. Admin có thể xem trực tiếp trong panel quản lý.

---

## 👤 Từ Phía Khách Hàng

### Các Bước Thực Hiện:

1. **Vào Trang Đơn Hàng**
   - Click menu "Đơn hàng của tôi"
   - Chọn tab "Hoàn thành"

2. **Tạo Yêu Cầu Trả Hàng**
   - Tìm đơn hàng cần trả
   - Click nút "Yêu cầu trả hàng"

3. **Modal Hiện Lên - Điền Thông Tin**
   ```
   📝 Thông tin liên hệ
   ├─ Họ và tên
   └─ Số điện thoại

   📦 Sản phẩm hoàn trả (tự động)

   🏦 THÔNG TIN NHẬN TIỀN HOÀN (Bắt buộc)
   ├─ Tên ngân hàng
   ├─ Số tài khoản
   └─ Tên chủ tài khoản

   ❓ Lý do đổi trả
   ├─ Sản phẩm bị lỗi/hư hỏng
   ├─ Nhận sai sản phẩm
   ├─ Sản phẩm bị vỡ do vận chuyển
   ├─ Chất lượng không đúng kỳ vọng
   ├─ Giao hàng quá lâu
   └─ Khác

   📝 Ghi chú (tùy chọn)

   🖼️ UPLOAD ẢNH/VIDEO BẰNG CHỨNG ⭐ BẮT BUỘC
   └─ Click chọn tệp
   ```

4. **Upload Ảnh/Video** (⭐ **BẮT BUỘC**)
   - Click vùng "Chọn tệp"
   - Chọn ảnh hoặc video từ máy tính
   - **Hỗ trợ định dạng:**
     - 📷 **Ảnh**: JPG, PNG, WebP
     - 🎬 **Video**: MP4, MOV
     - 📊 **Tối đa**: 50MB

5. **Gửi Yêu Cầu**
   - Click "XÁC NHẬN GỬI"
   - Xem thông báo "✅ Gửi yêu cầu thành công!"
   - Trang tự động refresh

### Lưu Ý:
- ⚠️ **Không upload file → Sẽ có lỗi**: "Vui lòng upload ảnh hoặc video bằng chứng"
- ✅ Ảnh/Video phải cho thấy **tình trạng thực tế** của sản phẩm
- 📱 Có thể dùng camera điện thoại để quay video

---

## 👨‍💼 Từ Phía Admin

### Quy Trình Xử Lý:

1. **Vào Admin Panel**
   - URL: `/admin-panel/`
   - Chọn "Xử lý yêu cầu trả hàng"

2. **Danh Sách Yêu Cầu**
   ```
   Bộ lọc:
   ├─ Chờ xử lý (n)
   └─ Đã từ chối (m)

   Tìm kiếm: Nhập mã đơn, tên khách, etc.
   ```

3. **Xem Chi Tiết Yêu Cầu**
   - Click nút "Xem" (🔍)
   - Modal chi tiết mở ra

4. **Kiểm Tra Bằng Chứng**
   ```
   ┌─ Bằng chứng khách hàng cung cấp
   │  ├─ Nếu ảnh: Hiển thị ảnh thumbnail
   │  │  └─ Click để mở full size
   │  │
   │  └─ Nếu video: Video player
   │     ├─ Nút Play/Pause
   │     ├─ Timeline scrubber
   │     └─ Fullscreen
   │
   └─ (Nhấp vào để xem kích thước đầy đủ)
   ```

5. **Đánh Giá & Quyết Định**
   - ✅ **Chấp nhận**: Click "Chấp nhận & Duyệt"
     - Xác nhận số tiền hoàn (tự động tính hoặc sửa)
     - Trạng thái chuyển sang "Đã duyệt"
   
   - ❌ **Từ chối**: Click "Từ chối"
     - Nhập lý do chi tiết
     - Gửi phản hồi cho khách

---

## 📂 Cấu Trúc Lưu Trữ

```
media/
└── customer_return_proofs/
    ├── DH17148265XYZ1_photo_2024.jpg
    ├── DH17148265XYZ2_video_proof.mp4
    ├── DH17148265XYZ3_damage.png
    └── ...
```

**Tên file được lưu dưới dạng**: 
- Tên file gốc được keep nguyên
- Tạo unique path tự động

---

## 🔍 Chi Tiết Kỹ Thuật

### Backend Flow:
```python
# Khách upload file
┌─ POST /orders/{order_code}/return/
├─ Validate: customer_return_proof bắt buộc
├─ Nếu thiếu → Error JSON: "Vui lòng upload ảnh hoặc video..."
└─ Nếu OK → Lưu ReturnRequest với file
   └─ File lưu tại: media/customer_return_proofs/{filename}
```

### Frontend Flow:
```javascript
// Form submit
┌─ FormData (multipart/form-data)
├─ Serialize form fields + file
├─ POST /orders/{order_code}/return/
└─ Response: JSON { success: true/false }
   └─ Success → Toast "Gửi yêu cầu thành công!"
   └─ Error → Alert error message
```

---

## ✅ Kiểm Thử (QA)

### Test Case 1: Upload Ảnh
```
✓ Lựa chọn: File ảnh (JPG/PNG/WebP)
✓ Expected: Upload thành công, admin xem được ảnh thumbnail
✓ Actual: PASS
```

### Test Case 2: Upload Video
```
✓ Lựa chọn: File video (MP4/MOV)
✓ Expected: Upload thành công, admin xem được video player
✓ Actual: PASS
```

### Test Case 3: Không Upload
```
✓ Lựa chọn: Không chọn file, submit
✓ Expected: Lỗi "Vui lòng upload ảnh hoặc video..."
✓ Actual: PASS
```

### Test Case 4: File Quá Lớn
```
✓ Lựa chọn: File > 50MB
✓ Expected: Lỗi upload hoặc từ chối
✓ Actual: Phụ thuộc cấu hình Django
```

### Test Case 5: File Không Hợp Lệ
```
✓ Lựa chọn: File .txt, .exe, .pdf
✓ Expected: Accept attribute chặn, không cho chọn
✓ Actual: PASS (phía client)
```

---

## 🐛 Xử Lý Lỗi

| Tình Huống | Lỗi | Giải Pháp |
|-----------|-----|---------|
| Không upload file | ❌ "Vui lòng upload..." | Bắt buộc chọn file |
| File quá lớn | ⚠️ Upload fail | Dùng ảnh/video nhỏ hơn 50MB |
| Format không đúng | ❌ Không cho chọn | Dùng JPG, PNG, MP4, MOV |
| Folder không tồn tại | 🔴 500 Error | Tạo `/media/customer_return_proofs/` |
| Permissions sai | 🔴 403 Forbidden | Kiểm tra quyền folder |

---

## 🚀 Deployment Checklist

- [ ] Database migration đã chạy (`python manage.py migrate`)
- [ ] Folder `/media/customer_return_proofs/` đã tạo
- [ ] Cấu hình `MEDIA_URL` và `MEDIA_ROOT` trong `settings.py`
- [ ] File upload permissions: `755` cho folder, `644` cho file
- [ ] Test upload ảnh/video trên live server
- [ ] Backup database trước khi deploy
- [ ] Test admin xem bằng chứng
- [ ] Test khách hàng xem trạng thái trả hàng

---

## 📞 Support

Nếu có vấn đề:
1. Kiểm tra logs: `python manage.py shell` → inspect database
2. Xem file upload: `ls media/customer_return_proofs/`
3. Debug: Thêm print() trong `return_request()` view
4. Check permissions: `ls -la media/customer_return_proofs/`

---

**Version**: 1.0  
**Last Updated**: May 4, 2026  
**Status**: ✅ Hoạt động

