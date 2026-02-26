# Learning Management System (LMS)

Hệ thống quản lý học tập với AI đề xuất khóa học, hỗ trợ cả Web (Odoo) và Mobile (Flutter).

## Cấu Trúc Dự Án

```
LMS/
├── lms/                    # Backend Odoo Module
│   ├── controllers/        # API Controllers
│   ├── models/            # Data Models
│   ├── views/             # UI Views
│   └── security/          # Security Rules
│
├── lms_mobile/            # Flutter Mobile App
│   ├── lib/
│   │   ├── config/        # App Configuration
│   │   ├── models/        # Data Models
│   │   ├── providers/     # State Management
│   │   ├── screens/       # UI Screens
│   │   └── services/      # API Services
│   └── pubspec.yaml       # Dependencies
│
├── config/                # Odoo Configuration
├── data/                  # Database & Sessions
└── docker-compose.yml     # Docker Setup
```

## Yêu Cầu

- Docker & Docker Compose
- Flutter SDK (>=3.0.0)
- Odoo 18.0

## Chạy Backend (Odoo)

```bash
# Start services
docker-compose up -d

# Xem logs
docker-compose logs -f odoo

# Stop services
docker-compose down
```

Truy cập: `http://localhost:8069`

## Chạy Mobile App (Flutter)

```bash
cd lms_mobile

# Cài đặt dependencies
flutter pub get

# Chạy trên Chrome
flutter run -d chrome

# Hoặc chạy trên Android/iOS
flutter run
```

## Cấu Hình

### Backend
- Database: `odoo` (mặc định)
- Port: `8069` (hoặc `8072` nếu dùng docker-compose)

### Mobile App
Cập nhật URL trong `lms_mobile/lib/config/app_config.dart`:
```dart
static const String odooBaseUrl = 'http://localhost:8069';
static const String odooDatabase = 'odoo';
```

**Lưu ý**: Nếu chạy trên thiết bị thật hoặc emulator, thay `localhost` bằng IP máy tính.

## API Endpoints

### Authentication
- `POST /lms/api/register` - Đăng ký tài khoản mới
- `POST /lms/api/login` - Đăng nhập

### Quiz
- `GET /lms/api/quiz/<lesson_id>` - Lấy danh sách quiz
- `POST /lms/api/quiz/submit` - Submit quiz

### Roadmap
- `POST /lms/roadmap/generate` - Tạo roadmap đề xuất

## Tính Năng

- ✅ Đăng ký/Đăng nhập
- ✅ Quản lý khóa học
- ✅ Quiz và đánh giá
- ✅ Roadmap học tập với AI
- ✅ Theo dõi tiến độ
- ✅ Mobile app (Flutter)

## Troubleshooting

### Lỗi CORS
- Đảm bảo Odoo server đã restart sau khi sửa controllers
- Kiểm tra CORS headers trong response

### Lỗi đăng nhập
- Kiểm tra password có được set đúng trong Odoo không
- Reset password trong Odoo admin nếu cần
- Xem log Odoo để debug

### Mobile không kết nối được
- Thay `localhost` bằng IP máy tính trong `app_config.dart`
- Đảm bảo Odoo server đang chạy
- Kiểm tra firewall
