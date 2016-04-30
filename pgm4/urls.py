"""pgm4 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin

import pgm4app.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$',
        pgm4app.views.HomeView.as_view(), name='home'),
    url(r'^users/$',
        pgm4app.views.UserListView.as_view(), name='user-list'),
    url(r'^users/(?P<username>\w+)/$',
        pgm4app.views.UserDetailView.as_view(), name='user-detail'),

    url(r'^ask/$',
        pgm4app.views.QuestionCreateView.as_view(), name='question-create'),
    url(r'^ask/(?P<pk>\d+)/$',
        pgm4app.views.QuestionUpdateView.as_view(), name='question-update'),
    url(r'^questions/$',
        pgm4app.views.QuestionListView.as_view(), name='question-list'),
    url(r'^questions/(?P<pk>\d+)/(?P<slug>[a-z0-9_-]+)/$',
        pgm4app.views.QuestionDetailView.as_view(), name='question-detail'),

    url(r'^tags/$',
        pgm4app.views.TagListView.as_view(), name='tag-list'),
    url(r'^tags/(?P<slug>[a-z0-9_-]+)$',
        pgm4app.views.TagDetailView.as_view(), name='tag-detail'),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
