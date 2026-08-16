from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount
from django.contrib.messages import constants as message_constants
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse

from main import views
from main.models import Profile, ProfileMergeRequest, ProfileStudentRequest

from .helpers import create_profile, create_user


class IndexViewTests(TestCase):
    def test_anonymous_sees_unknown_state(self):
        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['is_known'])

    def test_active_member_is_redirected_to_home(self):
        user = create_user('parent1')
        create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        self.client.force_login(user)

        resp = self.client.get(reverse('index'))
        self.assertRedirects(resp, reverse('home'))

    def test_pending_member_is_not_redirected(self):
        user = create_user('parent1')
        create_profile(user, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(user)

        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['is_known'])

    def test_first_login_message_redirects_to_new_user(self):
        # main.signals.new_user (connected to allauth's user_signed_up) adds a
        # 'prvni_login' message; index() checks for it and redirects here.
        user = create_user('parent1')
        request = RequestFactory().get(reverse('index'))
        request.user = user
        setattr(request, 'session', self.client.session)
        storage = FallbackStorage(request)
        storage.add(message_constants.INFO, 'prvni_login')
        setattr(request, '_messages', storage)

        resp = views.index(request)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('new_user'))

    def test_pending_merge_request_shows_banner(self):
        user = create_user('requester1')
        ProfileMergeRequest.objects.create(
            user=user, old_email='old@example.com', first_name='Kid', last_name='X',
        )
        self.client.force_login(user)

        resp = self.client.get(reverse('index'))
        content = resp.content.decode()
        self.assertIn('Žádost o spojení účtu v řešení', content)
        self.assertIn('old@example.com', content)

    def test_rejected_merge_request_does_not_show_banner(self):
        user = create_user('requester1')
        ProfileMergeRequest.objects.create(
            user=user, old_email='old@example.com', first_name='Kid', last_name='X',
            status=ProfileMergeRequest.RequestStatus.REJECTED,
        )
        self.client.force_login(user)

        resp = self.client.get(reverse('index'))
        self.assertNotIn('Žádost o spojení účtu v řešení', resp.content.decode())


class HomeViewTests(TestCase):
    def test_requires_login(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp.url)

    def test_non_member_redirected_to_index(self):
        user = create_user('parent1')
        create_profile(user, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(user)

        resp = self.client.get(reverse('home'))
        self.assertRedirects(resp, reverse('index'))

    def test_active_member_sees_home_page(self):
        user = create_user('parent1', first_name='Petr', last_name='Novak')
        create_profile(user, status=Profile.ProfileStatus.ACTIVE, street_and_number='Hlavni 10', city='Praha')
        self.client.force_login(user)

        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Petr Novak', content)
        self.assertIn('Hlavni 10', content)

    def test_shows_no_children_message_when_none_pending_or_confirmed(self):
        user = create_user('parent1')
        create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        self.client.force_login(user)

        resp = self.client.get(reverse('home'))
        self.assertIn('Žádné děti nenalezeny', resp.content.decode())

    def test_shows_pending_student_request_without_no_children_message(self):
        user = create_user('parent1')
        profile = create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        ProfileStudentRequest.objects.create(
            profile=profile, first_name='Anicka', last_name='Novakova', birth_date='2016-01-01',
        )
        self.client.force_login(user)

        resp = self.client.get(reverse('home'))
        content = resp.content.decode()
        self.assertIn('Anicka Novakova', content)
        self.assertIn('čeká na schválení', content)
        self.assertNotIn('Žádné děti nenalezeny', content)

    def test_does_not_show_approved_or_rejected_requests(self):
        user = create_user('parent1')
        profile = create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        ProfileStudentRequest.objects.create(
            profile=profile, first_name='Schvaleny', last_name='Zak', birth_date='2016-01-01',
            status=ProfileStudentRequest.RequestStatus.APPROVED,
        )
        self.client.force_login(user)

        resp = self.client.get(reverse('home'))
        self.assertNotIn('čeká na schválení', resp.content.decode())

    def test_shows_plain_email_when_no_social_accounts(self):
        user = create_user('parent1', email='petr@example.com')
        create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        self.client.force_login(user)

        resp = self.client.get(reverse('home'))
        self.assertIn('petr@example.com', resp.content.decode())

    def test_shows_connected_social_accounts_with_primary_highlighted(self):
        user = create_user('parent1', email='petr.google@example.com')
        create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        SocialAccount.objects.create(
            user=user, provider='google', uid='g1', extra_data={'email': 'petr.google@example.com'}
        )
        SocialAccount.objects.create(
            user=user, provider='facebook', uid='f1', extra_data={'email': 'petr.fb@example.com'}
        )
        self.client.force_login(user)

        resp = self.client.get(reverse('home'))
        content = resp.content.decode()
        self.assertIn('petr.google@example.com', content)
        self.assertIn('petr.fb@example.com', content)
        self.assertIn('bi-google', content)
        self.assertIn('bi-facebook', content)
        self.assertIn('(hlavní)', content)

        # only the account matching User.email is marked primary
        google_idx = content.find('petr.google@example.com')
        facebook_idx = content.find('petr.fb@example.com')
        primary_idx = content.find('(hlavní)')
        self.assertLess(abs(primary_idx - google_idx), 200)
        self.assertGreater(abs(primary_idx - facebook_idx), 200)


class NewUserViewTests(TestCase):
    def test_requires_login(self):
        resp = self.client.get(reverse('new_user'))
        self.assertEqual(resp.status_code, 302)

    def test_submit_profile_creates_profile_and_student_requests(self):
        user = create_user('parent1', first_name='Petr', last_name='Novak')
        self.client.force_login(user)

        with patch('main.models.validuj_adresu'):
            resp = self.client.post(reverse('new_user'), {
                'submit_profile': '1',
                'first_name': 'Petr', 'last_name': 'Novak', 'email': 'ignored@evil.com',
                'birth_date': '1990-01-01',
                'street_and_number': 'Ulice 1', 'city': 'Praha', 'zip_code': '11000',
                'phone_number': '', 'membership': 'A', 'comments': '',
                'form-TOTAL_FORMS': '2', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-first_name': 'Dite', 'form-0-last_name': 'Novakovo',
                'form-0-birth_date': '2018-01-01', 'form-0-comments': '',
                'form-1-first_name': '', 'form-1-last_name': '', 'form-1-birth_date': '', 'form-1-comments': '',
            }, follow=True)

        self.assertEqual(resp.status_code, 200)
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.status, Profile.ProfileStatus.PENDING)
        self.assertEqual(ProfileStudentRequest.objects.filter(profile=profile).count(), 1)
        student_request = ProfileStudentRequest.objects.get(profile=profile)
        self.assertEqual(student_request.first_name, 'Dite')

    def test_submit_merge_creates_merge_request(self):
        user = create_user('parent1')
        self.client.force_login(user)

        resp = self.client.post(reverse('new_user'), {
            'submit_merge': '1',
            'old_email': 'old@example.com',
            'first_name': 'Kid', 'last_name': 'X', 'comments': '',
        }, follow=True)

        self.assertEqual(resp.status_code, 200)
        mr = ProfileMergeRequest.objects.get(user=user)
        self.assertEqual(mr.old_email, 'old@example.com')
        self.assertEqual(mr.status, ProfileMergeRequest.RequestStatus.PENDING)


