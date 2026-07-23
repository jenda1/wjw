import datetime

from django.test import TestCase
from django.urls import reverse

from main.models import Profile, ProfileMergeRequest

from .helpers import create_profile, create_user


class PendingRequestsCountContextProcessorTests(TestCase):
    def _create_pending_requests(self):
        pending_user = create_user('pending1')
        create_profile(pending_user, status=Profile.ProfileStatus.PENDING)

        requester = create_user('requester1')
        ProfileMergeRequest.objects.create(
            user=requester, old_email='old@example.com',
            first_name='Kid', last_name='X', birth_date=datetime.date(2016, 1, 1),
        )

    def test_anonymous_sees_no_counts(self):
        self._create_pending_requests()
        resp = self.client.get(reverse('index'))
        self.assertNotIn('pending_requests_count', resp.context)

    def test_non_staff_sees_no_counts(self):
        self._create_pending_requests()
        member = create_user('member1')
        create_profile(member, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(member)

        resp = self.client.get(reverse('index'))
        self.assertNotIn('pending_requests_count', resp.context)

    def test_staff_sees_correct_counts(self):
        self._create_pending_requests()
        staff = create_user('staff1', is_staff=True)
        self.client.force_login(staff)

        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.context['pending_membership_requests_count'], 1)
        self.assertEqual(resp.context['pending_merge_requests_count'], 1)
        self.assertEqual(resp.context['pending_requests_count'], 2)
