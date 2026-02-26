# FIX CÁC USER ĐÃ TẠO NHƯNG KHÔNG CÓ PASSWORD

## 🔧 SCRIPT FIX TRONG ODOO SHELL

Chạy script này để fix các user đã tạo nhưng password không được set:

```python
# Vào Odoo shell
docker-compose exec odoo odoo shell -d odoo

# Hoặc nếu không dùng docker:
# python3 odoo-bin shell -d odoo

# Trong shell, chạy script sau:

# 1. Tìm các user không có password_crypt
users_without_password = env['res.users'].search([
    ('password_crypt', '=', False),
    ('active', '=', True)
])

print(f"Found {len(users_without_password)} users without password")

# 2. Xóa các user này (hoặc set password nếu bạn biết password)
for user in users_without_password:
    print(f"User {user.id}: {user.login} - {user.name}")
    # Option 1: Xóa user
    user.unlink()
    print(f"  ✅ Deleted user {user.id}")
    
    # Option 2: Set password mặc định (nếu bạn muốn giữ user)
    # user._set_password('defaultpassword123')
    # env.cr.commit()
    # print(f"  ✅ Set default password for user {user.id}")

env.cr.commit()
print("✅ All done!")
```

## 🔍 KIỂM TRA USER CÓ PASSWORD KHÔNG

```python
# Kiểm tra user cụ thể
email = 'test@example.com'  # Thay bằng email của bạn
user = env['res.users'].search([('login', '=', email)], limit=1)

if user:
    print(f"User: {user.name} (ID: {user.id})")
    print(f"Has password_crypt: {bool(user.password_crypt)}")
    if user.password_crypt:
        print(f"Password crypt length: {len(user.password_crypt)}")
        print(f"Password crypt preview: {user.password_crypt[:20]}...")
    else:
        print("❌ User has NO password!")
        
        # Set password
        new_password = '123456'  # Thay bằng password bạn muốn
        user._set_password(new_password)
        env.cr.commit()
        user.refresh()
        
        # Verify
        try:
            user._check_credentials(new_password)
            print("✅ Password set and verified successfully!")
        except:
            print("❌ Password verification failed!")
else:
    print(f"❌ User not found: {email}")
```

## 🗑️ XÓA TẤT CẢ USER KHÔNG CÓ PASSWORD

```python
# Tìm và xóa tất cả user không có password
users_to_delete = env['res.users'].search([
    ('password_crypt', '=', False),
    ('active', '=', True)
])

print(f"Found {len(users_to_delete)} users without password to delete")

for user in users_to_delete:
    print(f"Deleting user {user.id}: {user.login}")
    user.unlink()

env.cr.commit()
print(f"✅ Deleted {len(users_to_delete)} users")
```

## 📝 LƯU Ý

- **Backup database** trước khi xóa user
- Chỉ xóa user test/development, không xóa user production
- Nếu user đã có student record, cần xóa student trước hoặc xử lý riêng
