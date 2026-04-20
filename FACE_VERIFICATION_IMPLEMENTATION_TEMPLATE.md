# Template implementation cho Face Verification Endpoint
# (Đây là code template, cần integrate vào face_sample.py)

"""
IMPLEMENTATION GUIDE: Face Verification Endpoint
================================================

Thêm vào file: lms_face_gate/controllers/face_sample.py

Phần 1: Helper function - so sánh face embeddings
Phần 2: Helper function - tìm sinh viên từ ảnh
Phần 3: Endpoint /lms/face-gate/verify
"""

# ============================================================================
# PHẦN 1: HELPER FUNCTION - SO SÁNH FACE EMBEDDINGS
# ============================================================================

def compare_face_embeddings(embedding1_json, embedding2_json):
    """
    So sánh 2 face embeddings (128-d vectors)
    
    Args:
        embedding1_json: JSON string của embedding 1
        embedding2_json: JSON string của embedding 2
    
    Returns:
        (similarity_score, error_message)
        - similarity_score: 0.0-1.0 (1.0 = giống hoàn toàn)
        - error_message: None nếu thành công, hoặc mô tả lỗi
    
    Note:
        - face_recognition library sử dụng euclidean distance
        - Threshold thường là 0.6 (nghĩa là < 0.6 được coi là khác người)
    """
    try:
        import numpy as np  # noqa: PLC0415
        import json as json_module  # noqa: PLC0415
        from scipy.spatial.distance import euclidean  # noqa: PLC0415
        
        # Parse JSON embeddings
        try:
            enc1 = np.array(json_module.loads(embedding1_json))
            enc2 = np.array(json_module.loads(embedding2_json))
        except (json_module.JSONDecodeError, ValueError, TypeError):
            return None, 'Embedding không hợp lệ'
        
        # Validate dimensions
        if enc1.shape != (128,) or enc2.shape != (128,):
            return None, 'Embedding phải là vector 128 chiều'
        
        # Tính euclidean distance
        distance = euclidean(enc1, enc2)
        
        # Convert distance to similarity score (0-1)
        # face_recognition uses threshold ~0.6
        # similarity = 1 / (1 + distance)
        # Nhưng cách tốt hơn: map distance range (0-1) to similarity (1-0)
        # Thường distance trong range 0-1 cho face_recognition
        
        # Method 1: Exponential mapping
        similarity = np.exp(-distance * 2)  # 1.0 tại distance=0, giảm dần
        
        # Method 2: Inverse mapping (thường dùng hơn)
        # similarity = 1.0 - (distance / 2)  # distance max ~0.8, min ~0.0
        
        # Clamp to [0, 1]
        similarity = max(0.0, min(1.0, float(similarity)))
        
        return round(similarity, 4), None
        
    except ImportError as exc:
        return None, f'Missing dependency: {exc}'
    except Exception as exc:
        _logger.exception('compare_face_embeddings failed')
        return None, f'Lỗi so sánh: {str(exc)}'


# ============================================================================
# PHẦN 2: HELPER FUNCTION - TÌM SINH VIÊN TỪ ẢNH
# ============================================================================

