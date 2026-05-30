from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("update_profile", views.update_profile, name="update_profile"),
]