class ProfileEditViewTests(TestCase):
    def test_requires_login(self):
        resp = self.client.get(reverse('profile_edit'))
        self.assertEqual(resp.status_code, 302)

    def test_redirects_to_new_user_when_no_profile(self):
        user = create_user('parent1')
        self.client.force_login(user)

        resp = self.client.get(reverse('profile_edit'))
        self.assertRedirects(resp, reverse('new_user'))

    def test_get_prefills_existing_values(self):
        user = create_user('parent1', first_name='Petr', last_name='Novak')
        create_profile(user, street_and_number='Hlavni 10')
        self.client.force_login(user)

        resp = self.client.get(reverse('profile_edit'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Petr', content)
        self.assertIn('Hlavni 10', content)

    def test_post_updates_profile_and_user_name(self):
        user = create_user('parent1', first_name='Petr', last_name='Novak', email='petr@example.com')
        create_profile(user, street_and_number='Stara 1')
        self.client.force_login(user)

        with patch('main.models.validuj_adresu'):
            resp = self.client.post(reverse('profile_edit'), {
                'first_name': 'Petr Updated', 'last_name': 'Novak Updated', 'email': 'hacked@evil.com',
                'birth_date': '1980-01-01',
                'street_and_number': 'Nova 5', 'city': 'Brno', 'zip_code': '60200',
                'phone_number': '', 'membership': 'A', 'comments': '',
            }, follow=True)

        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Petr Updated')
        self.assertEqual(user.email, 'petr@example.com')

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.street_and_number, 'Nova 5')

    def test_post_cannot_change_membership_type(self):
        user = create_user('parent1')
        create_profile(user, membership=Profile.MembershipType.ACTIVE)
        self.client.force_login(user)

        with patch('main.models.validuj_adresu'):
            resp = self.client.post(reverse('profile_edit'), {
                'first_name': 'Test', 'last_name': 'User', 'email': 'ignored@evil.com',
                'birth_date': '1980-01-01',
                'street_and_number': 'Ulice 1', 'city': 'Praha', 'zip_code': '11000',
                'phone_number': '', 'membership': 'P', 'comments': '',
            }, follow=True)

        self.assertEqual(resp.status_code, 200)
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.membership, Profile.MembershipType.ACTIVE)