def find_students_by_face(env, lesson_id, captured_image_bytes, min_similarity=0.6):
    """
    Tìm sinh viên từ ảnh live bằng cách so sánh embedding
    
    Args:
        env: Odoo environment
        lesson_id: ID của buổi học
        captured_image_bytes: bytes của ảnh chụp live
        min_similarity: threshold tương đồng tối thiểu (0-1)
    
    Returns:
        {
            'success': bool,
            'student_id': int or None,
            'student_name': str or None,
            'similarity_score': float,
            'matches': [  # Tất cả matches >= min_similarity
                {'student_id': int, 'name': str, 'similarity': float},
                ...
            ],
            'error': str or None
        }
    """
    try:
        # Bước 1: Tính embedding của ảnh live
        embedding_live, error = validate_and_embed(captured_image_bytes)
        if error:
            return {
                'success': False,
                'student_id': None,
                'student_name': None,
                'similarity_score': 0.0,
                'matches': [],
                'error': error
            }
        
        # Bước 2: Tìm buổi học
        lesson = env['lms.lesson'].sudo().browse(lesson_id)
        if not lesson.exists():
            return {
                'success': False,
                'student_id': None,
                'student_name': None,
                'similarity_score': 0.0,
                'matches': [],
                'error': 'Không tìm thấy buổi học'
            }
        
        # Bước 3: Tìm tất cả sinh viên đăng ký buổi học này
        # Note: cần kiểm tra relationship giữa lesson ↔ course ↔ student enrollment
        course = lesson.course_id
        enrollments = env['lms.student.course'].sudo().search([
            ('course_id', '=', course.id),
            ('status', 'in', ['approved', 'learning', 'completed']),  # Chỉ sinh viên active
        ])
        
        students_in_lesson = enrollments.mapped('student_id')
        
        # Bước 4: Filter sinh viên có face sample hợp lệ
        valid_students = students_in_lesson.filtered(
            lambda s: s.face_sample_status == 'ok' and s.face_embedding
        )
        
        if not valid_students:
            return {
                'success': False,
                'student_id': None,
                'student_name': None,
                'similarity_score': 0.0,
                'matches': [],
                'error': 'Không có sinh viên nào có ảnh mẫu trong buổi học này'
            }
        
        # Bước 5: So sánh embedding live với mỗi sinh viên
        matches = []
        
        for student in valid_students:
            try:
                similarity, compare_error = compare_face_embeddings(
                    embedding_live,
                    student.face_embedding
                )
                
                if compare_error:
                    _logger.warning(
                        'Could not compare face for student %s: %s',
                        student.id, compare_error
                    )
                    continue
                
                if similarity >= min_similarity:
                    matches.append({
                        'student_id': student.id,
                        'name': student.name,
                        'similarity': similarity,
                    })
            except Exception as exc:
                _logger.warning(
                    'Face comparison failed for student %s: %s',
                    student.id, exc
                )
                continue
        
        # Bước 6: Sắp xếp theo similarity (cao nhất trước)
        matches = sorted(matches, key=lambda m: m['similarity'], reverse=True)
        
        if not matches:
            return {
                'success': False,
                'student_id': None,
                'student_name': None,
                'similarity_score': 0.0,
                'matches': [],
                'error': f'Không tìm thấy khuôn mặt phù hợp (threshold: {min_similarity})'
            }
        
        # Bước 7: Return sinh viên có match cao nhất
        best_match = matches[0]
        return {
            'success': True,
            'student_id': best_match['student_id'],
            'student_name': best_match['name'],
            'similarity_score': best_match['similarity'],
            'matches': matches,
            'error': None
        }
        
    except Exception as exc:
        _logger.exception('find_students_by_face failed')
        return {
            'success': False,
            'student_id': None,
            'student_name': None,
            'similarity_score': 0.0,
            'matches': [],
            'error': f'Lỗi: {str(exc)}'
        }


# ============================================================================
# PHẦN 3: ENDPOINT /lms/face-gate/verify (MAIN ENDPOINT)
# ============================================================================

