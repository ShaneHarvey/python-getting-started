from django.conf.urls import url

from django.contrib import admin

admin.autodiscover()

import hello.views

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    url(r"^$", hello.views.index, name="index"),
    url(r"^db/", hello.views.db, name="db"),
    url(r"^admin/", admin.site.urls),
    url(r"^mongodb/", hello.views.mongodb, name="mongodb"),
]
