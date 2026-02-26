import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/odoo_service.dart';
import '../config/app_config.dart';
import '../models/student.dart';

class AuthProvider with ChangeNotifier {
  final OdooService _odooService = OdooService(
    baseUrl: AppConfig.odooBaseUrl,
    database: AppConfig.odooDatabase,
  );

  Student? _currentStudent;
  bool _isLoading = false;
  String? _errorMessage;

  Student? get currentStudent => _currentStudent;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _currentStudent != null;

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      print('🔐 Attempting login with email: $email');
      
      // Authenticate với Odoo - sẽ trả về user và student data
      final authenticated = await _odooService.authenticate(email, password);
      
      if (authenticated) {
        print('✅ Authentication successful, getting student data...');
        
        // getCurrentStudent sẽ ưu tiên dùng cache từ login response (nhanh)
        final student = await _odooService.getCurrentStudent();
        
        if (student != null) {
          _currentStudent = student;
          
          // Lưu credentials để auto login lần sau
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('email', email);
          await prefs.setString('password', password);
          
          print('✅ Login completed successfully for student: ${student.name} (User ID: ${student.userId})');
          _isLoading = false;
          notifyListeners();
          return true;
        } else {
          _errorMessage = 'Đăng nhập thành công nhưng không tìm thấy thông tin sinh viên.';
          print('⚠️ Login successful but student data not found');
        }
      } else {
        _errorMessage = _odooService.lastError ?? 'Đăng nhập thất bại. Vui lòng kiểm tra lại email và mật khẩu.';
        print('❌ Authentication failed: $_errorMessage');
      }
      
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _errorMessage = 'Lỗi kết nối: ${e.toString()}';
      print('❌ Login exception: $e');
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> autoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final email = prefs.getString('email');
    final password = prefs.getString('password');

    if (email != null && password != null) {
      await login(email, password);
    }
  }

  Future<bool> register({
    required String name,
    required String email,
    required String password,
    String? phone,
    required String currentLevel,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      print('📝 Starting registration...');
      print('  - Name: $name');
      print('  - Email: $email');
      print('  - Password length: ${password.length}');
      
      final result = await _odooService.register(
        name: name,
        email: email,
        password: password,
        phone: phone,
        currentLevel: currentLevel,
      );
      
      print('📝 Registration result: $result');
      
      if (result['success'] == true) {
        print('✅ Registration successful!');
        _isLoading = false;
        _errorMessage = null;
        notifyListeners();
        return true;
      }
      
      // Lấy error message từ response
      final errorMsg = result['message'] ?? 'Đăng ký thất bại. Vui lòng thử lại.';
      print('❌ Registration failed: $errorMsg');
      
      // Cải thiện error message cho user
      String userFriendlyMsg = errorMsg;
      if (errorMsg.contains('đã được sử dụng') || errorMsg.contains('already')) {
        userFriendlyMsg = 'Email này đã được sử dụng. Vui lòng dùng email khác.';
      } else if (errorMsg.contains('mật khẩu') || errorMsg.contains('password')) {
        userFriendlyMsg = 'Không thể tạo mật khẩu. Vui lòng thử lại hoặc liên hệ admin.';
      } else if (errorMsg.contains('kết nối') || errorMsg.contains('connection')) {
        userFriendlyMsg = 'Không thể kết nối đến server. Kiểm tra lại kết nối mạng.';
      }
      
      _errorMessage = userFriendlyMsg;
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      print('❌ Registration exception: $e');
      _errorMessage = 'Lỗi đăng ký: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('email');
    await prefs.remove('password');
    
    _currentStudent = null;
    _errorMessage = null;
    notifyListeners();
  }
}
