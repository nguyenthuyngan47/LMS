# LMS Mobile App

Ứng dụng mobile Flutter cho sinh viên trong hệ thống LMS.

## Chạy App

### 1. Cài đặt Dependencies
```bash
flutter pub get
```

### 2. Cấu hình URL
Mở `lib/config/app_config.dart` và cập nhật:
```dart
static const String odooBaseUrl = 'http://localhost:8069';
```

**Lưu ý**: 
- Chrome/Web: Dùng `localhost`
- Android Emulator: Dùng `http://10.0.2.2:8069`
- Thiết bị thật: Dùng IP máy tính (ví dụ: `http://192.168.1.100:8069`)

### 3. Chạy App
```bash
# Chrome (Web)
flutter run -d chrome

# Android
flutter run -d android

# iOS (chỉ trên Mac)
flutter run -d ios
```

## Cấu Trúc

- `lib/config/` - Cấu hình app và routing
- `lib/models/` - Data models
- `lib/providers/` - State management (Provider)
- `lib/screens/` - UI screens
- `lib/services/` - API services

## Tính Năng

- Đăng nhập/Đăng ký
- Xem danh sách khóa học
- Xem roadmap học tập
- Theo dõi tiến độ
- Làm quiz
