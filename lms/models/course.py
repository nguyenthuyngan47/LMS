# -*- coding: utf-8 -*-

from odoo import models, fields, api


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
    description = fields.Html(string='Mô tả', tracking=True)
    image_1920 = fields.Image(string='Ảnh khóa học', max_width=1920, max_height=1920)
    
    # Phân loại
    category_id = fields.Many2one('lms.course.category', string='Danh mục', required=True, tracking=True)
    level_id = fields.Many2one('lms.course.level', string='Cấp độ', required=True, tracking=True)
    tag_ids = fields.Many2many('lms.course.tag', 'course_tag_rel', 'course_id', 'tag_id', string='Nhãn')
    
    # Thông tin khóa học
    instructor_id = fields.Many2one('res.users', string='Giảng viên', tracking=True)
    duration_hours = fields.Float(string='Thời lượng (giờ)', digits=(16, 2), tracking=True)
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
    
    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('published', 'Đã xuất bản'),
        ('archived', 'Lưu trữ'),
    ], string='Trạng thái', default='draft', tracking=True)
    
    is_active = fields.Boolean(string='Đang hoạt động', default=True)
    
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
    
    student_course_ids = fields.One2many('lms.student.course', 'course_id', string='Học viên đăng ký')
    
    def action_publish(self):
        """Xuất bản khóa học"""
        self.write({'state': 'published'})
        return True


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
    
    # Quiz
    quiz_ids = fields.One2many('lms.quiz', 'lesson_id', string='Câu hỏi quiz')
    has_quiz = fields.Boolean(string='Có quiz', compute='_compute_has_quiz')
    
    # Thời lượng
    duration_minutes = fields.Integer(string='Thời lượng (phút)')
    
    @api.depends('quiz_ids')
    def _compute_has_quiz(self):
        for record in self:
            record.has_quiz = bool(record.quiz_ids)


class Quiz(models.Model):
    _name = 'lms.quiz'
    _description = 'Câu hỏi quiz'
    _order = 'sequence, name'

    name = fields.Char(string='Câu hỏi', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    lesson_id = fields.Many2one('lms.lesson', string='Bài học', required=True, ondelete='cascade')
    
    question_type = fields.Selection([
        ('multiple_choice', 'Trắc nghiệm'),
        ('true_false', 'Đúng/Sai'),
        ('short_answer', 'Câu trả lời ngắn'),
    ], string='Loại câu hỏi', default='multiple_choice', required=True)
    
    options = fields.Text(string='Các lựa chọn (mỗi dòng một lựa chọn)')
    correct_answer = fields.Char(string='Đáp án đúng', required=True)
    points = fields.Integer(string='Điểm số', default=1)
    
    def get_options_list(self):
        """Trả về danh sách các lựa chọn dưới dạng list"""
        if not self.options:
            return []
        return [opt.strip() for opt in self.options.split('\n') if opt.strip()]
    
    def check_answer(self, user_answer):
        """Kiểm tra đáp án của người dùng"""
        if not user_answer:
            return False
        # So sánh không phân biệt hoa thường và loại bỏ khoảng trắng
        user_answer_clean = user_answer.strip().lower()
        correct_answer_clean = self.correct_answer.strip().lower()
        return user_answer_clean == correct_answer_clean