class FaceSampleController(http.Controller):

    # ... (existing upload_sample endpoint) ...

    @http.route(
        '/lms/face-gate/verify',
        type='json',
        auth='public',  # Cho phép public access vì camera cần gọi
        methods=['POST'],
        csrf=False,  # API call từ device, không phải browser
    )
    def verify_face(self, lesson_id=None, captured_image=None, **kwargs):
        """
        Endpoint xác thực khuôn mặt sinh viên tại cổng điểm danh
        
        Request:
        {
            "lesson_id": 123,
            "captured_image": "base64..." or "data:image/jpeg;base64,..."
        }
        
        Response:
        {
            "success": true,
            "student_id": 45,
            "student_name": "Nguyễn Văn A",
            "similarity_score": 0.87,
            "timestamp": "2026-04-20T10:30:45",
            "message": "Điểm danh thành công",
            "error": null,
            "matches": [  // Tất cả candidates được so sánh
                {"student_id": 45, "name": "Nguyễn Văn A", "similarity": 0.87},
                {"student_id": 46, "name": "Trần Văn B", "similarity": 0.62}
            ]
        }
        
        Error Response:
        {
            "success": false,
            "student_id": null,
            "error": "Không tìm thấy khuôn mặt phù hợp",
            "timestamp": "..."
        }
        """
        try:
            # Bước 1: Validate input
            captured_image = captured_image or kwargs.get('captured_image')
            lesson_id = lesson_id or kwargs.get('lesson_id')
            
            if not captured_image:
                return {
                    'success': False,
                    'error': 'Thiếu dữ liệu ảnh',
                    'timestamp': fields.Datetime.now(),
                }
            
            if not lesson_id:
                return {
                    'success': False,
                    'error': 'Thiếu ID buổi học',
                    'timestamp': fields.Datetime.now(),
                }
            
            # Bước 2: Validate lesson_id
            try:
                lesson_id_int = int(lesson_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': 'ID buổi học không hợp lệ',
                    'timestamp': fields.Datetime.now(),
                }
            
            # Bước 3: Convert captured_image to bytes
            image_bytes = _raw_image_file_bytes(captured_image)
            if not image_bytes:
                return {
                    'success': False,
                    'error': 'Ảnh không hợp lệ',
                    'timestamp': fields.Datetime.now(),
                }
            
            # Bước 4: Kiểm tra kích thước ảnh
            if len(image_bytes) > MAX_IMAGE_BYTES:
                return {
                    'success': False,
                    'error': f'Ảnh quá lớn ({len(image_bytes) / 1024 / 1024:.1f}MB), tối đa 8MB',
                    'timestamp': fields.Datetime.now(),
                }
            
            # Bước 5: Lấy Odoo environment
            env = request.env
            
            # Bước 6: Lấy threshold từ config
            try:
                min_similarity = float(
                    env['ir.config_parameter']
                    .sudo()
                    .get_param('lms_face_gate.similarity_threshold', '0.6')
                )
            except (TypeError, ValueError):
                min_similarity = 0.6
            
            # Bước 7: Tìm sinh viên từ ảnh
            result = find_students_by_face(
                env,
                lesson_id_int,
                image_bytes,
                min_similarity=min_similarity
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'student_id': None,
                    'student_name': None,
                    'similarity_score': 0.0,
                    'message': result['error'],
                    'error': result['error'],
                    'timestamp': fields.Datetime.now(),
                    'matches': result.get('matches', []),
                }
            
            # Bước 8: Ghi nhận điểm danh
            student_id = result['student_id']
            similarity_score = result['similarity_score']
            
            try:
                attendance = env['lms.face.attendance'].sudo().create({
                    'student_id': student_id,
                    'lesson_id': lesson_id_int,
                    'passed': True,
                    'similarity_score': similarity_score,
                    'captured_image': image_bytes,
                    'failure_reason': None,
                    'timestamp': fields.Datetime.now(),
                })
                _logger.info(
                    'Face attendance recorded: student=%s, lesson=%s, similarity=%.4f',
                    student_id, lesson_id_int, similarity_score
                )
            except Exception as exc:
                _logger.exception('Failed to record attendance')
                # Vẫn trả về success nếu xác thực thành công, log error
                # (để tránh sinh viên bị mắc kẹt ở cổng)
            
            # Bước 9: Trả về kết quả
            return {
                'success': True,
                'student_id': student_id,
                'student_name': result['student_name'],
                'similarity_score': similarity_score,
                'message': f'Điểm danh thành công - {result["student_name"]} ({similarity_score:.2%} tương đồng)',
                'error': None,
                'timestamp': fields.Datetime.now(),
                'matches': result.get('matches', []),
            }
            
        except Exception as exc:
            _logger.exception('verify_face endpoint failed')
            return {
                'success': False,
                'error': f'Lỗi xác thực: {str(exc)}',
                'timestamp': fields.Datetime.now(),
            }
    
    
    @http.route(
        '/lms/face-gate/failed-attempt',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def log_failed_attempt(self, lesson_id=None, captured_image=None, reason=None, **kwargs):
        """
        Ghi nhận các lần cố gắng điểm danh thất bại (để audit trail)
        
        Request:
        {
            "lesson_id": 123,
            "captured_image": "base64...",
            "reason": "Không tìm thấy khuôn mặt phù hợp"
        }
        """
        try:
            captured_image = captured_image or kwargs.get('captured_image')
            lesson_id = lesson_id or kwargs.get('lesson_id')
            reason = reason or kwargs.get('reason', 'Unknown')
            
            if not all([captured_image, lesson_id]):
                return {'success': False, 'error': 'Thiếu dữ liệu'}
            
            try:
                lesson_id_int = int(lesson_id)
            except (ValueError, TypeError):
                return {'success': False, 'error': 'ID buổi học không hợp lệ'}
            
            image_bytes = _raw_image_file_bytes(captured_image)
            if not image_bytes:
                return {'success': False, 'error': 'Ảnh không hợp lệ'}
            
            env = request.env
            
            # Tạo record "thất bại" - không ghi student_id
            env['lms.face.attendance'].sudo().create({
                'lesson_id': lesson_id_int,
                'passed': False,
                'failure_reason': reason,
                'captured_image': image_bytes,
                'timestamp': fields.Datetime.now(),
            })
            
            return {'success': True, 'message': 'Đã ghi nhận lần cố gắng'}
            
        except Exception as exc:
            _logger.exception('log_failed_attempt failed')
            return {'success': False, 'error': str(exc)}


# ============================================================================
# HƯỚNG DẪN TÍCH HỢP
# ============================================================================

"""
1. Thêm code trên vào file: lms_face_gate/controllers/face_sample.py
   (trước class FaceSampleController)

2. Cập nhật requirements.txt - thêm scipy:
   pip install scipy

3. Thêm config parameter (res_config_settings.py):
   lms_face_gate_similarity_threshold = fields.Float(
       string='Face Similarity Threshold',
       default=0.6,
       help='0.0-1.0, higher = stricter matching'
   )

4. Test endpoint:
   curl -X POST http://localhost:8069/lms/face-gate/verify \
     -H "Content-Type: application/json" \
     -d '{
       "lesson_id": 1,
       "captured_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
     }'

5. Frontend sẽ gọi:
   - Upload sample: /lms/face-gate/upload-sample (POST, auth=user)
   - Verify: /lms/face-gate/verify (POST, auth=public)
   - Log failed: /lms/face-gate/failed-attempt (POST, auth=public)
"""
