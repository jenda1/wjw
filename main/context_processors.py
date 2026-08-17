from django.db.models import Q
from django.utils import timezone

from .models import ClassCollective, ClassRepresentative, Profile, ProfileMergeRequest, ProfileStudentRequest, Student
from .permissions import can_approve_requests, can_view_all_classes, can_view_others


def pending_requests_count(request):
    context = {}

    if can_approve_requests(request.user):
        membership_count = Profile.objects.filter(status=Profile.ProfileStatus.PENDING).count()
        merge_count = ProfileMergeRequest.objects.filter(status=ProfileMergeRequest.RequestStatus.PENDING).count()
        student_count = ProfileStudentRequest.objects.filter(
            status=ProfileStudentRequest.RequestStatus.PENDING
        ).count()

        context.update({
            'can_approve_requests': True,
            'pending_membership_requests_count': membership_count,
            'pending_merge_requests_count': merge_count,
            'pending_student_requests_count': student_count,
            'pending_requests_count': membership_count + merge_count + student_count,
        })

    if can_view_others(request.user):
        orphaned_students_count = Student.objects.filter(parents__isnull=True).count()
        orphaned_members_count = Profile.objects.filter(
            status=Profile.ProfileStatus.ACTIVE, children__isnull=True
        ).count()

        today = timezone.localdate()
        currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=today)
        classes_with_vr = set(ClassRepresentative.objects.filter(
            currently_valid, representant_type=ClassRepresentative.RepresentantType.VR
        ).values_list('school_class_id', flat=True))
        classes_with_treasurer = set(ClassRepresentative.objects.filter(
            currently_valid, representant_type=ClassRepresentative.RepresentantType.TREASURER
        ).values_list('school_class_id', flat=True))
        orphaned_classes_count = (
            ClassCollective.objects.exclude(pk__in=classes_with_vr)
            | ClassCollective.objects.exclude(pk__in=classes_with_treasurer)
        ).distinct().count()

        context.update({
            'can_view_others': True,
            'orphaned_students_count': orphaned_students_count,
            'orphaned_members_count': orphaned_members_count,
            'orphaned_classes_count': orphaned_classes_count,
            'issues_count': orphaned_students_count + orphaned_members_count + orphaned_classes_count,
        })

    return context


def available_classes(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    if profile is None or profile.status != Profile.ProfileStatus.ACTIVE:
        return {}

    if can_view_all_classes(user):
        classes = ClassCollective.objects.all()
    else:
        classes = ClassCollective.objects.filter(students__parents=profile).distinct()

    return {'available_classes': classes}
