from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


class MyLoginView(LoginView):
    template_name = "accounts/login.html"


@login_required
def post_login_router(request):
    return redirect("admin:index")
