# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json

from .base_controller import make_json_response, handle_cors_preflight


class QuizController(http.Controller):

    @http.route('/lms/api/quiz/<int:lesson_id>', type='http', auth='user', methods=['GET', 'POST', 'OPTIONS'], csrf=False)
    def get_quiz(self, lesson_id, **kwargs):
        """API endpoint để lấy danh sách quiz của một lesson (cho mobile app)"""
        # Xử lý OPTIONS request (CORS preflight)
        if request.httprequest.method == 'OPTIONS':
            return handle_cors_preflight(
                allow_methods='GET, POST, OPTIONS',
                allow_headers='Content-Type, Authorization',
            )
        
        try:
            lesson = request.env['lms.lesson'].browse(lesson_id)
            if not lesson.exists():
                result = {
                    'success': False,
                    'message': 'Bài học không tồn tại'
                }
                return make_json_response(
                    result,
                    allow_methods='GET, POST, OPTIONS',
                    allow_headers='Content-Type, Authorization',
                )
            
            # Kiểm tra quyền truy cập
            student = request.env['lms.student'].search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            
            if not student:
                result = {
                    'success': False,
                    'message': 'Bạn cần là sinh viên để làm quiz'
                }
                return make_json_response(
                    result,
                    allow_methods='GET, POST, OPTIONS',
                    allow_headers='Content-Type, Authorization',
                )
            
            # Kiểm tra sinh viên có đăng ký khóa học này không
            student_course = request.env['lms.student.course'].search([
                ('student_id', '=', student.id),
                ('course_id', '=', lesson.course_id.id)
            ], limit=1)
            
            if not student_course:
                result = {
                    'success': False,
                    'message': 'Bạn chưa đăng ký khóa học này'
                }
                return make_json_response(
                    result,
                    allow_methods='GET, POST, OPTIONS',
                    allow_headers='Content-Type, Authorization',
                )
            
            quizzes = lesson.quiz_ids.sorted('sequence')
            
            # Chuẩn bị dữ liệu quiz với options đã parse
            quiz_data = []
            for quiz in quizzes:
                quiz_info = {
                    'id': quiz.id,
                    'name': quiz.name,
                    'sequence': quiz.sequence,
                    'question_type': quiz.question_type,
                    'points': quiz.points,
                    'options': quiz.get_options_list() if quiz.question_type == 'multiple_choice' else [],
                }
                quiz_data.append(quiz_info)
            
            result = {
                'success': True,
                'lesson': {
                    'id': lesson.id,
                    'name': lesson.name,
                    'course_id': lesson.course_id.id,
                    'course_name': lesson.course_id.name,
                },
                'quizzes': quiz_data,
                'total_questions': len(quiz_data),
                'total_points': sum(q.points for q in quizzes),
            }

            return make_json_response(
                result,
                allow_methods='GET, POST, OPTIONS',
                allow_headers='Content-Type, Authorization',
            )
            
        except Exception as e:
            result = {
                'success': False,
                'message': f'Lỗi: {str(e)}'
            }
            return make_json_response(
                result,
                allow_methods='GET, POST, OPTIONS',
                allow_headers='Content-Type, Authorization',
            )
    
    @http.route('/lms/api/quiz/submit', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False)
    def submit_quiz(self, **kwargs):
        """Xử lý submit quiz và tính điểm"""
        # Xử lý OPTIONS request (CORS preflight)
        if request.httprequest.method == 'OPTIONS':
            return handle_cors_preflight(
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type, Authorization',
            )
        
        try:
            # Đọc JSON từ request body
            data = json.loads(request.httprequest.data.decode('utf-8'))
            if isinstance(data, dict) and 'params' in data:
                # JSON-RPC format từ Flutter
                data = data['params']
            
            lesson_id = data.get('lesson_id')
            answers = data.get('answers', {})
            
            if not lesson_id:
                result = {
                    'success': False,
                    'message': 'Thiếu lesson_id'
                }
                return make_json_response(
                    result,
                    allow_methods='POST, OPTIONS',
                    allow_headers='Content-Type, Authorization',
                )
            
            lesson = request.env['lms.lesson'].browse(lesson_id)
            if not lesson.exists():
                result = {
                    'success': False,
                    'message': 'Bài học không tồn tại'
                }
                return make_json_response(
                    result,
                    allow_methods='POST, OPTIONS',
                    allow_headers='Content-Type, Authorization',
                )
            
            # Kiểm tra quyền truy cập
            student = request.env['lms.student'].search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            
            if not student:
                result = {
                    'success': False,
                    'message': 'Bạn cần là sinh viên để làm quiz'
                }
                return make_json_response(
                    result,
                    allow_methods='POST, OPTIONS',
                    allow_headers='Content-Type, Authorization',
                )
            
            # Lấy tất cả quiz của lesson
            quizzes = lesson.quiz_ids.sorted('sequence')
            
            # Tính điểm
            total_score = 0
            max_score = 0
            results = []
            
            for quiz in quizzes:
                max_score += quiz.points
                user_answer = answers.get(str(quiz.id), '')
                is_correct = quiz.check_answer(user_answer)
                
                if is_correct:
                    total_score += quiz.points
                
                results.append({
                    'quiz_id': quiz.id,
                    'question': quiz.name,
                    'user_answer': user_answer,
                    'correct_answer': quiz.correct_answer,
                    'is_correct': is_correct,
                    'points': quiz.points if is_correct else 0,
                })
            
            # Tính phần trăm
            score_percentage = (total_score / max_score * 100) if max_score > 0 else 0
            
            # Tìm hoặc tạo student_course
            student_course = request.env['lms.student.course'].search([
                ('student_id', '=', student.id),
                ('course_id', '=', lesson.course_id.id)
            ], limit=1)
            
            if not student_course:
                student_course = request.env['lms.student.course'].create({
                    'student_id': student.id,
                    'course_id': lesson.course_id.id,
                    'status': 'in_progress',
                })
            
            # Tạo hoặc cập nhật learning history
            learning_history = request.env['lms.learning.history'].search([
                ('student_id', '=', student.id),
                ('lesson_id', '=', lesson_id),
            ], limit=1)
            
            if learning_history:
                learning_history.write({
                    'quiz_score': total_score,
                    'max_score': max_score,
                    'status': 'completed',
                })
            else:
                learning_history = request.env['lms.learning.history'].create({
                    'student_id': student.id,
                    'student_course_id': student_course.id,
                    'lesson_id': lesson_id,
                    'quiz_score': total_score,
                    'max_score': max_score,
                    'status': 'completed',
                })
            
            result = {
                'success': True,
                'total_score': total_score,
                'max_score': max_score,
                'score_percentage': round(score_percentage, 2),
                'results': results,
                'learning_history_id': learning_history.id,
                'message': f'Bạn đã hoàn thành quiz với điểm số {total_score}/{max_score} ({score_percentage:.1f}%)',
                'passed': score_percentage >= 50,  # Đạt nếu >= 50%
            }

            return make_json_response(
                result,
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type, Authorization',
            )
            
        except Exception as e:
            result = {
                'success': False,
                'message': f'Lỗi: {str(e)}'
            }
            return make_json_response(
                result,
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type, Authorization',
            )
