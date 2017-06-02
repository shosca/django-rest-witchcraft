# -*- coding: utf-8 -*-
import django
import django.test.utils
from django.conf import settings

settings.configure()

django.setup()
django.test.utils.setup_test_environment()
