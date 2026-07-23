from django.test import TestCase
from django.urls import reverse

from main.models import Profile, ProfileStudentRequest

from .helpers import create_profile, create_user


class MembershipRequestsListViewTests(TestCase):
    def test_requires_staff(self):
        user = create_user('member1')
        create_profile(user, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(user)

        resp = self.client.get(reverse('membership_requests'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lists_only_pending_profiles(self):
        pending_user = create_user('pending1', first_name='Petr', last_name='Novak')
        create_profile(pending_user, status=Profile.ProfileStatus.PENDING)

        active_user = create_user('active1', first_name='Jana', last_name='Svobodova')
        create_profile(active_user, status=Profile.ProfileStatus.ACTIVE)

        staff = create_user('staff1', is_staff=True)
        self.client.force_login(staff)

        resp = self.client.get(reverse('membership_requests'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Petr', content)
        self.assertNotIn('Jana', content)


class MembershipRequestDetailViewTests(TestCase):
    def setUp(self):
        self.staff = create_user('staff1', is_staff=True)
        self.applicant = create_user('applicant1', first_name='Petr', last_name='Novak')
        self.profile = create_profile(self.applicant, status=Profile.ProfileStatus.PENDING)

    def test_requires_staff(self):
        self.client.force_login(self.applicant)
        resp = self.client.get(reverse('membership_request_detail', args=[self.profile.pk]))
        self.assertNotEqual(resp.status_code, 200)

    def test_shows_related_student_requests(self):
        ProfileStudentRequest.objects.create(
            profile=self.profile, first_name='Anicka', last_name='Novakova',
            birth_date='2016-01-01',
        )
        self.client.force_login(self.staff)

        resp = self.client.get(reverse('membership_request_detail', args=[self.profile.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Anicka', resp.content.decode())

    def test_approve_activates_profile(self):
        self.client.force_login(self.staff)

        resp = self.client.post(
            reverse('membership_request_detail', args=[self.profile.pk]), {}, follow=True
        )

        self.assertEqual(resp.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, Profile.ProfileStatus.ACTIVE)

    def test_reject_cancels_profile(self):
        self.client.force_login(self.staff)

        resp = self.client.post(
            reverse('membership_request_detail', args=[self.profile.pk]), {'reject': '1'}, follow=True
        )

        self.assertEqual(resp.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, Profile.ProfileStatus.CANCELLED)

    def test_already_processed_request_404s(self):
        self.profile.status = Profile.ProfileStatus.ACTIVE
        self.profile.save()
        self.client.force_login(self.staff)

        resp = self.client.get(reverse('membership_request_detail', args=[self.profile.pk]))
        self.assertEqual(resp.status_code, 404)
