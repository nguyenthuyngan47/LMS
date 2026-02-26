# LMS Odoo Module

Module Odoo cho hệ thống Learning Management System.

## Cài Đặt

1. Copy module vào `addons` hoặc mount vào Docker
2. Upgrade module trong Odoo: Apps → LMS → Upgrade
3. Cấu hình System Parameters nếu cần (Gemini API key)

## API Endpoints

### Authentication
- `POST /lms/api/login` - Đăng nhập
- `POST /lms/api/register` - Đăng ký

### Quiz
- `GET /lms/api/quiz/<lesson_id>` - Lấy quiz
- `POST /lms/api/quiz/submit` - Submit quiz

### Roadmap
- `POST /lms/roadmap/generate` - Tạo roadmap

## Models

- `lms.student` - Sinh viên
- `lms.course` - Khóa học
- `lms.lesson` - Bài học
- `lms.quiz` - Câu hỏi quiz
- `lms.roadmap` - Roadmap học tập
- `lms.ai.analysis` - AI phân tích và đề xuất

## Security

- Student group: Chỉ xem được dữ liệu của mình
- Mentor group: Xem được dữ liệu của học viên được phân công
- Admin: Full access
