# -*- coding: utf-8 -*-

from . import models
from . import wizards
from . import controllers

# Ensure post-init hook is importable by Odoo.
from .hooks import post_init_hook, pre_init_hook  # noqa: F401



