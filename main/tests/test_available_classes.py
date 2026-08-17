import datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import ParentRelationship
from main.permissions import CAPO_DI_TUTTI_GROUP_NAME

from .helpers import create_class_collective, create_profile, create_student, create_user


class AvailableClassesContextProcessorTests(TestCase):
    def test_regular_member_sees_only_own_childs_class(self):
        own_class = create_class_collective(school_class=2)
        other_class = create_class_collective(school_class=3)

        user = create_user('parent1')
        profile = create_profile(user)
        child = create_student(school_class=own_class, birth_date=datetime.date(2016, 1, 1))
        ParentRelationship.objects.create(parent=profile, student=child)

        self.client.force_login(user)
        resp = self.client.get(reverse('home'))
        content = resp.content.decode()

        self.assertIn(f'/show_members/{own_class.pk}', content)
        self.assertNotIn(f'/show_members/{other_class.pk}', content)

    def test_capo_di_tutti_sees_all_classes(self):
        class_a = create_class_collective(school_class=1)
        class_b = create_class_collective(school_class=2)

        capo_user = create_user('capo1')
        create_profile(capo_user)
        group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
        capo_user.groups.add(group)

        self.client.force_login(capo_user)
        resp = self.client.get(reverse('home'))
        content = resp.content.decode()

        self.assertIn(f'/show_members/{class_a.pk}', content)
        self.assertIn(f'/show_members/{class_b.pk}', content)

    def test_member_without_children_sees_no_class_links(self):
        user = create_user('parent1')
        create_profile(user)

        self.client.force_login(user)
        resp = self.client.get(reverse('home'))
        self.assertNotIn('show_members', resp.content.decode())
