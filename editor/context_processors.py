import os
import socket

import django


def _build_info_rows():
    """Return (label, value) pairs for the admin footer, skipping empty values.

    Build-time values are baked into the Docker image by the CI workflow;
    runtime values are injected by Kubernetes (Downward API / stage values).
    """
    version = os.environ.get("APP_VERSION", "local development (no image build)")
    image = os.environ.get("APP_IMAGE", "")
    rows = [
        ("Environment", os.environ.get("APP_ENVIRONMENT", "local")),
        ("Namespace", os.environ.get("POD_NAMESPACE", "")),
        ("Pod", os.environ.get("POD_NAME", socket.gethostname())),
        ("Version", version),
        # Last dash-separated segment of the tag, i.e. the short git SHA
        # (e.g. "develop-20260916143022-a1b2c3d" -> "a1b2c3d").
        ("Commit", version.rsplit("-", 1)[-1] if "-" in version else ""),
        ("Image", f"{image}:{version}" if image else ""),
        ("Django", django.get_version()),
    ]
    return [(label, value) for label, value in rows if value]


# Computed once at import time because nothing here can change while the process is running.
_BUILD_INFO_ROWS = _build_info_rows()


def build_info(request):
    """Expose build and runtime information to all templates."""
    return {"build_info": _BUILD_INFO_ROWS}
