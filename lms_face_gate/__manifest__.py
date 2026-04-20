{
    'name': 'LMS Face Gate',
    'version': '18.0.1.0.0',
    'category': 'Education',
    'summary': 'Điểm danh khuôn mặt cho LMS',
    'depends': ['lms', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/config_parameters.xml',
        'views/student_face_views.xml',
        'views/face_gate_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lms_face_gate/static/src/js/face_sample_camera.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
