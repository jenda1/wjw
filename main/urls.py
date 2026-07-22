from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("new_user", views.new_user, name="new_user"),
    path("home", views.home, name="home"),
    path("profile_edit", views.profile_edit, name="profile_edit"),
    path("merge_requests", views.merge_requests, name="merge_requests"),
    path("merge_requests/<int:pk>", views.merge_request_detail, name="merge_request_detail"),
    path("membership_requests", views.membership_requests, name="membership_requests"),
    path("membership_requests/<int:pk>", views.membership_request_detail, name="membership_request_detail"),
]
