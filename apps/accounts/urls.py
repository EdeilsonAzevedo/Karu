from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.MyLoginView.as_view(), name="login"),
    path("post-login/", views.post_login_router, name="post_login_router"),
]
