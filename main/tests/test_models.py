import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase

from main.models import Profile, ProfileMergeRequest

from .helpers import create_profile, create_student, create_user


class ProfileModelTests(TestCase):
    def test_str_uses_user_name_and_membership_when_active(self):
        user = create_user('parent1', first_name='Petr', last_name='Novak')
        profile = create_profile(user, status='AC', membership='A')
        self.assertEqual(str(profile), "Petr Novak (A)")

    def test_str_when_pending_shows_membership(self):
        # NOTE: Profile.__str__ compares self.status to
        # self.ProfileStatus.PENDING[0], which indexes the *string* 'PE' and
        # yields 'P' rather than the PENDING choice - so this branch never
        # actually distinguishes PENDING and always falls through to
        # self.membership. This test documents the current (buggy) behavior.
        user = create_user('parent1', first_name='Petr', last_name='Novak')
        profile = create_profile(user, status='PE', membership='A')
        self.assertEqual(str(profile), "Petr Novak (A)")

    def test_user_is_required(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Profile.objects.create(
                    user=None,
                    birth_date=datetime.date(1980, 1, 1),
                    street_and_number='X', city='Praha', zip_code='11000',
                )

    def test_get_status_full(self):
        user = create_user('parent1')
        profile = create_profile(user, status='AC', membership='A')
        self.assertEqual(profile.get_status_full(), "člen - aktivní")


class StudentModelTests(TestCase):
    def test_str(self):
        student = create_student(first_name='Anicka', last_name='Novakova')
        self.assertEqual(str(student), "Anicka Novakova (3. ročník (2023))")


class ProfileMergeRequestModelTests(TestCase):
    def test_default_status_is_pending(self):
        user = create_user('requester')
        mr = ProfileMergeRequest.objects.create(
            user=user, old_email='old@example.com',
            first_name='Kid', last_name='X',
        )
        self.assertEqual(mr.status, ProfileMergeRequest.RequestStatus.PENDING)

    def test_deleting_user_sets_null_and_keeps_request(self):
        user = create_user('requester')
        mr = ProfileMergeRequest.objects.create(
            user=user, old_email='old@example.com',
            first_name='Kid', last_name='X',
        )
        user.delete()

        mr.refresh_from_db()
        self.assertIsNone(mr.user)
        self.assertEqual(mr.first_name, 'Kid')
