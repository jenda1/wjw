from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("new_user", views.new_user, name="new_user"),
    path("home", views.home, name="home"),
    path("profile_edit", views.profile_edit, name="profile_edit"),
    path("add_student", views.add_student, name="add_student"),
    path("merge_requests", views.merge_requests, name="merge_requests"),
    path("merge_requests/<int:pk>", views.merge_request_detail, name="merge_request_detail"),
    path("membership_requests", views.membership_requests, name="membership_requests"),
    path("membership_requests/<int:pk>", views.membership_request_detail, name="membership_request_detail"),
    path("student_requests", views.student_requests, name="student_requests"),
    path("student_requests/<int:pk>", views.student_request_detail, name="student_request_detail"),
    path("orphaned_students", views.orphaned_students, name="orphaned_students"),
    path("orphaned_members", views.orphaned_members, name="orphaned_members"),
    path("orphaned_classes", views.orphaned_classes, name="orphaned_classes"),
]
