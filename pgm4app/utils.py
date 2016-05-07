from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import resolve_url


def login_required_ajax(function=None, redirect_field_name=None):
    """
    Assert the user is authenticated to access a certain ajax view. Otherwise,
    if request was AJAX return HTTP 401. Otherwise, redirect (302) to default
    login page.

    Based on: http://stackoverflow.com/q/10031001/5520354
    """
    def _decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)

            if request.is_ajax():
                return HttpResponse(status=401)

            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(settings.LOGIN_URL)
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]

            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(
                    path, resolved_login_url, redirect_field_name)
        return _wrapped_view

    if function is None:
        return _decorator
    else:
        return _decorator(function)
