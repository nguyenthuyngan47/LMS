# SỬA LỖI TẠO MẬT KHẨU

## 🔴 VẤN ĐỀ

Khi đăng ký, báo lỗi "Lỗi khi tạo mật khẩu" hoặc "Không thể tạo mật khẩu"

## ✅ GIẢI PHÁP ĐÃ ÁP DỤNG

### **Cách set password mới (ưu tiên):**

1. **Tạo user trước** (không có password)
2. **Hash password** bằng `crypt_context.hash()`
3. **Set trực tiếp** vào `password_crypt` field
4. **Verify** password đã được set đúng

### **Fallback methods:**

- Nếu cách 1 không được → Dùng `_set_password()`
- Nếu vẫn không được → Dùng `write({'password': password})`

## 🔍 DEBUG

### **Xem log Odoo:**

```bash
docker-compose logs -f odoo | grep -E "(Password|password|ERROR|✅|❌)"
```

### **Kiểm tra trong Odoo Shell:**

```python
# Vào Odoo shell
docker-compose exec odoo odoo shell -d odoo

# Kiểm tra user vừa tạo
email = 'test@example.com'  # Thay bằng email bạn vừa đăng ký
user = env['res.users'].search([('login', '=', email)], limit=1)

if user:
    print(f"User: {user.name} (ID: {user.id})")
    print(f"Has password_crypt: {bool(user.password_crypt)}")
    if user.password_crypt:
        print(f"✅ Password đã được set!")
        
        # Test password
        password = '123456'  # Thay bằng password bạn đã nhập
        try:
            user._check_credentials(password)
            print("✅ Password đúng!")
        except:
            print("❌ Password sai!")
    else:
        print("❌ Password chưa được set!")
        
        # Set password thủ công
        password = '123456'
        crypt_context = user._crypt_context()
        hashed = crypt_context.hash(password)
        user.write({'password_crypt': hashed})
        env.cr.commit()
        print("✅ Password đã được set thủ công!")
else:
    print("❌ User không tồn tại!")
```

## 🚀 CẦN LÀM

1. **Restart Odoo:**
   ```bash
   docker-compose restart odoo
   ```

2. **Test lại đăng ký:**
   - Đăng ký tài khoản mới
   - Xem log Odoo để kiểm tra password có được set không
   - Nếu vẫn lỗi, xem log chi tiết

3. **Nếu vẫn lỗi:**
   - Xem log Odoo để biết cách nào set password thành công
   - Hoặc set password thủ công trong Odoo Shell (xem script trên)

## 📝 LƯU Ý

- Nếu password không được set, user sẽ bị xóa tự động (để có thể đăng ký lại)
- Student record cũng sẽ bị xóa nếu user bị xóa
- Error message sẽ hiển thị rõ ràng cho user
