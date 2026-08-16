import datetime

from django.test import TestCase
from django.urls import reverse

from main.models import Profile, ProfileMergeRequest, ProfileStudentRequest

from .helpers import create_approver, create_profile, create_user


class PendingRequestsCountContextProcessorTests(TestCase):
    def _create_pending_requests(self):
        pending_user = create_user('pending1')
        create_profile(pending_user, status=Profile.ProfileStatus.PENDING)

        requester = create_user('requester1')
        ProfileMergeRequest.objects.create(
            user=requester, old_email='old@example.com',
            first_name='Kid', last_name='X',
        )

        student_requester = create_user('student_requester1')
        student_requester_profile = create_profile(student_requester, status=Profile.ProfileStatus.ACTIVE)
        ProfileStudentRequest.objects.create(
            profile=student_requester_profile, first_name='Another', last_name='Kid',
            birth_date=datetime.date(2017, 1, 1),
        )

    def test_anonymous_sees_no_counts(self):
        self._create_pending_requests()
        resp = self.client.get(reverse('index'))
        self.assertNotIn('pending_requests_count', resp.context)

    def test_non_approver_sees_no_counts(self):
        self._create_pending_requests()
        member = create_user('member1')
        create_profile(member, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(member)

        resp = self.client.get(reverse('index'))
        self.assertNotIn('pending_requests_count', resp.context)

    def test_approver_sees_correct_counts(self):
        self._create_pending_requests()
        approver = create_approver()
        self.client.force_login(approver)

        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.context['pending_membership_requests_count'], 1)
        self.assertEqual(resp.context['pending_merge_requests_count'], 1)
        self.assertEqual(resp.context['pending_student_requests_count'], 1)
        self.assertEqual(resp.context['pending_requests_count'], 3)
