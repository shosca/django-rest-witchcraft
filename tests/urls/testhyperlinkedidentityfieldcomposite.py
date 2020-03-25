from django.conf.urls import url


urlpatterns = [url(r"^example/(?P<id>.+)/(?P<other_id>.+)/$", lambda: None, name="owner")]
