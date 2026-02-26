# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Student(models.Model):
    _name = 'lms.student'
    _description = 'Sinh viên'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên sinh viên', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    
    @api.constrains('email')
    def _check_email(self):
        """Kiểm tra định dạng email"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValueError('Email không hợp lệ. Vui lòng nhập đúng định dạng email.')
    phone = fields.Char(string='Số điện thoại')
    image_1920 = fields.Image(string='Ảnh đại diện', max_width=1920, max_height=1920)
    
    # Thông tin đầu vào
    current_level = fields.Selection([
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], string='Trình độ hiện tại', default='beginner', required=True, tracking=True)
    
    learning_goals = fields.Text(string='Mục tiêu học tập', tracking=True)
    desired_skills = fields.Text(string='Kỹ năng mong muốn', tracking=True)
    
    # Quan hệ
    enrolled_courses_ids = fields.One2many(
        'lms.student.course', 'student_id', string='Khóa học đã đăng ký'
    )
    learning_history_ids = fields.One2many(
        'lms.learning.history', 'student_id', string='Lịch sử học tập'
    )
    roadmap_ids = fields.One2many(
        'lms.roadmap', 'student_id', string='Roadmap đề xuất'
    )
    mentor_id = fields.Many2one('lms.mentor', string='Mentor phụ trách')
    user_id = fields.Many2one('res.users', string='User Account', ondelete='cascade', index=True, tracking=True)
    
    # Thống kê
    total_courses = fields.Integer(string='Tổng số khóa học', compute='_compute_statistics', store=True)
    completed_courses = fields.Integer(string='Khóa học đã hoàn thành', compute='_compute_statistics', store=True)
    average_score = fields.Float(string='Điểm trung bình', compute='_compute_statistics', store=True, digits=(16, 2))
    total_study_time = fields.Float(string='Tổng thời gian học (giờ)', compute='_compute_statistics', store=True, digits=(16, 2))
    last_activity_date = fields.Date(string='Hoạt động cuối', compute='_compute_statistics', store=True, index=True)
    
    # Trạng thái
    is_active = fields.Boolean(string='Đang hoạt động', default=True, tracking=True)
    inactive_days = fields.Integer(string='Số ngày không hoạt động', compute='_compute_inactive_days', store=True, index=True)
    
    @api.depends('learning_history_ids.date', 'learning_history_ids.quiz_score', 'learning_history_ids.study_duration', 'enrolled_courses_ids', 'enrolled_courses_ids.status')
    def _compute_statistics(self):
        for record in self:
            record.total_courses = len(record.enrolled_courses_ids)
            record.completed_courses = len(record.enrolled_courses_ids.filtered(lambda x: x.status == 'completed'))
            
            # Tính điểm trung bình
            histories = record.learning_history_ids.filtered(lambda h: h.quiz_score)
            if histories:
                record.average_score = sum(histories.mapped('quiz_score')) / len(histories)
            else:
                record.average_score = 0.0
            
            # Tính tổng thời gian học
            record.total_study_time = sum(record.learning_history_ids.mapped('study_duration'))
            
            # Ngày hoạt động cuối
            if record.learning_history_ids:
                dates = record.learning_history_ids.mapped('date')
                # Lọc bỏ các giá trị None/False
                valid_dates = [d for d in dates if d]
                if valid_dates:
                    max_datetime = max(valid_dates)
                    # Chuyển đổi Datetime sang Date
                    if hasattr(max_datetime, 'date'):
                        record.last_activity_date = max_datetime.date()
                    else:
                        record.last_activity_date = max_datetime
                else:
                    record.last_activity_date = False
            else:
                record.last_activity_date = False
    
    @api.depends('last_activity_date')
    def _compute_inactive_days(self):
        """Tính số ngày không hoạt động và gửi email nhắc nhở nếu > 7 ngày"""
        today = fields.Date.today()
        for record in self:
            old_inactive_days = record.inactive_days
            if record.last_activity_date:
                record.inactive_days = (today - record.last_activity_date).days
            else:
                record.inactive_days = 0
            
            # Gửi email nhắc nhở nếu không hoạt động > 7 ngày (chỉ gửi 1 lần)
            if record.inactive_days > 7 and old_inactive_days <= 7 and record.email:
                template = self.env.ref('lms.email_template_inactive_reminder', raise_if_not_found=False)
                if template:
                    template.send_mail(record.id, force_send=True)
            
            # Gửi email cho mentor nếu học viên có nguy cơ (chỉ gửi 1 lần)
            if record.inactive_days > 7 and old_inactive_days <= 7 and record.mentor_id and record.mentor_id.user_id and record.mentor_id.user_id.email:
                template = self.env.ref('lms.email_template_student_at_risk', raise_if_not_found=False)
                if template:
                    template.send_mail(record.id, force_send=True)
    
    def action_generate_roadmap(self):
        """Tạo roadmap đề xuất cho sinh viên"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo Roadmap',
            'res_model': 'lms.roadmap.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_student_id': self.id},
        }


class StudentCourse(models.Model):
    _name = 'lms.student.course'
    _description = 'Khóa học của sinh viên'
    _rec_name = 'course_id'

    student_id = fields.Many2one('lms.student', string='Sinh viên', required=True, ondelete='cascade')
    course_id = fields.Many2one('lms.course', string='Khóa học', required=True)
    
    enrollment_date = fields.Date(string='Ngày đăng ký', default=fields.Date.today, required=True)
    start_date = fields.Date(string='Ngày bắt đầu')
    completion_date = fields.Date(string='Ngày hoàn thành')
    
    status = fields.Selection([
        ('enrolled', 'Đã đăng ký'),
        ('in_progress', 'Đang học'),
        ('completed', 'Đã hoàn thành'),
        ('dropped', 'Bỏ cuộc'),
    ], string='Trạng thái', default='enrolled', tracking=True)
    
    progress = fields.Float(string='Tiến độ (%)', compute='_compute_progress', store=True, digits=(16, 2))
    final_score = fields.Float(string='Điểm cuối cùng', digits=(16, 2))
    
    @api.depends('learning_history_ids', 'learning_history_ids.status', 'course_id', 'course_id.lesson_ids')
    def _compute_progress(self):
        for record in self:
            if record.course_id:
                total_lessons = len(record.course_id.lesson_ids)
                completed_lessons = len(record.learning_history_ids.filtered(
                    lambda h: h.lesson_id.course_id == record.course_id and h.status == 'completed'
                ))
                if total_lessons > 0:
                    record.progress = (completed_lessons / total_lessons) * 100
                else:
                    record.progress = 0.0
            else:
                record.progress = 0.0
    
    learning_history_ids = fields.One2many(
        'lms.learning.history', 'student_course_id', string='Lịch sử học tập'
    )


