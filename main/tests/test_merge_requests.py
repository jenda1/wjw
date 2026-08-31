from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main.models import ProfileMergeRequest

from .helpers import create_approver, create_user

User = get_user_model()


class MergeRequestsListViewTests(TestCase):
    def test_requires_approver_group(self):
        user = create_user('member1')
        self.client.force_login(user)

        resp = self.client.get(reverse('merge_requests'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lists_only_pending_requests(self):
        requester = create_user('requester1')
        ProfileMergeRequest.objects.create(
            user=requester, old_email='old@example.com',
            first_name='Anicka', last_name='Novakova',
        )

        other_requester = create_user('requester2')
        approved = ProfileMergeRequest.objects.create(
            user=other_requester, old_email='approved@example.com',
            first_name='Jiny', last_name='Zak',
            status=ProfileMergeRequest.RequestStatus.APPROVED,
        )

        approver = create_approver()
        self.client.force_login(approver)

        resp = self.client.get(reverse('merge_requests'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Anicka', content)
        self.assertNotIn('Jiny', content)
        self.assertNotEqual(approved.status, ProfileMergeRequest.RequestStatus.PENDING)


class MergeRequestDetailViewTests(TestCase):
    def setUp(self):
        self.approver = create_approver()
        self.target = create_user('target1', first_name='Petr', last_name='Novak')
        self.requester = create_user('requester1', first_name='Petr', last_name='Novak')
        self.merge_request = ProfileMergeRequest.objects.create(
            user=self.requester, old_email='old@example.com',
            first_name='Anicka', last_name='Novakova',
        )

    def test_requires_approver_group(self):
        self.client.force_login(self.requester)
        resp = self.client.get(reverse('merge_request_detail', args=[self.merge_request.pk]))
        self.assertNotEqual(resp.status_code, 200)

    def test_approve_moves_social_accounts_and_deletes_requester(self):
        SocialAccount.objects.create(user=self.target, provider='google', uid='g1')
        SocialAccount.objects.create(user=self.requester, provider='seznam', uid='f1')
        self.client.force_login(self.approver)

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
        self.assertEqual(target_providers, {'google', 'seznam'})

    def test_reject_keeps_requester_and_marks_rejected(self):
        self.client.force_login(self.approver)

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
        self.client.force_login(self.approver)

        resp = self.client.get(reverse('merge_request_detail', args=[self.merge_request.pk]))
        self.assertEqual(resp.status_code, 404)
