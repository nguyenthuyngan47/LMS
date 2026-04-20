import base64
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

MIN_FACE_RATIO_DEFAULT = '0.12'
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 1280 * 720

_JPEG_MAGIC = b'\xff\xd8\xff'
_PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


def _raw_image_file_bytes(image_input):
    """
    Trả về bytes nội dung file ảnh (JPEG/PNG) từ:
    - Chuỗi base64 / data URL (data:image/...;base64,...)
    - Bytes đã là file JPEG/PNG (giống cache Binary trên record sau khi ghi)
    """
    if not image_input:
        return None
    if isinstance(image_input, memoryview):
        image_input = image_input.tobytes()
    if isinstance(image_input, bytes):
        if image_input.startswith(_JPEG_MAGIC) or image_input.startswith(_PNG_MAGIC):
            return image_input
        try:
            s = image_input.decode('ascii')
        except UnicodeDecodeError:
            return None
        return _raw_image_file_bytes(s)
    if isinstance(image_input, str):
        s = image_input.strip()
        if s.startswith('data:') and 'base64,' in s:
            s = s.split('base64,', 1)[1]
        s = s.replace('\n', '').replace('\r', '')
        try:
            return base64.b64decode(s, validate=True)
        except Exception:
            try:
                return base64.b64decode(s)
            except Exception:
                return None
    return None


def _validate_image_file(data):
    """
    Xác thực cấu trúc file ảnh, detect corruption sớm.
    Trả về (is_valid, error_message)
    """
    if not data or len(data) < 4:
        return False, 'Dữ liệu ảnh quá nhỏ hoặc bị hỏng'
    
    # Check magic bytes
    if data.startswith(_JPEG_MAGIC):
        # JPEG: kiểm tra đóng file (FFD9)
        if not data.endswith(b'\xff\xd9'):
            return False, 'File JPEG không hoàn chỉnh hoặc bị hỏng'
    elif data.startswith(_PNG_MAGIC):
        # PNG: kiểm tra có IEND chunk (49454E44 = IEND)
        if b'IEND' not in data:
            return False, 'File PNG không hoàn chỉnh hoặc bị hỏng'
    else:
        return False, 'Định dạng file không được hỗ trợ, cần JPEG hoặc PNG'
    
    return True, None


def validate_and_embed(image_b64, min_face_ratio=0.12):
    import base64, json
    import numpy as np
    import cv2
    import face_recognition

    # Bước 1: Decode base64 → cv2.imdecode
    try:
        data = base64.b64decode(image_b64)
    except Exception:
        return None, 'Dữ liệu ảnh không hợp lệ'

    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None, 'Định dạng ảnh không hợp lệ, chỉ chấp nhận JPEG hoặc PNG'

    # Convert BGR → RGB (bắt buộc cho face_recognition)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Resize về tối đa 800px để tránh std::bad_alloc
    MAX_DIM = 800
    h, w = img_rgb.shape[:2]
    if max(h, w) > MAX_DIM:
        scale = MAX_DIM / max(h, w)
        img_rgb = cv2.resize(
            img_rgb,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA,
        )

    img_h, img_w = img_rgb.shape[:2]

    # Bước 2: Detect khuôn mặt
    locations = face_recognition.face_locations(img_rgb, model='hog')
    if len(locations) == 0:
        return None, 'Không phát hiện khuôn mặt trong ảnh, vui lòng chụp lại'

    # Bước 3: Chỉ 1 khuôn mặt
    if len(locations) > 1:
        return None, f'Phát hiện {len(locations)} khuôn mặt, ảnh mẫu chỉ được có 1 người'

    # Bước 4: Mặt chiếm đủ diện tích
    top, right, bottom, left = locations[0]
    face_area  = (bottom - top) * (right - left)
    image_area = img_h * img_w
    ratio = face_area / image_area
    if ratio < min_face_ratio:
        return None, (
            f'Khuôn mặt quá nhỏ ({ratio * 100:.1f}% diện tích ảnh), '
            f'vui lòng chụp gần hơn'
        )

    # Bước 5: Tính embedding
    encodings = face_recognition.face_encodings(
        img_rgb, known_face_locations=locations
    )
    if not encodings:
        return None, 'Không thể trích xuất đặc trưng khuôn mặt, thử ảnh khác'

    return json.dumps(encodings[0].tolist()), None


class FaceSampleController(http.Controller):

    @http.route(
        '/lms/face-gate/upload-sample',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=True,
    )
    def upload_sample(self, image=None, student_id=None, **kwargs):
        image_b64 = image if image is not None else kwargs.get('image')
        if student_id is None:
            student_id = kwargs.get('student_id')

        if not image_b64:
            return {'success': False, 'error': 'Thiếu dữ liệu ảnh'}

        env = request.env
        user = env.user

        is_manager = user.has_group('lms.group_lms_manager')

        if is_manager and student_id:
            # ✅ Fix Lỗi 1: Chuyển đổi Integer an toàn
            try:
                student_id_int = int(student_id)
            except (ValueError, TypeError):
                return {'success': False, 'error': 'ID sinh viên không hợp lệ'}
            
            student = env['lms.student'].sudo().browse(student_id_int)
            if not student.exists():
                return {'success': False, 'error': 'Không tìm thấy sinh viên'}
            
            # ✅ Fix Lỗi 4: Kiểm tra quyền chỉnh sửa
            if student.is_instructor_restricted:
                return {'success': False, 'error': 'Sinh viên này không thể sửa ảnh do bị khóa'}
        else:
            # Sinh viên chỉ có thể sửa ảnh của chính mình
            student = env['lms.student'].sudo().search(
                [('user_id', '=', user.id)],
                limit=1,
            )
            if not student:
                return {
                    'success': False,
                    'error': 'Tài khoản chưa liên kết hồ sơ sinh viên, liên hệ admin',
                }

        try:
            min_face_ratio = float(
                env['ir.config_parameter']
                .sudo()
                .get_param('lms_face_gate.min_face_ratio', MIN_FACE_RATIO_DEFAULT)
            )
        except (TypeError, ValueError):
            min_face_ratio = 0.12

        embedding, error = validate_and_embed(image_b64, min_face_ratio)

        if error:
            student.with_context(lms_face_gate_skip_face_sample_validation=True).write({
                'face_sample_status': 'invalid',
                'face_sample_message': error,
            })
            return {'success': False, 'error': error}

        # ✅ Fix Lỗi 2 + Lỗi 5: Convert base64 → bytes trước khi write, skip validate lần 2
        image_bytes = _raw_image_file_bytes(image_b64)
        if not image_bytes:
            return {'success': False, 'error': 'Không thể chuyển đổi ảnh'}

        student.with_context(lms_face_gate_skip_face_sample_validation=True).write({
            'face_sample_image': image_bytes,  # ✅ Gửi bytes thực tế, không phải base64 string
            'face_embedding': embedding,
            'face_sample_status': 'ok',
            'face_sample_message': 'Ảnh mẫu hợp lệ, sẵn sàng điểm danh',
        })
        return {'success': True, 'message': 'Ảnh mẫu đã được lưu thành công'}
