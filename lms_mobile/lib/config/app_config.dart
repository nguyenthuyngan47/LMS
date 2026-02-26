class AppConfig {
  // CỐ ĐỊNH SERVER (không dùng settings)
  // Nếu bạn deploy production thì đổi sang domain/public IP tương ứng.
  static const String odooBaseUrl = 'http://localhost:8069';
  static const String odooDatabase = 'odoo';

  // API Endpoints
  static String get xmlRpcUrl => '$odooBaseUrl/xmlrpc/2';
  static String get jsonRpcUrl => '$odooBaseUrl/jsonrpc';
  
  // Model names
  static const String studentModel = 'lms.student';
  static const String courseModel = 'lms.course';
  static const String roadmapModel = 'lms.roadmap';
  static const String studentCourseModel = 'lms.student.course';
  static const String learningHistoryModel = 'lms.learning.history';
  
  // App Info
  static const String appName = 'LMS Student';
  static const String appVersion = '1.0.0';
}
