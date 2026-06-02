from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("new_user", views.new_user, name="new_user"),
    path("profile/update", views.profile_update, name="profile_update"),
    path("profile/merge", views.profile_merge, name="profile_merge"),
]
