# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class CORSController(http.Controller):
    """Controller để xử lý CORS preflight requests"""
    
    @http.route('/lms/api/<path:path>', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def cors_preflight(self, path, **kwargs):
        """Xử lý CORS preflight requests"""
        return request.make_response('', headers=[
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With'),
            ('Access-Control-Max-Age', '3600'),
        ])
