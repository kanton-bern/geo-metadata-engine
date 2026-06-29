from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


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
