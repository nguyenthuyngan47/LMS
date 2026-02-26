# FLOW ĐĂNG NHẬP MỚI - LẤY TỪ BẢNG RES.USERS

## 🎯 NGUYÊN TẮC

**Flutter lấy thông tin tài khoản từ bảng `res.users` của Odoo, và student được link với user qua `user_id`**

## 📋 CẤU TRÚC DỮ LIỆU

### 1. **Bảng `res.users` (Odoo)**
- Chứa thông tin tài khoản đăng nhập
- Fields: `id`, `name`, `login`, `email`, `password_crypt`
- Đây là bảng chính để authenticate

### 2. **Bảng `lms.student` (Odoo)**
- Chứa thông tin sinh viên
- **Field mới**: `user_id` (Many2one → `res.users`)
- Link với `res.users` qua `user_id`

## 🔄 FLOW ĐĂNG NHẬP

### **Bước 1: User nhập email/password**
```
LoginScreen → User nhập → AuthProvider.login(email, password)
```

### **Bước 2: Gửi request đến Odoo**
```
POST http://localhost:8069/lms/api/login
Body: {
  "email": "...",
  "password": "...",
  "database": "odoo"
}
```

### **Bước 3: Odoo xử lý (auth_controller.py)**
1. Tìm user trong `res.users` theo `login = email`
2. Verify password bằng `user._check_credentials(password)`
3. Nếu thành công, tìm student trong `lms.student` theo `user_id = uid`
4. Trả về:
   - `user`: Thông tin từ `res.users`
   - `student`: Thông tin từ `lms.student` (nếu có)

### **Bước 4: Flutter nhận response**
```
OdooService.authenticate()
  → Cache user và student data từ response
  → Lưu uid và password để dùng cho RPC calls
```

### **Bước 5: Lấy student data**
```
AuthProvider.login()
  → OdooService.getCurrentStudent()
  → Ưu tiên dùng cache từ login response
  → Fallback: RPC call tìm student qua user_id
```

## 🔗 LINKING STUDENT VỚI USER

### **Khi đăng ký mới:**
```python
# auth_controller.py - register()
user = request.env['res.users'].sudo().create({...})
student = request.env['lms.student'].sudo().create({
    'name': name,
    'email': email,
    'user_id': user.id,  # ← Link ngay khi tạo
    ...
})
```

### **Khi đăng nhập (auto-link):**
```python
# auth_controller.py - login()
student = request.env['lms.student'].sudo().search([
    ('user_id', '=', uid)
], limit=1)

# Nếu không tìm thấy qua user_id, tìm qua email và link
if not student:
    student = request.env['lms.student'].sudo().search([
        ('email', '=', email)
    ], limit=1)
    if student and not student.user_id:
        student.sudo().write({'user_id': uid})  # ← Auto-link
```

## 📦 CẤU TRÚC RESPONSE

### **Login Response từ Odoo:**
```json
{
  "success": true,
  "uid": 123,
  "message": "Đăng nhập thành công",
  "user": {
    "id": 123,
    "name": "Nguyen Van A",
    "email": "a@example.com",
    "login": "a@example.com",
    "partner_id": 456
  },
  "student": {
    "id": 789,
    "name": "Nguyen Van A",
    "email": "a@example.com",
    "user_id": 123,  // ← Link với res.users
    ...
  }
}
```

## ⚡ TỐI ƯU

1. **Cache từ login response**: Không cần RPC call thêm
2. **Tìm student qua user_id**: Nhanh hơn tìm qua email
3. **Auto-link**: Tự động link student với user nếu chưa có

## 🔍 DEBUG

### **Kiểm tra user trong Odoo:**
```python
user = env['res.users'].search([('login', '=', 'email@example.com')])
print(f"User ID: {user.id}, Name: {user.name}")
```

### **Kiểm tra student link:**
```python
student = env['lms.student'].search([('user_id', '=', user.id)])
print(f"Student ID: {student.id}, User ID: {student.user_id.id}")
```

### **Kiểm tra password:**
```python
user._check_credentials('password123')  # Sẽ raise exception nếu sai
```

## ✅ CHECKLIST

- [x] Student model có field `user_id`
- [x] Đăng ký tự động link student với user
- [x] Đăng nhập tìm student qua `user_id` (ưu tiên)
- [x] Auto-link student với user nếu chưa có
- [x] Flutter cache user và student từ login response
- [x] Flutter model có `userId` field
