# -*- coding: utf-8 -*-
{
    'name': 'Learning Management System (LMS)',
    'version': '18.0.1.0.0',
    'category': 'Education',
    'summary': 'Hệ thống quản lý học tập với AI đề xuất khóa học',
    'description': """
Learning Management System với AI
=================================
* Quản lý sinh viên và khóa học
* Theo dõi tiến độ học tập
* AI đề xuất roadmap học tập
* Content-Based Filtering và Rule-Based Recommendation
* Quản lý mentor và giảng viên
    """,
    'author': 'LMS Team',
    'depends': ['base', 'mail', 'portal'],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/lms_groups.xml',
        'security/ir.model.access.csv',
        'data/remove_old_rules.xml',
        'security/lms_security.xml',
        'data/system_parameters.xml',
        'data/outgoing_mail_server.xml',
        'data/course_category_data.xml',
        'data/course_level_data.xml',
        'data/demo_data.xml',
        'data/mail_templates.xml',
        'views/student_views.xml',
        'views/course_views.xml',
        'views/learning_history_views.xml',
        'views/mentor_views.xml',
        'views/roadmap_views.xml',
        # 'views/settings_views.xml',  # Tạm comment để module load được, sẽ sửa xpath sau
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

