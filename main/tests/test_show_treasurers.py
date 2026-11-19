from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import ClassRepresentative
from main.permissions import CAPO_DI_TUTTI_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME, SOTTO_CAPO_GROUP_NAME

from .helpers import create_class_collective, create_profile, create_user


class ShowTreasurersViewTests(TestCase):
    def test_requires_login(self):
        resp = self.client.get(reverse('show_treasurers'))
        self.assertEqual(resp.status_code, 302)

    def test_ordinary_member_forbidden(self):
        viewer = create_user('viewer1')
        create_profile(viewer)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_treasurers'))
        self.assertEqual(resp.status_code, 403)

    def test_capo_di_tutti_can_view(self):
        viewer = create_user('capo1')
        create_profile(viewer)
        group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
        viewer.groups.add(group)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_treasurers'))
        self.assertEqual(resp.status_code, 200)

    def test_sotto_capo_can_view(self):
        viewer = create_user('sotto1')
        create_profile(viewer)
        group, _ = Group.objects.get_or_create(name=SOTTO_CAPO_GROUP_NAME)
        viewer.groups.add(group)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_treasurers'))
        self.assertEqual(resp.status_code, 200)

    def test_secretary_of_the_treasury_can_view(self):
        viewer = create_user('secretary1')
        create_profile(viewer)
        group, _ = Group.objects.get_or_create(name=SECRETARY_OF_THE_TREASURY_GROUP_NAME)
        viewer.groups.add(group)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_treasurers'))
        self.assertEqual(resp.status_code, 200)

    def test_shows_class_treasurers_sorted_by_class(self):
        viewer = create_user('secretary2')
        create_profile(viewer)
        group, _ = Group.objects.get_or_create(name=SECRETARY_OF_THE_TREASURY_GROUP_NAME)
        viewer.groups.add(group)

        for username, last_name, school_class in [('pok5', 'Pata', 5), ('pok1', 'Prvni', 1)]:
            rep_user = create_user(username, first_name='Pokladnik', last_name=last_name)
            rep_profile = create_profile(rep_user)
            ClassRepresentative.objects.create(
                school_class=create_class_collective(year=2026 - school_class, school_class=school_class),
                representative=rep_profile,
                representant_type=ClassRepresentative.RepresentantType.TREASURER,
            )

        self.client.force_login(viewer)
        content = self.client.get(reverse('show_treasurers')).content.decode()
        self.assertIn('Prvni Pokladnik', content)
        self.assertIn('Pata Pokladnik', content)
        self.assertLess(content.index('Prvni Pokladnik'), content.index('Pata Pokladnik'))

    def test_vr_class_representative_not_listed(self):
        """Zástupce třídy ve VR (ne pokladník) se na stránce nezobrazí."""
        viewer = create_user('secretary3')
        create_profile(viewer)
        group, _ = Group.objects.get_or_create(name=SECRETARY_OF_THE_TREASURY_GROUP_NAME)
        viewer.groups.add(group)

        rep_user = create_user('vr1', first_name='Zastupce', last_name='Vr')
        rep_profile = create_profile(rep_user)
        ClassRepresentative.objects.create(
            school_class=create_class_collective(), representative=rep_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        )

        self.client.force_login(viewer)
        content = self.client.get(reverse('show_treasurers')).content.decode()
        self.assertNotIn('Zastupce Vr', content)
