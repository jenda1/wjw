import datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import ClassRepresentative, ParentRelationship
from main.permissions import CAPO_DI_TUTTI_GROUP_NAME

from .helpers import create_class_collective, create_profile, create_student, create_user, create_vr_member


class OrphanedStudentsViewTests(TestCase):
    def test_requires_approver_group(self):
        user = create_user('parent1')
        create_profile(user)
        self.client.force_login(user)

        resp = self.client.get(reverse('orphaned_students'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lists_only_students_without_parents_in_represented_class(self):
        represented_class = create_class_collective(school_class=3)
        orphan = create_student(
            first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
            school_class=represented_class,
        )

        parented = create_student(
            first_name='Jiny', last_name='Zak', birth_date=datetime.date(2016, 1, 1),
            school_class=represented_class,
        )
        parent_user = create_user('parent1')
        parent_profile = create_profile(parent_user)
        ParentRelationship.objects.create(parent=parent_profile, student=parented)

        vr_user = create_vr_member()
        vr_profile = create_profile(vr_user)
        ClassRepresentative.objects.create(
            school_class=represented_class, representative=vr_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        )
        self.client.force_login(vr_user)

        resp = self.client.get(reverse('orphaned_students'))
        content = resp.content.decode()
        self.assertIn(orphan.first_name, content)
        self.assertNotIn('Jiny', content)

    def test_vr_member_does_not_see_orphans_of_other_classes(self):
        other_class = create_class_collective(school_class=4)
        orphan = create_student(
            first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
            school_class=other_class,
        )

        vr_user = create_vr_member()
        create_profile(vr_user)
        self.client.force_login(vr_user)

        resp = self.client.get(reverse('orphaned_students'))
        self.assertNotIn(orphan.first_name, resp.content.decode())

    def test_capo_di_tutti_sees_all_orphans(self):
        class_collective = create_class_collective(school_class=5)
        orphan = create_student(
            first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
            school_class=class_collective,
        )

        capo_user = create_user('capo1')
        create_profile(capo_user)
        group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
        capo_user.groups.add(group)
        self.client.force_login(capo_user)

        resp = self.client.get(reverse('orphaned_students'))
        self.assertIn(orphan.first_name, resp.content.decode())
