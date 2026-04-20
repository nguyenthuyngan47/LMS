# BÁO CÁO LỖI TẢI ẢNH LÊN - LMS FACE GATE

## 📋 Tóm tắt
Phát hiện 5 lỗi tiềm ẩn khi tải ảnh lên hệ thống, có thể gây lỗi server, dữ liệu không nhất quán hoặc xác thực ảnh thất bại.

---

## 🔴 Lỗi 1: Chuyển đổi Integer không an toàn (Critical)

**Vị trí:** `lms_face_gate/controllers/face_sample.py`, dòng 175

```python
if is_manager and student_id:
    student = env['lms.student'].sudo().browse(int(student_id))  # ❌ Có thể lỗi ValueError
```

**Vấn đề:**
- Nếu `student_id` không phải là số hợp lệ, `int(student_id)` sẽ ném `ValueError`
- Lỗi này không được bắt, gây crash API

**Giải pháp:**
```python
try:
    student_id_int = int(student_id)
except (ValueError, TypeError):
    return {'success': False, 'error': 'ID sinh viên không hợp lệ'}

if is_manager and student_id:
    student = env['lms.student'].sudo().browse(student_id_int)
```

---

## 🔴 Lỗi 2: Chuyển đổi ảnh không đúng format (Critical)

**Vị trí:** `lms_face_gate/controllers/face_sample.py`, dòng 183-185

```python
student.with_context(lms_face_gate_skip_face_sample_validation=True).write({
    'face_sample_image': image_b64,  # ❌ Gửi base64 string thay vì bytes
    'face_embedding': embedding,
    'face_sample_status': 'ok',
    'face_sample_message': 'Ảnh mẫu hợp lệ, sẵn sàng điểm danh',
})
```

**Vấn đề:**
- `face_sample_image` là Binary field, cần bytes không phải base64 string
- Comment trong `lms_student_face.py` dòng 51 nói: "Sau super().write, Binary trên record là bytes file thật"
- Nếu gửi base64, Odoo sẽ lưu sai format, làm re-validation thất bại

**Giải pháp:**
```python
from odoo.addons.lms_face_gate.controllers.face_sample import _raw_image_file_bytes

# Trước khi write, chuyển base64 → raw bytes
image_bytes = _raw_image_file_bytes(image_b64)
if not image_bytes:
    return {'success': False, 'error': 'Không thể chuyển đổi ảnh'}

student.with_context(lms_face_gate_skip_face_sample_validation=True).write({
    'face_sample_image': image_bytes,  # ✅ Gửi bytes thực tế
    'face_embedding': embedding,
    'face_sample_status': 'ok',
    'face_sample_message': 'Ảnh mẫu hợp lệ, sẵn sàng điểm danh',
})
```

---

## 🟠 Lỗi 3: Thông báo lỗi không chính xác (High)

**Vị trí:** `lms_face_gate/controllers/face_sample.py`, dòng 83-85

```python
except Exception:
    return None, 'Định dạng ảnh không hợp lệ, chỉ chấp nhận JPEG hoặc PNG'
```

**Vấn đề:**
- Bắt tất cả Exception nhưng chỉ báo lỗi định dạng
- Lỗi thực tế có thể là: hết bộ nhớ, lỗi permissions, lỗi thư viện, v.v...
- Khó debug khi hệ thống gặp sự cố

**Giải pháp:**
```python
except Exception as exc:
    _logger.exception('Image decoding failed')
    error_msg = str(exc) if str(exc) else 'Lỗi xử lý ảnh'
    return None, f'Định dạng ảnh không hợp lệ hoặc lỗi kỹ thuật: {error_msg}'
```

---

## 🟠 Lỗi 4: Không xác thực quyền editor image (High)

**Vị trí:** `lms_face_gate/controllers/face_sample.py`, dòng 168-173

```python
if is_manager and student_id:
    student = env['lms.student'].sudo().browse(int(student_id))
    if not student.exists():
        return {'success': False, 'error': 'Không tìm thấy sinh viên'}
```

**Vấn đề:**
- Manager có thể tải ảnh cho sinh viên bất kỳ mà không kiểm tra quyền
- Không kiểm tra `is_student_course_readonly` hoặc các constraints khác
- Sinh viên có thể chỉnh sửa ảnh của sinh viên khác (nếu bypass)

