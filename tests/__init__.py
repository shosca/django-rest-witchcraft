# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from psycopg2cffi import compat

import django
import django.test.utils
from django.conf import settings


compat.register()

settings.configure()

django.setup()
django.test.utils.setup_test_environment()
