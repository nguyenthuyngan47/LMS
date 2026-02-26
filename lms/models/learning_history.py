# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LearningHistory(models.Model):
    _name = 'lms.learning.history'
    _description = 'Lịch sử học tập'
    _order = 'date desc, create_date desc'

    student_id = fields.Many2one('lms.student', string='Sinh viên', required=True, ondelete='cascade', index=True)
    student_course_id = fields.Many2one('lms.student.course', string='Khóa học của sinh viên', ondelete='cascade')
    course_id = fields.Many2one('lms.course', string='Khóa học', related='student_course_id.course_id', store=True)
    lesson_id = fields.Many2one('lms.lesson', string='Bài học', required=True, ondelete='cascade')
    
    date = fields.Datetime(string='Ngày học', default=fields.Datetime.now, required=True, index=True)
    study_duration = fields.Float(string='Thời gian học (giờ)', digits=(16, 2), default=0.0)
    
    # Trạng thái
    status = fields.Selection([
        ('started', 'Đã bắt đầu'),
        ('in_progress', 'Đang học'),
        ('completed', 'Đã hoàn thành'),
        ('skipped', 'Bỏ qua'),
    ], string='Trạng thái', default='started', required=True, tracking=True)
    
    # Điểm số
    quiz_score = fields.Float(string='Điểm quiz', digits=(16, 2))
    max_score = fields.Float(string='Điểm tối đa', digits=(16, 2))
    score_percentage = fields.Float(string='Tỷ lệ điểm (%)', compute='_compute_score_percentage', digits=(16, 2))
    
    # Dấu hiệu học kém
    is_low_performance = fields.Boolean(string='Học kém', compute='_compute_is_low_performance')
    is_at_risk = fields.Boolean(string='Có nguy cơ bỏ cuộc', compute='_compute_is_at_risk')
    
    notes = fields.Text(string='Ghi chú')
    
    @api.constrains('quiz_score', 'max_score')
    def _check_quiz_score(self):
        """Kiểm tra điểm quiz không được vượt quá điểm tối đa"""
        for record in self:
            if record.quiz_score and record.max_score:
                if record.quiz_score > record.max_score:
                    raise ValueError(f'Điểm quiz ({record.quiz_score}) không được vượt quá điểm tối đa ({record.max_score})')
                if record.quiz_score < 0:
                    raise ValueError('Điểm quiz không được âm')
            if record.max_score and record.max_score < 0:
                raise ValueError('Điểm tối đa không được âm')
    
    @api.constrains('study_duration')
    def _check_study_duration(self):
        """Kiểm tra thời gian học không được âm"""
        for record in self:
            if record.study_duration and record.study_duration < 0:
                raise ValueError('Thời gian học không được âm')
    
    @api.depends('quiz_score', 'max_score')
    def _compute_score_percentage(self):
        for record in self:
            if record.max_score and record.max_score > 0:
                record.score_percentage = (record.quiz_score / record.max_score) * 100
            else:
                record.score_percentage = 0.0
    
    @api.depends('score_percentage')
    def _compute_is_low_performance(self):
        for record in self:
            old_value = record.is_low_performance
            record.is_low_performance = record.score_percentage < 50.0 if record.score_percentage else False
            # Gửi email cảnh báo nếu điểm thấp (chỉ gửi 1 lần khi chuyển từ False sang True)
            if record.is_low_performance and not old_value and record.student_id.email:
                template = self.env.ref('lms.email_template_low_performance', raise_if_not_found=False)
                if template:
                    template.send_mail(record.id, force_send=True)
    
    @api.depends('student_id', 'date', 'score_percentage')
    def _compute_is_at_risk(self):
        for record in self:
            # Kiểm tra nếu điểm thấp hoặc không hoạt động > 7 ngày
            is_low_score = record.score_percentage < 50.0 if record.score_percentage else False
            
            # Kiểm tra ngày không hoạt động - tính từ date của chính record này
            is_inactive = False
            if record.student_id and record.date:
                try:
                    today = fields.Date.today()
                    # Chuyển đổi Datetime sang Date để so sánh
                    record_date = record.date
                    if hasattr(record_date, 'date'):
                        record_date = record_date.date()
                    
                    days_inactive = (today - record_date).days
                    is_inactive = days_inactive > 7
                except (TypeError, AttributeError, ValueError):
                    is_inactive = False
            
            record.is_at_risk = is_low_score or is_inactive
    
    def action_mark_completed(self):
        """Đánh dấu bài học đã hoàn thành"""
        self.write({'status': 'completed'})
        return True
    
    @api.model
    def create_learning_record(self, student_id, lesson_id, duration=0.0):
        """Tạo bản ghi học tập"""
        student_course = self.env['lms.student.course'].search([
            ('student_id', '=', student_id),
            ('course_id', '=', lesson_id.course_id.id)
        ], limit=1)
        
        if not student_course:
            student_course = self.env['lms.student.course'].create({
                'student_id': student_id,
                'course_id': lesson_id.course_id.id,
                'status': 'in_progress',
            })
        
        return self.create({
            'student_id': student_id,
            'student_course_id': student_course.id,
            'lesson_id': lesson_id.id,
            'study_duration': duration,
            'status': 'completed',
        })