**Giải pháp:**
```python
if is_manager and student_id:
    try:
        student = env['lms.student'].sudo().browse(int(student_id))
    except (ValueError, TypeError):
        return {'success': False, 'error': 'ID sinh viên không hợp lệ'}
    
    if not student.exists():
        return {'success': False, 'error': 'Không tìm thấy sinh viên'}
    
    # ✅ Kiểm tra quyền chỉnh sửa
    if student.is_instructor_restricted:
        return {'success': False, 'error': 'Sinh viên này không thể sửa ảnh do bị khóa'}
else:
    # Sinh viên chỉ có thể sửa ảnh của chính mình
    student = env['lms.student'].sudo().search([('user_id', '=', user.id)], limit=1)
    if not student:
        return {
            'success': False,
            'error': 'Tài khoản chưa liên kết hồ sơ sinh viên, liên hệ admin',
        }
```

---

## 🟡 Lỗi 5: Race condition - validate 2 lần (Medium)

**Vị trí:** 
- `face_sample.py` dòng 165: `validate_and_embed(image_b64, min_face_ratio)`
- `lms_student_face.py` dòng 70-75: validate lại trong `write()`

**Vấn đề:**
- Validate ảnh ở controller (convert base64 → bytes)
- Validate lại ở model khi `write()` (nhưng lúc này đã là bytes)
- Nếu bytes không match với base64 ban đầu (do lỗi encoding), validation thứ 2 sẽ fail
- Ảnh sẽ bị đánh dấu "invalid" dù validate lần 1 thành công

**Mô tả chi tiết:**
```
Luồng hiện tại:
1. Controller nhận base64 → validate_and_embed(base64)
2. Controller gửi base64 đến model.write()
3. Odoo ORM convert base64 → bytes
4. Model lại gọi validate_and_embed(bytes) 
5. _raw_image_file_bytes(bytes) check magic bytes

VẤNĐỀ: Nếu bytes sau ORM convert không match 100%, validate lần 2 fail
```

**Giải pháp:**
```python
# Trong controller - chỉ validate 1 lần, sau đó skip ở model
embedding, error = validate_and_embed(image_b64, min_face_ratio)
if error:
    student.with_context(
        lms_face_gate_skip_face_sample_validation=True
    ).write({
        'face_sample_status': 'invalid',
        'face_sample_message': error,
    })
    return {'success': False, 'error': error}

# Convert base64 → bytes trước khi write
image_bytes = _raw_image_file_bytes(image_b64)
student.with_context(
    lms_face_gate_skip_face_sample_validation=True  # ✅ Skip validate lần 2
).write({
    'face_sample_image': image_bytes,
    'face_embedding': embedding,
    'face_sample_status': 'ok',
    'face_sample_message': 'Ảnh mẫu hợp lệ, sẵn sàng điểm danh',
})
```

---

## 📊 Bảng Mức Độ Ưu Tiên

| Lỗi | Tên | Mức Độ | Tác Động | Khắc Phục |
|-----|-----|--------|---------|----------|
| 1 | Integer không an toàn | 🔴 Critical | Server crash | 1 giờ |
| 2 | Format ảnh sai | 🔴 Critical | Re-validation fail | 1-2 giờ |
| 3 | Thông báo lỗi sai | 🟠 High | Khó debug | 30 phút |
| 4 | Không kiểm quyền | 🟠 High | Bảo mật | 1 giờ |
| 5 | Validate 2 lần | 🟡 Medium | UX xấu | 45 phút |

---

## 🔧 Tổng Hợp File Cần Sửa

### File 1: `lms_face_gate/controllers/face_sample.py`
- Dòng 175: Thêm try-except cho `int(student_id)`
- Dòng 183-185: Convert `image_b64` → `image_bytes`
- Dòng 85: Cải thiện thông báo lỗi
- Dòng 170-173: Thêm kiểm tra quyền

### File 2: `lms_face_gate/models/lms_student_face.py`
- Dòng 70-75: Cập nhật validation logic nếu cần

---

## ✅ Kiểm Tra Tính Năng Sau Sửa

```bash
# Test case 1: Upload ảnh hợp lệ
POST /lms/face-gate/upload-sample
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJ...",
  "student_id": null
}

# Test case 2: Upload với student_id không hợp lệ
POST /lms/face-gate/upload-sample
{
  "image": "...",
  "student_id": "abc"  # ❌ Phải trả về lỗi chứ không crash
}

# Test case 3: Manager upload cho sinh viên khác
POST /lms/face-gate/upload-sample
{
  "image": "...",
  "student_id": 5
}

# Test case 4: Ảnh quá nhỏ/lớn
POST /lms/face-gate/upload-sample
{
  "image": "..."  # 50MB
}
```

---

## 📝 Ghi Chú Thêm

- Cần test trên Windows với file path dài
- Cần kiểm tra memory leaks khi xử lý ảnh lớn
- Cân nhắc cache face embeddings
- Thêm timeout cho face_recognition.face_locations()
