from .models import Profile, ProfileMergeRequest, ProfileStudentRequest, Student
from .permissions import can_approve_requests, can_view_others


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
        orphan_students_count = Student.objects.filter(parents__isnull=True).count()
        profiles_without_students_count = Profile.objects.filter(
            status=Profile.ProfileStatus.ACTIVE, children__isnull=True
        ).count()

        context.update({
            'can_view_others': True,
            'orphan_students_count': orphan_students_count,
            'profiles_without_students_count': profiles_without_students_count,
            'issues_count': orphan_students_count + profiles_without_students_count,
        })

    return context
