import os
import socket


def build_info(request):
    """Expose build and runtime information to all templates.

    APP_VERSION is baked into the Docker image by the CI workflow.
    POD_NAME is injected by Kubernetes via the Downward API.
    Both fall back to descriptive values for local development.
    """
    return {
        "app_version": os.environ.get("APP_VERSION", "local development (no image build"),
        "pod_name": os.environ.get("POD_NAME", socket.gethostname()),
    }