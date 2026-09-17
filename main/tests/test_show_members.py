import datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import ClassRepresentative, ParentRelationship, Profile
from main.permissions import CAPO_DI_TUTTI_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME

from .helpers import (
    create_class_collective, create_profile, create_student, create_user, create_vr_member,
)


class ShowMembersViewTests(TestCase):
    def setUp(self):
        self.class_collective = create_class_collective(school_class=3)
        self.other_class = create_class_collective(school_class=4)

        self.parent_user = create_user('parent1', first_name='Petr', last_name='Rodic', email='petr@example.com')
        self.parent_profile = create_profile(self.parent_user)
        self.child = create_student(
            first_name='Anicka', last_name='Rodicova', school_class=self.class_collective,
            birth_date=datetime.date(2016, 1, 1),
        )
        ParentRelationship.objects.create(parent=self.parent_profile, student=self.child)

    def test_requires_login(self):
        resp = self.client.get(reverse('show_members', args=[self.class_collective.pk]))
        self.assertEqual(resp.status_code, 302)

    def test_member_with_child_in_class_can_see_it(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(reverse('show_members', args=[self.class_collective.pk]))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Rodic Petr', content)
        self.assertIn('petr@example.com', content)
        self.assertIn('Rodicova Anicka', content)

    def test_member_without_child_in_class_is_forbidden(self):
        outsider_user = create_user('outsider1')
        create_profile(outsider_user)
        self.client.force_login(outsider_user)

        resp = self.client.get(reverse('show_members', args=[self.class_collective.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_member_cannot_see_other_class(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(reverse('show_members', args=[self.other_class.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_capo_di_tutti_can_see_any_class(self):
        capo_user = create_user('capo1')
        create_profile(capo_user)
        group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
        capo_user.groups.add(group)
        self.client.force_login(capo_user)

        resp = self.client.get(reverse('show_members', args=[self.class_collective.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Rodic Petr', resp.content.decode())

    def test_secretary_can_see_any_class(self):
        secretary_user = create_user('secretary1')
        create_profile(secretary_user)
        group, _ = Group.objects.get_or_create(name=SECRETARY_OF_THE_TREASURY_GROUP_NAME)
        secretary_user.groups.add(group)
        self.client.force_login(secretary_user)

        resp = self.client.get(reverse('show_members', args=[self.other_class.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_pending_member_is_forbidden(self):
        pending_user = create_user('pending1')
        create_profile(pending_user, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(pending_user)

        resp = self.client.get(reverse('show_members', args=[self.class_collective.pk]))
        self.assertEqual(resp.status_code, 403)


class ShowMembersRepresentativesTests(TestCase):
    """Zástupci třídy se vypisují po řádcích - zvlášť zástupci ve VR, zvlášť pokladníci."""

    def setUp(self):
        self.class_collective = create_class_collective(school_class=3)
        self.child = create_student(school_class=self.class_collective)

        viewer = create_user('viewer1')
        viewer_profile = create_profile(viewer)
        ParentRelationship.objects.create(parent=viewer_profile, student=self.child)
        self.client.force_login(viewer)

    def _create_representative(self, username, representant_type, **profile_kwargs):
        user = create_vr_member(username, **{
            'first_name': profile_kwargs.pop('first_name', 'Jan'),
            'last_name': profile_kwargs.pop('last_name', 'Zastupce'),
            'email': profile_kwargs.pop('email', f'{username}@example.com'),
        })
        profile = create_profile(user, **profile_kwargs)
        ParentRelationship.objects.create(parent=profile, student=self.child)
        return ClassRepresentative.objects.create(
            school_class=self.class_collective, representative=profile,
            representant_type=representant_type,
        )

    def _content(self):
        resp = self.client.get(reverse('show_members', args=[self.class_collective.pk]))
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_vr_representatives_are_listed_before_treasurers(self):
        self._create_representative(
            'treasurer1', ClassRepresentative.RepresentantType.TREASURER,
            last_name='Pokladni', email='pokladni@example.com',
        )
        self._create_representative(
            'vrrep1', ClassRepresentative.RepresentantType.VR,
            last_name='Radni', email='radni@example.com',
        )

        content = self._content()
        self.assertLess(content.index("Zástupce ve VR:"), content.index("Pokladník:"))
        self.assertLess(content.index('radni@example.com'), content.index('pokladni@example.com'))

    def test_several_representatives_of_one_type_share_a_line(self):
        self._create_representative(
            'vrrep2', ClassRepresentative.RepresentantType.VR, last_name='Bbb',
        )
        self._create_representative(
            'vrrep3', ClassRepresentative.RepresentantType.VR, last_name='Aaa',
        )

        content = self._content()
        self.assertIn("Zástupci ve VR:", content)
        self.assertNotIn("Zástupce ve VR:", content)
        # V rámci řádku abecedně podle příjmení.
        self.assertLess(content.index('Aaa'), content.index('Bbb'))

    def test_representative_phone_respects_visibility(self):
        self._create_representative(
            'vrrep4', ClassRepresentative.RepresentantType.VR,
            phone_number='+420111222333', phone_visible=False,
        )
        self._create_representative(
            'treasurer2', ClassRepresentative.RepresentantType.TREASURER,
            phone_number='+420444555666', phone_visible=True,
        )

        content = self._content()
        reps_section = content[:content.index('<table')]
        self.assertNotIn('+420111222333', reps_section)
        self.assertIn('+420444555666', reps_section)
