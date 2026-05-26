from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("user_config", views.user_config, name="user_config"),
]
