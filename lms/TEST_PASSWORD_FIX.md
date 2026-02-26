# TEST VÀ DEBUG PASSWORD

## 🔍 KIỂM TRA PASSWORD TRONG ODOO

### **Cách 1: Kiểm tra trong Odoo Shell**

```python
# Vào Odoo shell
docker-compose exec odoo odoo shell -d odoo

# Hoặc nếu không dùng docker:
# python3 odoo-bin shell -d odoo

# Trong shell:
email = 'test@example.com'  # Thay bằng email bạn vừa đăng ký
password = '123456'  # Thay bằng password bạn vừa đăng ký

# Tìm user
user = env['res.users'].search([('login', '=', email)], limit=1)
if not user:
    print(f"❌ User not found: {email}")
else:
    print(f"✅ User found: {user.name} (ID: {user.id})")
    print(f"   - Has password_crypt: {bool(user.password_crypt)}")
    print(f"   - password_crypt length: {len(user.password_crypt) if user.password_crypt else 0}")
    
    # Test password
    try:
        user._check_credentials(password)
        print(f"✅ Password is CORRECT!")
    except Exception as e:
        print(f"❌ Password is WRONG: {str(e)}")
        
        # Thử reset password
        print("\n🔧 Resetting password...")
        user._set_password(password)
        env.cr.commit()
        user.refresh()
        
        # Test lại
        try:
            user._check_credentials(password)
            print(f"✅ Password reset and verified successfully!")
        except:
            print(f"❌ Password still wrong after reset")
```

### **Cách 2: Kiểm tra trong Database**

```sql
-- Kiểm tra user có password_crypt không
SELECT id, login, name, password_crypt, active 
FROM res_users 
WHERE login = 'test@example.com';

-- Nếu password_crypt là NULL hoặc rỗng → password chưa được set
```

## 🔧 SỬA PASSWORD THỦ CÔNG

### **Trong Odoo Shell:**

```python
email = 'test@example.com'
new_password = '123456'

user = env['res.users'].search([('login', '=', email)], limit=1)
if user:
    user._set_password(new_password)
    env.cr.commit()
    print(f"✅ Password reset for user {user.id}")
    
    # Verify
    try:
        user._check_credentials(new_password)
        print("✅ Password verified successfully!")
    except:
        print("❌ Password verification failed!")
```

### **Trong Odoo Admin UI:**

1. Vào **Settings → Users & Companies → Users**
2. Tìm user với email
3. Click vào user
4. Click **Action → Change Password**
5. Đặt password mới
6. Save

## 📝 LOGGING

Xem log Odoo để biết password có được set không:

```bash
docker-compose logs -f odoo | grep -i password
```

Hoặc xem toàn bộ log:
```bash
docker-compose logs -f odoo
```

Tìm các dòng:
- `✅ Password set successfully`
- `❌ Password verification failed`
- `ERROR: Password was NOT set`

## 🚀 RESTART ODOO

Sau khi sửa code, restart Odoo:

```bash
docker-compose restart odoo
```

Hoặc nếu muốn xem log real-time:
```bash
docker-compose restart odoo && docker-compose logs -f odoo
```
