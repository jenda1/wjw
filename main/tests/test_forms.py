import datetime
from unittest.mock import patch

from django.test import TestCase

from main.forms import (
    EXISTING_MEMBER_NOTE,
    MergeRequestApprovalForm,
    ProfileForm,
    ProfileStudentRequestForm,
)

from .helpers import create_class_collective, create_student, create_user


class ProfileFormTests(TestCase):
    def test_prefills_from_user_and_marks_email_disabled(self):
        user = create_user('parent1', first_name='Petr', last_name='Novak', email='petr@example.com')
        form = ProfileForm(user)

        self.assertEqual(form.fields['first_name'].initial, 'Petr')
        self.assertEqual(form.fields['last_name'].initial, 'Novak')
        self.assertEqual(form.fields['email'].initial, 'petr@example.com')
        self.assertTrue(form.fields['email'].disabled)
        self.assertFalse(form.fields['first_name'].disabled)
        self.assertFalse(form.fields['last_name'].disabled)

    def test_field_order_has_identity_fields_first(self):
        form = ProfileForm(None)
        self.assertEqual(
            list(form.fields.keys())[:3],
            ['first_name', 'last_name', 'email'],
        )

    def _valid_post_data(self, **overrides):
        data = {
            'first_name': 'Petr', 'last_name': 'Novak', 'email': 'ignored@evil.com',
            'birth_date': '1990-01-01',
            'street_and_number': 'Ulice 1', 'city': 'Praha', 'zip_code': '11000',
            'phone_number': '', 'membership': 'A', 'comments': '',
        }
        data.update(overrides)
        return data

    def test_save_updates_name_on_user_but_ignores_tampered_email(self):
        user = create_user('parent1', first_name='Petr', last_name='Novak', email='petr@example.com')

        with patch('main.models.validuj_adresu'):
            form = ProfileForm(user, self._valid_post_data(first_name='Petr Updated', last_name='Novak Updated'))
            self.assertTrue(form.is_valid(), form.errors)
            form.instance.user = user
            profile = form.save()

        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Petr Updated')
        self.assertEqual(user.last_name, 'Novak Updated')
        self.assertEqual(user.email, 'petr@example.com')
        self.assertEqual(profile.user, user)
        self.assertFalse(hasattr(profile, 'first_name'))

    def test_save_commit_false_does_not_persist(self):
        user = create_user('parent1')

        with patch('main.models.validuj_adresu'):
            form = ProfileForm(user, self._valid_post_data())
            self.assertTrue(form.is_valid(), form.errors)
            profile = form.save(commit=False)

        self.assertIsNone(profile.pk)

    def test_allow_membership_change_false_disables_field_and_ignores_tampering(self):
        from main.models import Profile

        user = create_user('parent1')
        with patch('main.models.validuj_adresu'):
            profile = Profile.objects.create(
                user=user, birth_date=datetime.date(1980, 1, 1),
                street_and_number='Ulice 1', city='Praha', zip_code='11000',
                membership=Profile.MembershipType.ACTIVE,
            )

            form = ProfileForm(
                user, self._valid_post_data(membership='P'), instance=profile,
                allow_membership_change=False,
            )
            self.assertTrue(form.fields['membership'].disabled)
            self.assertTrue(form.is_valid(), form.errors)
            saved = form.save()

        self.assertEqual(saved.membership, Profile.MembershipType.ACTIVE)

    def test_allow_email_change_true_updates_email(self):
        user = create_user('parent1', email='petr@example.com')

        with patch('main.models.validuj_adresu'):
            form = ProfileForm(
                user, self._valid_post_data(email='novy@example.com'), allow_email_change=True,
            )
            self.assertFalse(form.fields['email'].disabled)
            self.assertTrue(form.is_valid(), form.errors)
            form.instance.user = user
            form.save()

        user.refresh_from_db()
        self.assertEqual(user.email, 'novy@example.com')

    def test_allow_email_change_true_rejects_email_used_by_another_user(self):
        create_user('other', email='obsazeny@example.com')
        user = create_user('parent1', email='petr@example.com')

        form = ProfileForm(
            user, self._valid_post_data(email='obsazeny@example.com'), allow_email_change=True,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_existing_member_flag_marks_comments(self):
        user = create_user('parent1')

        with patch('main.models.validuj_adresu'):
            form = ProfileForm(
                user, self._valid_post_data(existing_member='1', comments='Mám dvě děti.'),
            )
            self.assertTrue(form.is_valid(), form.errors)
            form.instance.user = user
            profile = form.save()

        self.assertEqual(profile.comments, f'{EXISTING_MEMBER_NOTE}\nMám dvě děti.')

    def test_comments_untouched_without_existing_member_flag(self):
        user = create_user('parent1')

        with patch('main.models.validuj_adresu'):
            form = ProfileForm(user, self._valid_post_data(comments='Mám dvě děti.'))
            self.assertTrue(form.is_valid(), form.errors)
            form.instance.user = user
            profile = form.save()

        self.assertEqual(profile.comments, 'Mám dvě děti.')


class StudentLookupMixinTests(TestCase):
    def setUp(self):
        klass = create_class_collective()
        self.student = create_student(
            first_name='Tomas', last_name='Novak', birth_date=datetime.date(2015, 5, 10), school_class=klass,
        )

    def _form_data(self, **overrides):
        data = {'first_name': 'tomas', 'last_name': 'NOVAK', 'birth_date': '2015-05-10', 'comments': ''}
        data.update(overrides)
        return data

    def test_matches_case_insensitively(self):
        form = ProfileStudentRequestForm(self._form_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['student_by_name'], self.student)

    def test_matches_ignoring_diacritics(self):
        klass = create_class_collective()
        accented_student = create_student(
            first_name='Tomáš', last_name='Novák', birth_date=datetime.date(2016, 3, 20), school_class=klass,
        )

        form = ProfileStudentRequestForm(
            {'first_name': 'tomas', 'last_name': 'novak', 'birth_date': '2016-03-20', 'comments': ''}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['student_by_name'], accented_student)

    def test_no_match_on_wrong_birth_date(self):
        form = ProfileStudentRequestForm(self._form_data(birth_date='1999-01-01'))
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data['student_by_name'])

    def test_valid_without_any_match_data(self):
        form = ProfileStudentRequestForm(
            {'first_name': 'Neco', 'last_name': 'Jine', 'birth_date': '2020-01-01', 'comments': ''}
        )
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data['student_by_name'])

    def test_save_sets_student_by_name_on_instance(self):
        form = ProfileStudentRequestForm(self._form_data())
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save(commit=False)
        self.assertEqual(instance.student_by_name, self.student)


class MergeRequestApprovalFormTests(TestCase):
    def test_target_user_is_required(self):
        form = MergeRequestApprovalForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('target_user', form.errors)

    def test_target_user_label_includes_name_and_email(self):
        user = create_user('target', first_name='Petr', last_name='Novak', email='petr@example.com')
        form = MergeRequestApprovalForm()
        label = form.fields['target_user'].label_from_instance(user)
        self.assertEqual(label, "Novak Petr (petr@example.com)")

    def test_valid_with_existing_user(self):
        user = create_user('target')
        form = MergeRequestApprovalForm({'target_user': user.pk})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['target_user'], user)
