import 'package:flutter/foundation.dart';
import '../services/odoo_service.dart';
import '../config/app_config.dart';
import '../models/course.dart';

class CourseProvider with ChangeNotifier {
  final OdooService _odooService = OdooService(
    baseUrl: AppConfig.odooBaseUrl,
    database: AppConfig.odooDatabase,
  );

  List<Course> _courses = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<Course> get courses => _courses;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> loadCourses() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _courses = await _odooService.getEnrolledCourses();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Lỗi tải danh sách khóa học: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }

  Course? getCourseById(int id) {
    try {
      return _courses.firstWhere((course) => course.id == id);
    } catch (e) {
      return null;
    }
  }
}
