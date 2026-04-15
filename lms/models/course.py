# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class CourseCategory(models.Model):
    _name = 'lms.course.category'
    _description = 'Danh mục khóa học'
    _order = 'sequence, name'

    name = fields.Char(string='Tên danh mục', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    description = fields.Text(string='Mô tả')
    course_ids = fields.One2many('lms.course', 'category_id', string='Khóa học')


class CourseLevel(models.Model):
    _name = 'lms.course.level'
    _description = 'Cấp độ khóa học'
    _order = 'sequence, name'

    name = fields.Char(string='Tên cấp độ', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    description = fields.Text(string='Mô tả')
    course_ids = fields.One2many('lms.course', 'level_id', string='Khóa học')


class CourseTag(models.Model):
    _name = 'lms.course.tag'
    _description = 'Nhãn khóa học'
    _order = 'name'

    name = fields.Char(string='Tên nhãn', required=True)
    color = fields.Integer(string='Màu sắc')
    course_ids = fields.Many2many('lms.course', 'course_tag_rel', 'tag_id', 'course_id', string='Khóa học')


class Course(models.Model):
    _name = 'lms.course'
    _description = 'Khóa học'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên khóa học', required=True, tracking=True)
    # mail.tracking không hỗ trợ field Html, chỉ giữ hiển thị nội dung.
    description = fields.Html(string='Mô tả')
    image_1920 = fields.Image(string='Ảnh khóa học', max_width=1920, max_height=1920)
    
    # Phân loại
    category_id = fields.Many2one('lms.course.category', string='Danh mục', required=True, tracking=True)
    level_id = fields.Many2one('lms.course.level', string='Cấp độ', required=True, tracking=True)
    tag_ids = fields.Many2many('lms.course.tag', 'course_tag_rel', 'course_id', 'tag_id', string='Nhãn')
    
    # Thông tin khóa học
    instructor_id = fields.Many2one('res.users', string='Giảng viên', tracking=True)
    duration_hours = fields.Float(string='Thời lượng (giờ)', digits=(16, 2), tracking=True)
    max_student = fields.Integer(string='Số học viên tối đa')
    start_date = fields.Date(string='Ngày bắt đầu')
    end_date = fields.Date(string='Ngày kết thúc')
    price = fields.Float(string='Chi phí', digits=(16, 2), tracking=True)
    contact_payment = fields.Text(string='Liên hệ giáo viên', tracking=True)
    prerequisite_ids = fields.Many2many(
        'lms.course', 'course_prerequisite_rel', 'course_id', 'prerequisite_id',
        string='Khóa học tiên quyết'
    )
    
    # Nội dung
    lesson_ids = fields.One2many('lms.lesson', 'course_id', string='Bài học')
    total_lessons = fields.Integer(string='Tổng số bài học', compute='_compute_total_lessons', store=True)
    
    # Thống kê
    enrolled_students_count = fields.Integer(string='Số học viên đăng ký', compute='_compute_enrolled_students', store=True)
    average_rating = fields.Float(string='Đánh giá trung bình', digits=(16, 2))
    show_register_button = fields.Boolean(
        string='Hiển thị nút đăng ký',
        compute='_compute_current_user_registration_state',
    )
    show_cancel_button = fields.Boolean(
        string='Hiển thị nút hủy đăng ký',
        compute='_compute_current_user_registration_state',
    )
    show_learning_content_tabs = fields.Boolean(
        string='Hiển thị tab học tập',
        compute='_compute_current_user_registration_state',
    )
    is_student_course_readonly = fields.Boolean(
        string='Form khóa học chỉ đọc (học sinh)',
        compute='_compute_is_student_course_readonly',
    )

    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('published', 'Đã xuất bản'),
        ('archived', 'Lưu trữ'),
    ], string='Trạng thái', default='draft', tracking=True)
    
    is_active = fields.Boolean(string='Đang hoạt động', default=True)

    @api.model
    def default_get(self, fields_list):
        """Giáo viên (không phải Admin LMS/Settings) tạo khóa mới: mặc định instructor là chính họ (cần cho ir.rule ghi)."""
        res = super().default_get(fields_list)
        if 'instructor_id' in fields_list and not res.get('instructor_id'):
            user = self.env.user
            if user.has_group('lms.group_lms_instructor') and not (
                user.has_group('lms.group_lms_manager') or user.has_group('base.group_system')
            ):
                res['instructor_id'] = user.id
        return res

    @api.constrains('duration_hours')
    def _check_duration_hours(self):
        """Kiểm tra thời lượng khóa học không được âm"""
        for record in self:
            if record.duration_hours and record.duration_hours < 0:
                raise ValueError('Thời lượng khóa học không được âm')
    
    @api.constrains('prerequisite_ids')
    def _check_prerequisite_cycle(self):
        """Kiểm tra prerequisite không được tạo vòng lặp"""
        for record in self:
            if record.id in record.prerequisite_ids.ids:
                raise ValueError('Khóa học không thể là prerequisite của chính nó')
            # Kiểm tra vòng lặp gián tiếp (đệ quy)
            visited = set()
            to_check = list(record.prerequisite_ids.ids)
            while to_check:
                prereq_id = to_check.pop()
                if prereq_id == record.id:
                    raise ValueError('Phát hiện vòng lặp trong prerequisite. Khóa học không thể có prerequisite dẫn đến chính nó.')
                if prereq_id in visited:
                    continue
                visited.add(prereq_id)
                prereq_course = self.browse(prereq_id)
                if prereq_course.exists():
                    to_check.extend(prereq_course.prerequisite_ids.ids)
    
    @api.depends('lesson_ids')
    def _compute_total_lessons(self):
        for record in self:
            record.total_lessons = len(record.lesson_ids)
    
    @api.depends('student_course_ids')
    def _compute_enrolled_students(self):
        for record in self:
            record.enrolled_students_count = len(record.student_course_ids)

    @api.depends('state')
    def _compute_current_user_registration_state(self):
        """Điều khiển hiển thị nút đăng ký/hủy theo user hiện tại trên form course."""
        user = self.env.user
        is_admin_user = user.has_group('base.group_system') or user.has_group('lms.group_lms_manager')
        is_instructor_user = user.has_group('lms.group_lms_instructor')
        is_student_user = user.has_group('lms.group_lms_user')

        if is_admin_user:
            for record in self:
                record.show_register_button = False
                record.show_cancel_button = False
                record.show_learning_content_tabs = True
            return

        if is_instructor_user and not is_student_user:
            for record in self:
                record.show_register_button = False
                record.show_cancel_button = False
                record.show_learning_content_tabs = bool(record.instructor_id and record.instructor_id.id == user.id)
            return

        if not is_student_user:
            for record in self:
                record.show_register_button = False
                record.show_cancel_button = False
                record.show_learning_content_tabs = False
            return

        student = self.env['lms.student'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not student:
            for record in self:
                record.show_register_button = False
                record.show_cancel_button = False
                record.show_learning_content_tabs = False
            return

        enrolled_ids = set(
            self.env['lms.student.course'].sudo().search([
                ('student_id', '=', student.id),
                ('course_id', 'in', self.ids),
                ('status', '!=', 'cancelled'),
            ]).mapped('course_id').ids
        )
        for record in self:
            is_enrolled = record.id in enrolled_ids
            record.show_register_button = not is_enrolled
            record.show_cancel_button = is_enrolled
            approved_or_learning = self.env['lms.student.course'].sudo().search_count(
                [
                    ('student_id', '=', student.id),
                    ('course_id', '=', record.id),
                    ('status', 'in', ['approved', 'learning']),
                ]
            )
            record.show_learning_content_tabs = bool(approved_or_learning)

    @api.depends()
    def _compute_is_student_course_readonly(self):
        """Chỉ tài khoản thuần học sinh (không phải GV/Admin) — không chỉnh sửa dữ liệu khóa học."""
        user = self.env.user
        readonly = user.has_group('lms.group_lms_user') and not (
            user.has_group('lms.group_lms_instructor')
            or user.has_group('lms.group_lms_manager')
            or user.has_group('base.group_system')
        )
        for record in self:
            record.is_student_course_readonly = readonly

    student_course_ids = fields.One2many('lms.student.course', 'course_id', string='Học viên đăng ký')
    
    def action_publish(self):
        """Xuất bản khóa học"""
        self.write({'state': 'published'})
        return True

    def action_register_courses(self):
        """
        Đăng ký 1 hoặc nhiều khóa học cho user đang đăng nhập.
        Dùng chung cho form (1 khóa) và list action (nhiều khóa).
        """
        user = self.env.user
        if not user.has_group('lms.group_lms_user'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Đăng ký khóa học'),
                    'message': _('Chỉ tài khoản học sinh mới được đăng ký khóa học.'),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                },
            }

        student = self.env['lms.student'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not student:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Đăng ký khóa học'),
                    'message': _('Tài khoản của bạn chưa liên kết hồ sơ sinh viên.'),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                },
            }

        StudentCourse = self.env['lms.student.course'].sudo()
        created_names = []
        duplicate_names = []
        blocked_names = []

        for course in self:
            # Chỉ cho đăng ký khóa học đang hoạt động và đã xuất bản.
            if course.state != 'published' or not course.is_active:
                blocked_names.append(course.name)
                continue
            existed = StudentCourse.search(
                [('student_id', '=', student.id), ('course_id', '=', course.id)],
                limit=1,
            )
            if existed:
                duplicate_names.append(course.name)
                continue
            StudentCourse.create(
                {
                    'student_id': student.id,
                    'course_id': course.id,
                    'status': 'pending',
                    'enrollment_date': fields.Date.today(),
                    'final_score': False,
                }
            )
            created_names.append(course.name)

        lines = []
        if created_names:
            lines.append(_('Đăng ký thành công: %s') % ', '.join(created_names))
        if duplicate_names:
            for name in duplicate_names:
                lines.append(_('Bạn đã đăng ký khóa học %s rồi') % name)
        if blocked_names:
            lines.append(
                _('Không thể đăng ký (chưa xuất bản hoặc không hoạt động): %s')
                % ', '.join(blocked_names)
            )
        if not lines:
            lines.append(_('Không có khóa học nào được xử lý.'))

        notif_type = 'success' if created_names and not (duplicate_names or blocked_names) else 'warning'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đăng ký khóa học'),
                'message': '\n'.join(lines),
                'type': notif_type,
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }

    def action_cancel_course_registration(self):
        """Hủy đăng ký bằng cách xóa bản ghi enrollment hiện tại."""
        self.ensure_one()
        student = self.env['lms.student'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        enrollments = self.env['lms.student.course'].sudo().search([
            ('student_id', '=', student.id),
            ('course_id', '=', self.id),
        ])
        enrollments.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hủy đăng ký'),
                'message': _('Đã hủy đăng ký khóa học %s.') % self.name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }


class Lesson(models.Model):
    _name = 'lms.lesson'
    _description = 'Bài học'
    _order = 'sequence, name'

    name = fields.Char(string='Tên bài học', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10, required=True)
    description = fields.Html(string='Mô tả')
    
    course_id = fields.Many2one('lms.course', string='Khóa học', required=True, ondelete='cascade')
    
    # Tài liệu học
    video_url = fields.Char(string='Link video')
    video_attachment = fields.Binary(string='File video', attachment=True)
    pdf_attachment = fields.Binary(string='File PDF', attachment=True)
    pdf_filename = fields.Char(string='Tên file PDF')

    # Thời lượng
    duration_minutes = fields.Integer(string='Thời lượng (phút)')

