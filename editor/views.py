import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import DEFAULT_DB_ALIAS, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.shortcuts import redirect, render


def liveness(request):
    """Public liveness probe at "/liveness/".

    Answers a single question: is the process up and able to serve HTTP?
    It runs no dependency checks (no DB), so a database outage does NOT make
    this fail — otherwise Kubernetes would kill and restart healthy pods that
    are merely waiting for the database to come back. Always returns 200 while
    the process can respond.
    """
    return JsonResponse({"status": "ok"})


def readiness(request):
    """Public readiness probe at "/readiness/".

    Reports whether the app can actually serve traffic by checking its
    dependencies, as JSON. Requires no authentication so it can be polled by
    Kubernetes probes and uptime monitors. Returns HTTP 200 when everything is
    healthy, 503 otherwise — signalling Kubernetes to stop routing traffic to
    this pod without killing it.

    Each entry in ``checks`` is either "ok" or an "error: ..." string; the
    overall status is unhealthy if any check failed. Informational fields
    (debug, latency) are reported but never affect the status code.
    """
    checks = {}
    info = {
        "debug": settings.DEBUG,
    }

    # Database connectivity, with round-trip latency for spotting a slow-but-up
    # database.
    database_ok = False
    try:
        start = time.monotonic()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        info["database_latency_ms"] = round((time.monotonic() - start) * 1000, 1)
        checks["database"] = "ok"
        database_ok = True
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Unapplied migrations — catches a pod that is up but running against an
    # out-of-date schema after a deploy. Skipped when the database is already
    # unreachable: it would only repeat the same connection failure and double
    # the probe latency (each attempt waits out the DB connect timeout).
    if database_ok:
        try:
            executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            if plan:
                checks["migrations"] = f"error: {len(plan)} unapplied migration(s)"
            else:
                checks["migrations"] = "ok"
        except Exception as exc:
            checks["migrations"] = f"error: {exc}"
    else:
        checks["migrations"] = "skipped: database unreachable"

    healthy = all(value == "ok" for value in checks.values())
    payload = {
        "status": "ok" if healthy else "unhealthy",
        "checks": checks,
        **info,
    }
    return JsonResponse(payload, status=200 if healthy else 503)


@login_required
def root(request):
    """Entry point at "/".

    Staff users are sent straight to the admin (the primary UI). Authenticated
    users without staff rights see a simple landing page instead of being
    bounced to the admin login form, which is confusing for someone who has
    already signed in successfully.
    """
    if request.user.is_staff:
        return redirect("admin:index")
    return render(request, "no_access.html")
