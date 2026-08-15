from .models import Profile, ProfileMergeRequest, ProfileStudentRequest, Student
from .permissions import can_approve_requests


def pending_requests_count(request):
    if not can_approve_requests(request.user):
        return {}

    membership_count = Profile.objects.filter(status=Profile.ProfileStatus.PENDING).count()
    merge_count = ProfileMergeRequest.objects.filter(status=ProfileMergeRequest.RequestStatus.PENDING).count()
    student_count = ProfileStudentRequest.objects.filter(
        status=ProfileStudentRequest.RequestStatus.PENDING
    ).count()
    orphan_students_count = Student.objects.filter(parents__isnull=True).count()

    return {
        'can_approve_requests': True,
        'pending_membership_requests_count': membership_count,
        'pending_merge_requests_count': merge_count,
        'pending_student_requests_count': student_count,
        'orphan_students_count': orphan_students_count,
        'pending_requests_count': membership_count + merge_count + student_count,
    }
