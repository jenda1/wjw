import datetime

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main.models import ProfileMergeRequest

from .helpers import create_user

User = get_user_model()


class MergeRequestsListViewTests(TestCase):
    def test_requires_staff(self):
        user = create_user('member1')
        self.client.force_login(user)

        resp = self.client.get(reverse('merge_requests'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lists_only_pending_requests(self):
        requester = create_user('requester1')
        ProfileMergeRequest.objects.create(
            user=requester, old_email='old@example.com',
            first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
        )

        other_requester = create_user('requester2')
        approved = ProfileMergeRequest.objects.create(
            user=other_requester, old_email='approved@example.com',
            first_name='Jiny', last_name='Zak', birth_date=datetime.date(2016, 1, 1),
            status=ProfileMergeRequest.RequestStatus.APPROVED,
        )

        staff = create_user('staff1', is_staff=True)
        self.client.force_login(staff)

        resp = self.client.get(reverse('merge_requests'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Anicka', content)
        self.assertNotIn('Jiny', content)
        self.assertNotEqual(approved.status, ProfileMergeRequest.RequestStatus.PENDING)


class MergeRequestDetailViewTests(TestCase):
    def setUp(self):
        self.staff = create_user('staff1', is_staff=True)
        self.target = create_user('target1', first_name='Petr', last_name='Novak')
        self.requester = create_user('requester1', first_name='Petr', last_name='Novak')
        self.merge_request = ProfileMergeRequest.objects.create(
            user=self.requester, old_email='old@example.com',
            first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
        )

    def test_requires_staff(self):
        self.client.force_login(self.requester)
        resp = self.client.get(reverse('merge_request_detail', args=[self.merge_request.pk]))
        self.assertNotEqual(resp.status_code, 200)

    def test_approve_moves_social_accounts_and_deletes_requester(self):
        SocialAccount.objects.create(user=self.target, provider='google', uid='g1')
        SocialAccount.objects.create(user=self.requester, provider='facebook', uid='f1')
        self.client.force_login(self.staff)

        resp = self.client.post(
            reverse('merge_request_detail', args=[self.merge_request.pk]),
            {'target_user': self.target.pk},
            follow=True,
        )

        self.assertEqual(resp.status_code, 200)

        self.merge_request.refresh_from_db()
        self.assertEqual(self.merge_request.status, ProfileMergeRequest.RequestStatus.APPROVED)
        self.assertIsNone(self.merge_request.user)

        self.assertFalse(User.objects.filter(pk=self.requester.pk).exists())

        target_providers = set(
            SocialAccount.objects.filter(user=self.target).values_list('provider', flat=True)
        )
        self.assertEqual(target_providers, {'google', 'facebook'})

    def test_reject_keeps_requester_and_marks_rejected(self):
        self.client.force_login(self.staff)

        resp = self.client.post(
            reverse('merge_request_detail', args=[self.merge_request.pk]),
            {'reject': '1'},
            follow=True,
        )

        self.assertEqual(resp.status_code, 200)
        self.merge_request.refresh_from_db()
        self.assertEqual(self.merge_request.status, ProfileMergeRequest.RequestStatus.REJECTED)
        self.assertTrue(User.objects.filter(pk=self.requester.pk).exists())

    def test_already_processed_request_404s(self):
        self.merge_request.status = ProfileMergeRequest.RequestStatus.APPROVED
        self.merge_request.save()
        self.client.force_login(self.staff)

        resp = self.client.get(reverse('merge_request_detail', args=[self.merge_request.pk]))
        self.assertEqual(resp.status_code, 404)
