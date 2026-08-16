from django.test import TestCase
from django.urls import reverse

from main.models import ParentRelationship, Profile

from .helpers import create_profile, create_student, create_user, create_vr_member


class ProfilesWithoutStudentsViewTests(TestCase):
    def test_requires_approver_group(self):
        user = create_user('parent1')
        create_profile(user)
        self.client.force_login(user)

        resp = self.client.get(reverse('profiles_without_students'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lists_only_active_profiles_without_students(self):
        childless_user = create_user('parent1', first_name='Anicka', last_name='Bezdetna')
        create_profile(childless_user)

        parented_user = create_user('parent2', first_name='Jiny', last_name='Rodic')
        parented_profile = create_profile(parented_user)
        student = create_student()
        ParentRelationship.objects.create(parent=parented_profile, student=student)

        pending_user = create_user('parent3', first_name='Cekajici', last_name='Zadatel')
        create_profile(pending_user, status=Profile.ProfileStatus.PENDING)

        vr_member = create_vr_member()
        self.client.force_login(vr_member)

        resp = self.client.get(reverse('profiles_without_students'))
        content = resp.content.decode()
        self.assertIn('Anicka', content)
        self.assertNotIn('Jiny', content)
        self.assertNotIn('Cekajici', content)
