import datetime

from django.test import TestCase
from django.urls import reverse

from main.models import ParentRelationship

from .helpers import create_profile, create_student, create_user, create_vr_member


class OrphanStudentsViewTests(TestCase):
    def test_requires_approver_group(self):
        user = create_user('parent1')
        create_profile(user)
        self.client.force_login(user)

        resp = self.client.get(reverse('orphan_students'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lists_only_students_without_parents(self):
        orphan = create_student(first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1))

        parented = create_student(first_name='Jiny', last_name='Zak', birth_date=datetime.date(2016, 1, 1))
        parent_user = create_user('parent1')
        parent_profile = create_profile(parent_user)
        ParentRelationship.objects.create(parent=parent_profile, student=parented)

        vr_member = create_vr_member()
        self.client.force_login(vr_member)

        resp = self.client.get(reverse('orphan_students'))
        content = resp.content.decode()
        self.assertIn(orphan.first_name, content)
        self.assertNotIn('Jiny', content)
