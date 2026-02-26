# SỬA LỖI PASSWORD - USER ĐÃ TẠO NHƯNG KHÔNG ĐĂNG NHẬP ĐƯỢC

## 🔴 VẤN ĐỀ

- Tạo tài khoản mới → Đăng nhập lại không được
- Đăng ký lại với cùng email → Báo "đã tồn tại"
- **Nguyên nhân**: User đã được tạo nhưng password không được set đúng

## ✅ GIẢI PHÁP

### **Cách 1: Dùng `_set_password()` (không sudo)**
```python
user._set_password(password)  # Không dùng sudo()
user.invalidate_recordset(['password_crypt'])
```

### **Cách 2: Hash password và set trực tiếp**
```python
crypt_context = user._crypt_context()
hashed = crypt_context.hash(password)
user.sudo().write({'password_crypt': hashed})
```

### **Cách 3: Write với password field**
```python
user.sudo().with_context(no_reset_password=True).write({'password': password})
```

## 🔍 VERIFY PASSWORD

Sau khi set password, verify ngay:
```python
user.refresh()
user._check_credentials(password)  # Sẽ raise exception nếu sai
```

## 📝 CODE MỚI

File: `lms/controllers/auth_controller.py` - hàm `register()`

1. Tạo user trước (không set password trong create)
2. Set password bằng 3 cách (fallback)
3. Verify password sau khi set
4. Log chi tiết để debug

## 🚀 CẦN LÀM

1. **Restart Odoo server**:
   ```bash
   docker-compose restart odoo
   ```

2. **Test lại đăng ký**:
   - Tạo tài khoản mới
   - Kiểm tra log Odoo xem password có được set không
   - Thử đăng nhập ngay sau khi đăng ký

3. **Nếu vẫn lỗi**:
   - Xem log Odoo để biết cách nào set password thành công
   - Kiểm tra `password_crypt` trong database:
     ```sql
     SELECT id, login, password_crypt FROM res_users WHERE login = 'email@example.com';
     ```

## 🔧 DEBUG

### **Kiểm tra password trong Odoo Shell**:
```python
user = env['res.users'].search([('login', '=', 'email@example.com')], limit=1)
print(f"User ID: {user.id}")
print(f"Has password_crypt: {bool(user.password_crypt)}")
try:
    user._check_credentials('password123')
    print("✅ Password is correct!")
except:
    print("❌ Password is wrong!")
```

### **Reset password thủ công**:
```python
user = env['res.users'].search([('login', '=', 'email@example.com')], limit=1)
user._set_password('newpassword123')
print("Password reset successfully")
```
