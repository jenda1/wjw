from .models import Profile, ProfileMergeRequest


def pending_requests_count(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}

    membership_count = Profile.objects.filter(status=Profile.ProfileStatus.PENDING).count()
    merge_count = ProfileMergeRequest.objects.filter(status=ProfileMergeRequest.RequestStatus.PENDING).count()

    return {
        'pending_membership_requests_count': membership_count,
        'pending_merge_requests_count': merge_count,
        'pending_requests_count': membership_count + merge_count,
    }
