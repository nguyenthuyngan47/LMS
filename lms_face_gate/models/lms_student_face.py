import base64
import logging

from odoo import _, models, fields

_logger = logging.getLogger(__name__)


def _get_validate_fn():
    from odoo.addons.lms_face_gate.controllers.face_sample import validate_and_embed

    return validate_and_embed


class LmsStudent(models.Model):
    _inherit = 'lms.student'

    face_sample_image = fields.Binary(
        string='Ảnh mẫu khuôn mặt',
        attachment=True,
        help='Ảnh chân dung chuẩn — đã qua validate khuôn mặt',
    )
    face_embedding = fields.Text(
        string='Face Embedding',
        readonly=True,
        help='128-d vector dạng JSON, tính tự động khi lưu ảnh mẫu',
    )
    face_sample_status = fields.Selection(
        [
            ('none', 'Chưa có ảnh'),
            ('ok', 'Hợp lệ'),
            ('invalid', 'Không hợp lệ'),
        ],
        string='Trạng thái ảnh mẫu',
        default='none',
        readonly=True,
    )
    face_sample_message = fields.Char(
        string='Thông báo xác thực',
        readonly=True,
    )

    def write(self, vals):
        if self.env.context.get('lms_face_gate_skip_face_sample_validation'):
            return super().write(vals)

        res = super().write(vals)

        if 'face_sample_image' not in vals:
            return res

        if not vals.get('face_sample_image'):
            try:
                self.with_context(lms_face_gate_skip_face_sample_validation=True).sudo().write(
                    {
                        'face_embedding': False,
                        'face_sample_status': 'none',
                        'face_sample_message': False,
                    }
                )
            except Exception:
                _logger.exception('lms_face_gate: could not reset face fields after image clear')
            return res

        try:
            try:
                min_face_ratio = float(
                    self.env['ir.config_parameter']
                    .sudo()
                    .get_param('lms_face_gate.min_face_ratio', '0.12')
                )
            except (TypeError, ValueError):
                min_face_ratio = 0.12

            validate_and_embed = _get_validate_fn()

            for rec in self:
                try:
                    # Sau super().write, Binary trên record là bytes file thật — đừng dùng vals (base64 / lệnh khác).
                    raw = rec.face_sample_image
                    if not raw:
                        continue
                    if isinstance(raw, bytes):
                        raw_b64 = base64.b64encode(raw).decode('ascii')
                    else:
                        raw_b64 = raw
                    embedding, error = validate_and_embed(raw_b64, min_face_ratio)
                    if error:
                        rec.with_context(lms_face_gate_skip_face_sample_validation=True).sudo().write(
                            {
                                'face_embedding': False,
                                'face_sample_status': 'invalid',
                                'face_sample_message': error,
                            }
                        )
                    else:
                        rec.with_context(lms_face_gate_skip_face_sample_validation=True).sudo().write(
                            {
                                'face_embedding': embedding,
                                'face_sample_status': 'ok',
                                'face_sample_message': _('Ảnh mẫu hợp lệ'),
                            }
                        )
                except Exception:
                    _logger.exception('lms_face_gate: validation failed for student %s', rec.id)
                    try:
                        rec.with_context(lms_face_gate_skip_face_sample_validation=True).sudo().write(
                            {
                                'face_embedding': False,
                                'face_sample_status': 'invalid',
                                'face_sample_message': _(
                                    'Lỗi khi xử lý ảnh mẫu. Thử ảnh JPEG/PNG nhỏ hơn hoặc liên hệ quản trị.'
                                ),
                            }
                        )
                    except Exception:
                        _logger.exception(
                            'lms_face_gate: could not write invalid status for student %s', rec.id
                        )
        except Exception:
            # Không ném exception ra ngoài write(): tránh RPC lỗi thiếu error.data → JS FormController.onSaveError vỡ
            _logger.exception('lms_face_gate: post-write face sample handling failed')

        return res


class LmsLesson(models.Model):
    _inherit = 'lms.lesson'

    face_gate_calendar_use_gate_url = fields.Boolean(
        string='Dùng link điểm danh trong Calendar',
        default=False,
        help='Nếu bật, mô tả Calendar event sẽ chứa link gate '
        'thay vì link Meet trực tiếp',
    )
