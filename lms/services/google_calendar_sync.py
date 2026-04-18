# -*- coding: utf-8 -*-
"""Dựng payload và đồng bộ Google Calendar cho lms.lesson, tách khỏi model."""

import logging

from . import google_calendar_client

_logger = logging.getLogger(__name__)


def _unique_attendees(items, max_attendees):
    seen = set()
    attendees = []
    for email, name in items:
        if not email:
            continue
        key = email.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        attendees.append({'email': email.strip(), 'displayName': (name or '').strip() or email.strip()})
        if len(attendees) >= max_attendees:
            break
    return attendees


def build_event_payload(lesson):
    config = google_calendar_client.get_google_calendar_config()
    course = lesson.course_id.sudo()
    attendees_raw = []

    if config['include_instructor'] and course.instructor_id:
        instructor_email = (course.instructor_id.email or course.instructor_id.login or '').strip()
        attendees_raw.append((instructor_email, course.instructor_id.name))

    if config['include_students']:
        enrollments = lesson.env['lms.student.course'].sudo().search(
            [
                ('course_id', '=', course.id),
                ('status', 'in', config['student_statuses']),
            ]
        )
        for student in enrollments.mapped('student_id'):
            attendees_raw.append((student.email or student.user_id.email or student.user_id.login, student.name))

    description_parts = [
        f"Khóa học: {course.name}",
    ]
    if lesson.description:
        description_parts.append(lesson.description)
    if config['include_meeting_url_in_description'] and lesson.meeting_url:
        description_parts.append(f"Link buổi học: {lesson.meeting_url}")

    tz = config['timezone']
    start_dt = lesson.start_datetime.isoformat() if lesson.start_datetime else None
    end_dt = lesson.end_datetime.isoformat() if lesson.end_datetime else None
    attendees = _unique_attendees(attendees_raw, config['max_attendees'])
    payload = {
        'summary': f"[LMS] {course.name} - {lesson.name}",
        'description': '\n\n'.join(p for p in description_parts if p),
        'start': {
            'dateTime': start_dt,
            'timeZone': tz,
        },
        'end': {
            'dateTime': end_dt,
            'timeZone': tz,
        },
    }
    if attendees:
        payload['attendees'] = attendees
    return payload


def sync_lesson_event(lesson):
    payload = build_event_payload(lesson)
    if lesson.google_event_id:
        event = google_calendar_client.update_event(lesson.google_event_id, payload)
    else:
        event = google_calendar_client.create_event(payload)
    return {
        'google_event_id': event.get('id') or False,
        'google_event_html_link': event.get('htmlLink') or False,
        'meeting_url': event.get('hangoutLink') or lesson.meeting_url or False,
        'calendar_sync_status': 'synced',
        'calendar_sync_error': False,
    }


def delete_lesson_event(lesson):
    if not lesson.google_event_id:
        return
    try:
        google_calendar_client.delete_event(lesson.google_event_id)
    except Exception:  # noqa: BLE001
        _logger.exception('Google Calendar delete failed for lesson %s', lesson.id)
        raise

