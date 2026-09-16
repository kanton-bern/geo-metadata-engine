import os
import socket

import django

# Build-time values are baked into the Docker image by the CI workflow;
# runtime values are injected by Kubernetes (Downward API / stage values).
# Everything is read once at import time because it cannot change while the process is running.
_APP_VERSION = os.environ.get("APP_VERSION", "local development (no image build)")
_APP_IMAGE = os.environ.get("APP_IMAGE", "")

_BUILD_INFO = {
    "app_version": _APP_VERSION,
    # Last dash-separated segment of the tag, i.e. the short git SHA
    # (e.g. "develop-20260916143022-a1b2c3d" -> "a1b2c3d").
    "app_version_short": _APP_VERSION.rsplit("-", 1)[-1] if "-" in _APP_VERSION else "",
    "image_name": f"{_APP_IMAGE}:{_APP_VERSION}" if _APP_IMAGE else "",
    "environment": os.environ.get("APP_ENVIRONMENT", "local"),
    "namespace": os.environ.get("POD_NAMESPACE", ""),
    "pod_name": os.environ.get("POD_NAME", socket.gethostname()),
    "django_version": django.get_version(),
}


def build_info(request):
    """Expose build and runtime information to all templates."""
    return _BUILD_INFO