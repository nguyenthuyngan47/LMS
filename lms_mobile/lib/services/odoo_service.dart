import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/student.dart';
import '../models/course.dart';
import '../models/roadmap.dart';
import '../models/progress.dart';

class OdooService {
  final String baseUrl;
  final String database;
  int? uid;
  String? sessionId;
  String? _password; // Lưu password để dùng cho RPC calls
  Map<String, dynamic>? _cachedUser; // Cache user data từ login response
  Map<String, dynamic>? _cachedStudent; // Cache student data từ login response
  String? lastError; // Lưu error message từ lần gọi API cuối

  OdooService({
    String? baseUrl,
    String? database,
  })  : baseUrl = baseUrl ?? AppConfig.odooBaseUrl,
        database = database ?? AppConfig.odooDatabase;

  // Authenticate user using custom API endpoint (có CORS)
  Future<bool> authenticate(String email, String password) async {
    lastError = null; // Reset error
    
    try {
      print('=== AUTHENTICATION REQUEST ===');
      print('URL: $baseUrl/lms/api/login');
      print('Database: $database');
      print('Email: $email');
      print('Password: ******');
      
      final url = Uri.parse('$baseUrl/lms/api/login');
      final body = jsonEncode({
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
          'email': email,
          'password': password,
          'database': database,
        },
        'id': 1,
      });

      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: body,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          lastError = 'Kết nối timeout. Kiểm tra lại URL và đảm bảo server đang chạy.';
          throw Exception(lastError);
        },
      );

      print('=== AUTHENTICATION RESPONSE ===');
      print('Status Code: ${response.statusCode}');
      print('Response Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Parse response (có thể là JSON-RPC hoặc direct JSON)
        final resultData = (data.containsKey('result') && data['result'] is Map)
            ? data['result'] as Map<String, dynamic>
            : (data.containsKey('success') ? data : null);
        
        if (resultData == null || resultData['success'] != true) {
          lastError = resultData?['message'] ?? 'Invalid response';
          print('❌ Login failed: $lastError');
          return false;
        }
        
        final resultUid = resultData['uid'];
        if (resultUid is int && resultUid > 0) {
          uid = resultUid;
          _password = password;
          
          // Cache user và student data từ response (ưu tiên từ login response)
          if (resultData.containsKey('user')) {
            _cachedUser = resultData['user'] as Map<String, dynamic>;
            print('✅ User data cached from login response');
          }
          
          if (resultData.containsKey('student') && resultData['student'] != null) {
            _cachedStudent = resultData['student'] as Map<String, dynamic>;
            print('✅ Student data cached from login response');
          } else {
            // Nếu không có student trong response, sẽ lấy sau qua getCurrentStudent
            print('⚠️ No student data in login response, will fetch via RPC');
          }
          
          print('✅ Authentication successful (UID: $uid)');
          return true;
        } else {
          lastError = 'UID không hợp lệ từ server';
          print('❌ Login failed: $lastError');
        }
      } else {
        lastError = 'HTTP ${response.statusCode}: ${response.body}';
        print('❌ Login failed: $lastError');
      }
      
      return false;
    } catch (e) {
      lastError = e.toString();
      print('❌ Login exception: $e');
      return false;
    }
  }

  // Execute RPC call using Odoo JSON-RPC
  Future<dynamic> _executeRpc(String model, String method, List<dynamic> args) async {
    if (uid == null) {
      print('User not authenticated');
      return null;
    }
    
    if (_password == null) {
      print('Password not available for RPC call');
      return null;
    }

    try {
      final url = Uri.parse(AppConfig.jsonRpcUrl);
      final body = jsonEncode({
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
          'service': 'object',
          'method': 'execute_kw',
          'args': [database, uid, _password, model, method, args],
        },
        'id': 1,
      });

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: body,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['error'] != null) {
          print('RPC error: ${data['error']}');
          return null;
        }
        return data['result'];
      }
      return null;
    } catch (e) {
      print('RPC error: $e');
      return null;
    }
  }

  // Get current student - ưu tiên dùng cache từ login response
  Future<Student?> getCurrentStudent() async {
    try {
      if (uid == null) {
        print('Cannot get student: user not authenticated');
        return null;
      }
      
      // Ưu tiên dùng cache từ login response (nhanh nhất)
      if (_cachedStudent != null) {
        print('✅ Using cached student data from login response');
        try {
          return Student.fromJson(_cachedStudent!);
        } catch (e) {
          print('Error parsing cached student: $e');
          _cachedStudent = null; // Clear cache nếu có lỗi
        }
      }
      
      print('Cache not available, fetching student via RPC using user_id...');
      
      // Fallback: Dùng RPC để lấy student qua user_id (ưu tiên user_id)
      final result = await _executeRpc(
        AppConfig.studentModel,
        'search_read',
        [
          [['user_id', '=', uid]],  // Tìm student qua user_id (cách đúng nhất)
          [
            'id',
            'name',
            'email',
            'phone',
            'current_level',
            'learning_goals',
            'desired_skills',
            'total_courses',
            'completed_courses',
            'average_score',
            'is_active',
            'user_id',
          ],
        ],
      );

      if (result != null && result.isNotEmpty) {
        final student = Student.fromJson(result[0]);
        _cachedStudent = result[0]; // Cache để dùng lần sau
        print('✅ Student found via RPC: ${student.name} (ID: ${student.id})');
        return student;
      }
      
      print('⚠️ No student found for user_id: $uid');
      return null;
    } catch (e) {
      print('Get student error: $e');
      return null;
    }
  }

  // Get enrolled courses for current student
  Future<List<Course>> getEnrolledCourses() async {
    try {
      // First get current student
      final student = await getCurrentStudent();
      if (student == null) {
        return [];
      }

      // Then get enrolled courses
      final result = await _executeRpc(
        AppConfig.studentCourseModel,
        'search_read',
        [
          [['student_id', '=', student.id]],
          [
            'id',
            'course_id',
            'enrollment_date',
            'status',
            'progress',
            'final_score',
            'completion_date',
          ],
        ],
      );

      if (result != null) {
        return result.map((json) => Course.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Get courses error: $e');
      return [];
    }
  }

  // Get roadmap for current student
  Future<List<Roadmap>> getRoadmaps() async {
    try {
      // First get current student
      final student = await getCurrentStudent();
      if (student == null) {
        return [];
      }

      // Then get roadmaps
      final result = await _executeRpc(
        AppConfig.roadmapModel,
        'search_read',
        [
          [['student_id', '=', student.id]],
          [
            'id',
            'name',
            'state',
            'recommendation_method',
            'total_courses',
            'create_date',
          ],
        ],
      );

      if (result != null) {
        return result.map((json) => Roadmap.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Get roadmaps error: $e');
      return [];
    }
  }

  // Register new user and student via API endpoint
  Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
    String? phone,
    required String currentLevel,
  }) async {
    try {
      // Đảm bảo URL đúng format
      String registerUrl = '$baseUrl/lms/api/register';
      if (registerUrl.contains('localhost') || registerUrl.contains('127.0.0.1')) {
        // Cảnh báo nếu dùng localhost trên mobile
        print('WARNING: Using localhost may not work on mobile device. Use your computer IP address instead.');
      }
      
      final url = Uri.parse(registerUrl);
      // Odoo JSON-RPC format
      final body = jsonEncode({
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
          'name': name,
          'email': email,
          'password': password,
          'phone': phone ?? '',
          'current_level': currentLevel,
        },
        'id': 1,
      });

      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: body,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw Exception('Kết nối timeout. Kiểm tra lại URL và đảm bảo server đang chạy.');
        },
      );

      print('=== REGISTRATION RESPONSE ===');
      print('Status Code: ${response.statusCode}');
      print('Response Body: ${response.body}');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('Parsed data: $data');
        
        // Có thể là JSON-RPC format hoặc direct JSON
        Map<String, dynamic>? resultData;
        if (data is Map<String, dynamic>) {
          if (data.containsKey('result')) {
            // JSON-RPC format
            resultData = data['result'] as Map<String, dynamic>;
            print('Using result from JSON-RPC format');
          } else if (data.containsKey('success')) {
            // Direct JSON response
            resultData = data;
            print('Using direct JSON response');
          }
        }
        
        if (resultData != null) {
          print('✅ Registration result: success=${resultData['success']}, message=${resultData['message']}');
          return resultData;
        } else {
          print('❌ Invalid response format');
          return {'success': false, 'message': 'Server không trả về dữ liệu hợp lệ'};
        }
      } else {
        print('❌ HTTP Error: ${response.statusCode}');
        return {
          'success': false,
          'message': 'Lỗi kết nối: HTTP ${response.statusCode}. Kiểm tra lại URL: $registerUrl'
        };
      }
    } catch (e) {
      print('Register error: $e');
      String errorMsg = 'Lỗi kết nối đến server';
      
      if (e.toString().contains('Failed host lookup') || e.toString().contains('Connection refused')) {
        errorMsg = 'Không thể kết nối đến server. '
            'Nếu dùng mobile device, hãy thay localhost bằng IP của máy tính (ví dụ: http://192.168.1.100:8069)';
      } else if (e.toString().contains('timeout')) {
        errorMsg = 'Kết nối timeout. Kiểm tra lại URL và đảm bảo server đang chạy.';
      } else {
        errorMsg = 'Lỗi: ${e.toString()}';
      }
      
      return {'success': false, 'message': errorMsg};
    }
  }

  // Get course progress
  Future<Progress?> getCourseProgress(int courseId) async {
    try {
      final result = await _executeRpc(
        AppConfig.learningHistoryModel,
        'search_read',
        [
          [['course_id', '=', courseId]],
          [
            'id',
            'date',
            'course_id',
            'lesson_id',
            'study_duration',
            'quiz_score',
            'status',
          ],
        ],
      );

      if (result != null && result.isNotEmpty) {
        return Progress.fromJson(result);
      }
      return null;
    } catch (e) {
      print('Get progress error: $e');
      return null;
    }
  }
}
