import 'package:flutter/foundation.dart';
import '../services/odoo_service.dart';
import '../config/app_config.dart';
import '../models/progress.dart';

class ProgressProvider with ChangeNotifier {
  final OdooService _odooService = OdooService(
    baseUrl: AppConfig.odooBaseUrl,
    database: AppConfig.odooDatabase,
  );

  Map<int, Progress> _progressMap = {};
  bool _isLoading = false;
  String? _errorMessage;

  Progress? getProgress(int courseId) => _progressMap[courseId];
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> loadProgress(int courseId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final progress = await _odooService.getCourseProgress(courseId);
      if (progress != null) {
        _progressMap[courseId] = progress;
      }
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Lỗi tải tiến độ: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }
}
