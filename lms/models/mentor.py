# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Mentor(models.Model):
    _name = 'lms.mentor'
    _description = 'Mentor'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên mentor', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Người dùng', required=True, tracking=True)
    email = fields.Char(string='Email', related='user_id.email', readonly=True)
    phone = fields.Char(string='Số điện thoại')
    image_1920 = fields.Image(string='Ảnh đại diện', max_width=1920, max_height=1920)
    
    # Quan hệ
    student_ids = fields.One2many('lms.student', 'mentor_id', string='Học viên phụ trách')
    total_students = fields.Integer(string='Tổng số học viên', compute='_compute_total_students')
    
    # Roadmap đã xem xét
    reviewed_roadmaps_ids = fields.One2many('lms.roadmap', 'reviewed_by', string='Roadmap đã xem xét')
    
    # Ghi chú
    notes = fields.Text(string='Ghi chú')
    is_active = fields.Boolean(string='Đang hoạt động', default=True, tracking=True)
    
    @api.depends('student_ids')
    def _compute_total_students(self):
        for record in self:
            record.total_students = len(record.student_ids)
    
    def action_view_students(self):
        """Xem danh sách học viên"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Học viên',
            'res_model': 'lms.student',
            'view_mode': 'list,form,kanban',
            'domain': [('mentor_id', '=', self.id)],
            'context': {'default_mentor_id': self.id},
        }
    
    def action_view_roadmaps(self):
        """Xem roadmap đã xem xét"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Roadmap đã xem xét',
            'res_model': 'lms.roadmap',
            'view_mode': 'list,form,kanban',
            'domain': [('reviewed_by', '=', self.id)],
        }



