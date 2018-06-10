# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import django
import django.test.utils
from django.conf import settings


settings.configure()

django.setup()
django.test.utils.setup_test_environment()
