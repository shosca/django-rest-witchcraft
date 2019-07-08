# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

from psycopg2cffi import compat

import django
import django.test.utils


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

compat.register()

django.setup()
