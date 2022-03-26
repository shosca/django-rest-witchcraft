try:
    from django.conf.urls import url as re_path
except ImportError:  # pragma: no cover
    from django.urls import re_path


urlpatterns = [re_path(r"^example/(?P<id>.+)/$", lambda: None, name="owner")]
