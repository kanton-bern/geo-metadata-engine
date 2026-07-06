"""
URL configuration for metadata project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from editor.views import liveness, readiness


# Keep a reference to the unwrapped admin login view so it stays reachable as a
# local username/password fallback for superusers (break-glass access if ADFS is
# unavailable).
admin_local_login = admin.site.login

# Force the default admin login to redirect to LOGIN_URL (ADFS) instead of
# rendering the built-in Django username/password form.
admin.site.login = login_required(admin.site.login)


urlpatterns = [
    path("", include("editor.urls", namespace="editor")),
    path("admin/local-login/", admin_local_login, name="admin-local-login"),
    path("admin/", admin.site.urls, name="admin"),
    path("oauth2/", include("django_auth_adfs.urls")),
    path("liveness/", liveness, name="liveness"),
    path("readiness/", readiness, name="readiness"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
