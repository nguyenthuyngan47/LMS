# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import functools


def cors_handler(func):
    """Decorator để thêm CORS headers cho API endpoints.

    Hiện tại decorator này chỉ xử lý OPTIONS request và trả về
    response có CORS headers. Đối với các method khác,
    hàm gốc được gọi bình thường.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Xử lý OPTIONS request (preflight)
        if request.httprequest.method == "OPTIONS":
            return handle_cors_preflight()

        # Gọi hàm gốc
        return func(*args, **kwargs)

    return wrapper


def make_json_response(
    data,
    status_code=200,
    allow_methods="GET, POST, PUT, DELETE, OPTIONS",
    allow_headers="Content-Type, Authorization, X-Requested-With",
):
    """Helper tạo JSON response với CORS headers thống nhất."""
    headers = [
        ("Content-Type", "application/json"),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", allow_methods),
        ("Access-Control-Allow-Headers", allow_headers),
    ]
    return request.make_response(json.dumps(data), headers=headers)


def handle_cors_preflight(
    allow_methods="GET, POST, PUT, DELETE, OPTIONS",
    allow_headers="Content-Type, Authorization, X-Requested-With",
    max_age="3600",
):
    """Helper xử lý CORS preflight request (OPTIONS)."""
    headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", allow_methods),
        ("Access-Control-Allow-Headers", allow_headers),
        ("Access-Control-Max-Age", max_age),
    ]
    return request.make_response("", headers=headers)


class BaseController(http.Controller):
    """Base controller với CORS support và helper dùng chung."""

    @staticmethod
    def _add_cors_headers_to_response(response):
        """Thêm CORS headers vào response hiện có."""
        if hasattr(response, "headers"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With"
            )
        return response
