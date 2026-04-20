from odoo import models, fields


class LmsFaceAttendance(models.Model):
    _name = 'lms.face.attendance'
    _description = 'Face Attendance Log'
    _order = 'timestamp desc'

    student_id = fields.Many2one(
        'lms.student',
        string='Sinh viên',
        required=True,
        ondelete='cascade',
        index=True,
    )
    lesson_id = fields.Many2one(
        'lms.lesson',
        string='Buổi học',
        required=True,
        ondelete='cascade',
        index=True,
    )
    passed = fields.Boolean(
        string='Điểm danh thành công',
        default=False,
    )
    timestamp = fields.Datetime(
        string='Thời gian',
        default=fields.Datetime.now,
        required=True,
    )
    similarity_score = fields.Float(
        string='Độ tương đồng',
        digits=(6, 4),
        help='1.0 = giống hoàn toàn, 0.0 = khác hoàn toàn',
    )
    failure_reason = fields.Char(
        string='Lý do thất bại',
    )
    captured_image = fields.Binary(
        string='Ảnh điểm danh',
        attachment=True,
        help='Ảnh chụp live lúc điểm danh — để admin kiểm tra lại',
    )
