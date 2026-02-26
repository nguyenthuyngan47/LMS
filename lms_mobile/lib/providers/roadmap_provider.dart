import 'package:flutter/foundation.dart';
import '../services/odoo_service.dart';
import '../config/app_config.dart';
import '../models/roadmap.dart';

class RoadmapProvider with ChangeNotifier {
  final OdooService _odooService = OdooService(
    baseUrl: AppConfig.odooBaseUrl,
    database: AppConfig.odooDatabase,
  );

  List<Roadmap> _roadmaps = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<Roadmap> get roadmaps => _roadmaps;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> loadRoadmaps() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _roadmaps = await _odooService.getRoadmaps();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Lỗi tải roadmap: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }
}
