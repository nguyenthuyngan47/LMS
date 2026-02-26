# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

from .base_controller import make_json_response, handle_cors_preflight

_logger = logging.getLogger(__name__)


class AuthController(http.Controller):

    @http.route('/lms/api/login', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def login(self, **kwargs):
        """API endpoint để đăng nhập (public, không cần auth)"""
        # Xử lý OPTIONS request (CORS preflight)
        if request.httprequest.method == 'OPTIONS':
            return handle_cors_preflight(
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type',
            )
        
        try:
            # Đọc JSON từ request body
            data = json.loads(request.httprequest.data.decode('utf-8'))
            if isinstance(data, dict) and 'params' in data:
                # JSON-RPC format từ Flutter
                data = data['params']
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            database = data.get('database', 'odoo')
            
            # Validation
            if not email or '@' not in email:
                return make_json_response({
                    'success': False,
                    'message': 'Email không hợp lệ'
                }, allow_methods='POST, OPTIONS', allow_headers='Content-Type')
            
            if not password:
                return make_json_response({
                    'success': False,
                    'message': 'Vui lòng nhập mật khẩu'
                }, allow_methods='POST, OPTIONS', allow_headers='Content-Type')
            
            # Authenticate với Odoo: Tìm user và verify password
            user = request.env['res.users'].sudo().search([
                ('login', '=', email),
            ], limit=1)
            
            if not user:
                _logger.warning(f'User not found: {email}')
                uid = False
            elif not user.active:
                _logger.warning(f'User is inactive: {email} (UID: {user.id})')
                uid = False
            else:
                _logger.info(f'User found: {user.name} (UID: {user.id}), verifying password...')
                # Verify password - thử nhiều cách
                uid = False
                
                # Cách 1: Dùng _check_credentials (cách đúng nhất)
                try:
                    user._check_credentials(password)
                    uid = user.id
                    _logger.info(f'✅ Password verified successfully using _check_credentials')
                except Exception as e1:
                    _logger.warning(f'_check_credentials failed: {str(e1)}, trying crypt_context...')
                    
                    # Cách 2: Dùng crypt_context verify
                    try:
                        crypt_context = user._crypt_context()
                        if crypt_context and user.password_crypt:
                            is_valid = crypt_context.verify(password, user.password_crypt)
                            if is_valid:
                                uid = user.id
                                _logger.info(f'✅ Password verified successfully using crypt_context')
                            else:
                                _logger.error(f'❌ Password verification failed: password does not match hash')
                        else:
                            _logger.error(f'❌ User {user.id} has no password_crypt or crypt_context')
                    except Exception as e2:
                        _logger.error(f'❌ Crypt context verify also failed: {str(e2)}')
                
                if not uid:
                    _logger.error(f'❌ All password verification methods failed for user {user.id}')
            
            if uid:
                # Lấy thông tin user từ res.users
                user = request.env['res.users'].sudo().browse(uid)
                
                # Lấy thông tin student từ user_id (ưu tiên) hoặc email (fallback)
                student = request.env['lms.student'].sudo().search([
                    ('user_id', '=', uid)
                ], limit=1)
                
                # Fallback: Tìm theo email nếu không tìm thấy qua user_id
                if not student:
                    student = request.env['lms.student'].sudo().search([
                        ('email', '=', email)
                    ], limit=1)
                    # Nếu tìm thấy qua email, link với user_id
                    if student and not student.user_id:
                        student.sudo().write({'user_id': uid})
                        _logger.info(f'Linked student {student.id} with user {uid}')
                
                # Trả về thông tin user từ res.users
                result = {
                    'success': True,
                    'uid': uid,
                    'message': 'Đăng nhập thành công',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email or user.login,
                        'login': user.login,
                        'partner_id': user.partner_id.id if user.partner_id else None,
                    }
                }
                
                # Thêm thông tin student nếu có
                if student:
                    result['student'] = {
                        'id': student.id,
                        'name': student.name,
                        'email': student.email,
                        'phone': student.phone or '',
                        'current_level': student.current_level,
                        'learning_goals': student.learning_goals or '',
                        'desired_skills': student.desired_skills or '',
                        'total_courses': student.total_courses,
                        'completed_courses': student.completed_courses,
                        'average_score': student.average_score,
                        'is_active': student.is_active,
                        'user_id': student.user_id.id if student.user_id else None,
                    }
                    _logger.info(f'Login successful: {email} (UID: {uid}, Student ID: {student.id})')
                else:
                    _logger.warning(f'Login successful but no student found for {email} (UID: {uid})')
                    result['student'] = None
            else:
                result = {
                    'success': False,
                    'message': 'Email hoặc mật khẩu không đúng'
                }
                _logger.warning(f'Login failed: {email}')
            
            return make_json_response(
                result,
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type',
            )
            
        except Exception as e:
            _logger.error(f'Login error: {str(e)}', exc_info=True)
            return make_json_response(
                {
                    'success': False,
                    'message': f'Lỗi đăng nhập: {str(e)}'
                },
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type',
            )

    @http.route('/lms/api/register', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def register(self, **kwargs):
        """API endpoint để đăng ký tài khoản mới (public, không cần auth)"""
        # Xử lý OPTIONS request (CORS preflight)
        if request.httprequest.method == 'OPTIONS':
            return handle_cors_preflight(
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type',
            )
        
        try:
            # Đọc JSON từ request body
            data = json.loads(request.httprequest.data.decode('utf-8'))
            if isinstance(data, dict) and 'params' in data:
                # JSON-RPC format từ Flutter
                data = data['params']
            
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            phone = data.get('phone', '').strip()
            current_level = data.get('current_level', 'beginner')
            
            # Validation
            if not name or len(name) < 2:
                return make_json_response({
                    'success': False,
                    'message': 'Họ và tên phải có ít nhất 2 ký tự'
                }, allow_methods='POST, OPTIONS', allow_headers='Content-Type')
            
            if not email or '@' not in email:
                return make_json_response({
                    'success': False,
                    'message': 'Email không hợp lệ'
                }, allow_methods='POST, OPTIONS', allow_headers='Content-Type')
            
            if not password or len(password) < 6:
                return make_json_response({
                    'success': False,
                    'message': 'Mật khẩu phải có ít nhất 6 ký tự'
                }, allow_methods='POST, OPTIONS', allow_headers='Content-Type')
            
            if current_level not in ['beginner', 'intermediate', 'advanced']:
                current_level = 'beginner'
            
            # Kiểm tra email đã tồn tại chưa
            existing_user = request.env['res.users'].sudo().search([
                ('login', '=', email)
            ], limit=1)
            
            if existing_user:
                return make_json_response({
                    'success': False,
                    'message': 'Email này đã được sử dụng'
                }, allow_methods='POST, OPTIONS', allow_headers='Content-Type')
            
            existing_student = request.env['lms.student'].sudo().search([
                ('email', '=', email)
            ], limit=1)
            
            if existing_student:
                return make_json_response({
                    'success': False,
                    'message': 'Email này đã được sử dụng'
                }, allow_methods='POST, OPTIONS', allow_headers='Content-Type')
            
            # Tạo partner
            partner = request.env['res.partner'].sudo().create({
                'name': name,
                'email': email,
                'phone': phone,
                'is_company': False,
            })
            
            # Tìm group Student
            student_group = request.env['res.groups'].sudo().search([
                ('category_id.name', '=', 'LMS'),
                ('name', 'ilike', 'Student')
            ], limit=1)
            
            # Tạo user
            user_vals = {
                'name': name,
                'login': email,
                'email': email,
                'partner_id': partner.id,
            }
            
            if student_group:
                user_vals['groups_id'] = [(6, 0, [student_group.id])]
            
            # Tạo user TRƯỚC (không set password trong create)
            user = request.env['res.users'].sudo().with_context(no_reset_password=True).create(user_vals)
            _logger.info(f'User created: {user.id} (email: {email})')
            
            # Set password SAU KHI tạo user
            # Dùng cách đơn giản nhất: hash password và set trực tiếp vào password_crypt
            password_set = False
            try:
                # Lấy crypt_context từ user
                crypt_context = user._crypt_context()
                if not crypt_context:
                    raise Exception("Cannot get crypt_context")
                
                # Hash password
                hashed = crypt_context.hash(password)
                _logger.info(f'Password hashed successfully, length: {len(hashed)}')
                
                # Set password_crypt trực tiếp (cách đơn giản và chắc chắn nhất)
                user.sudo().write({'password_crypt': hashed})
                
                # Invalidate cache và refresh
                user.invalidate_recordset(['password_crypt'])
                user.refresh()
                
                # Verify password đã được set
                if user.password_crypt and user.password_crypt == hashed:
                    password_set = True
                    _logger.info(f'✅ Password set successfully using crypt_context.hash for user {user.id}')
                else:
                    raise Exception(f"password_crypt mismatch. Expected length: {len(hashed)}, Got: {len(user.password_crypt) if user.password_crypt else 0}")
                    
            except Exception as e:
                _logger.error(f"crypt_context.hash failed: {str(e)}, trying _set_password...")
                try:
                    # Fallback: Dùng _set_password (có thể không hoạt động với sudo user)
                    # Tạo user record mới không dùng sudo để set password
                    user_without_sudo = request.env['res.users'].browse(user.id)
                    user_without_sudo._set_password(password)
                    user.invalidate_recordset(['password_crypt'])
                    user.refresh()
                    
                    if user.password_crypt:
                        password_set = True
                        _logger.info(f'✅ Password set using _set_password for user {user.id}')
                    else:
                        raise Exception("password_crypt is still empty after _set_password")
                except Exception as e2:
                    _logger.error(f"_set_password also failed: {str(e2)}")
                    # Thử cách cuối: write với password field
                    try:
                        user.sudo().with_context(no_reset_password=True).write({'password': password})
                        user.invalidate_recordset(['password_crypt'])
                        user.refresh()
                        if user.password_crypt:
                            password_set = True
                            _logger.info(f'✅ Password set using write with password field for user {user.id}')
                        else:
                            raise Exception("password_crypt is still empty")
                    except Exception as e3:
                        _logger.error(f"All password setting methods failed: {str(e3)}")
                        _logger.error(f"❌ User {user.id} created but password NOT set correctly!")
            
            # Verify password có thể dùng để login (QUAN TRỌNG)
            if password_set:
                try:
                    # Refresh user để đảm bảo có password_crypt mới nhất
                    user.refresh()
                    # Test với _check_credentials
                    user._check_credentials(password)
                    _logger.info(f'✅ Password verified successfully - ready for login')
                except Exception as e:
                    _logger.error(f'❌ Password verification failed after setting: {str(e)}')
                    _logger.warning(f'⚠️ Password may not work for login!')
                    # Log thêm thông tin debug
                    _logger.info(f'Debug: user.password_crypt exists: {bool(user.password_crypt)}')
                    _logger.info(f'Debug: user.password_crypt length: {len(user.password_crypt) if user.password_crypt else 0}')
                    _logger.info(f'Debug: user.password_crypt preview: {user.password_crypt[:20] if user.password_crypt else "None"}...')
                    # Đánh dấu password_set = False để trả về lỗi
                    password_set = False
            else:
                _logger.error(f'❌ ERROR: Password was NOT set for user {user.id} (email: {email})')
                # Xóa user vừa tạo vì password không được set (để user có thể đăng ký lại)
                try:
                    # Xóa student trước (nếu có)
                    student = request.env['lms.student'].sudo().search([('user_id', '=', user.id)], limit=1)
                    if student:
                        student.sudo().unlink()
                        _logger.info(f'Deleted student {student.id} linked to user {user.id}')
                    
                    # Xóa user
                    user.sudo().unlink()
                    _logger.info(f'Deleted user {user.id} because password was not set')
                except Exception as e:
                    _logger.error(f'Failed to delete user {user.id}: {str(e)}')
                
                # Trả về lỗi cho Flutter với message rõ ràng
                return make_json_response(
                    {
                        'success': False,
                        'message': 'Không thể tạo mật khẩu. Vui lòng thử lại hoặc liên hệ admin để được hỗ trợ.'
                    },
                    allow_methods='POST, OPTIONS',
                    allow_headers='Content-Type',
                )
            
            # Tạo student record và link với user_id
            student = request.env['lms.student'].sudo().create({
                'name': name,
                'email': email,
                'phone': phone,
                'current_level': current_level,
                'is_active': True,
                'user_id': user.id,  # Link student với user
            })
            
            _logger.info(f'User registered successfully: {email} (User ID: {user.id}, Student ID: {student.id})')
            
            result = {
                'success': True,
                'message': 'Đăng ký thành công',
                'user_id': user.id,
                'student_id': student.id,
            }
            
            return make_json_response(
                result,
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type',
            )
            
        except Exception as e:
            _logger.error(f'Registration error: {str(e)}', exc_info=True)
            return make_json_response(
                {
                    'success': False,
                    'message': f'Lỗi đăng ký: {str(e)}'
                },
                allow_methods='POST, OPTIONS',
                allow_headers='Content-Type',
            )
