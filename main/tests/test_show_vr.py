from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import ClassRepresentative
from main.permissions import CAPO_DI_TUTTI_GROUP_NAME, KOLEGIUM_GROUP_NAME, VR_MEMBER_GROUP_NAME

from .helpers import create_class_collective, create_profile, create_user


class ShowVrViewTests(TestCase):
    def test_requires_login(self):
        resp = self.client.get(reverse('show_vr'))
        self.assertEqual(resp.status_code, 302)

    def test_capo_di_tutti_listed_first_as_chairman(self):
        capo_user = create_user('capo1', first_name='Karel', last_name='Predseda', email='capo@example.com')
        capo_profile = create_profile(capo_user)
        vr_group, _ = Group.objects.get_or_create(name=VR_MEMBER_GROUP_NAME)
        capo_group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
        capo_user.groups.add(vr_group, capo_group)

        viewer = create_user('viewer1')
        create_profile(viewer)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_vr'))
        content = resp.content.decode()
        self.assertIn('Predseda Karel', content)
        self.assertIn('Předseda spolku', content)
        self.assertIn('capo@example.com', content)

    def test_class_representative_shows_class_name(self):
        rep_user = create_user('rep1', first_name='Anna', last_name='Zastupkyne', email='rep@example.com')
        rep_profile = create_profile(rep_user)
        vr_group, _ = Group.objects.get_or_create(name=VR_MEMBER_GROUP_NAME)
        rep_user.groups.add(vr_group)

        class_collective = create_class_collective(school_class=3)
        ClassRepresentative.objects.create(
            school_class=class_collective, representative=rep_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        )

        viewer = create_user('viewer2')
        create_profile(viewer)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_vr'))
        content = resp.content.decode()
        self.assertIn('Zastupkyne Anna', content)
        self.assertIn('3. (2023)', content)

    def test_non_vr_member_not_listed(self):
        outsider = create_user('outsider1', first_name='Petr', last_name='Nikdo')
        create_profile(outsider)

        viewer = create_user('viewer3')
        create_profile(viewer)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_vr'))
        self.assertNotIn('Petr Nikdo', resp.content.decode())

    def test_sections_are_ordered_and_classes_sorted(self):
        vr_group, _ = Group.objects.get_or_create(name=VR_MEMBER_GROUP_NAME)
        capo_group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
        kolegium_group, _ = Group.objects.get_or_create(name=KOLEGIUM_GROUP_NAME)

        capo_user = create_user('capo2', first_name='Karel', last_name='Predseda')
        create_profile(capo_user)
        capo_user.groups.add(vr_group, capo_group)

        kolegium_user = create_user('kol1', first_name='Jana', last_name='Ucitelka')
        create_profile(kolegium_user)
        kolegium_user.groups.add(kolegium_group)

        # Člen VR bez zastoupení třídy patří mezi ostatní.
        other_user = create_user('other1', first_name='Pavel', last_name='Ostatni')
        create_profile(other_user)
        other_user.groups.add(vr_group)

        # Zástupce 5. ročníku zakládáme jako první, aby se ověřilo řazení podle třídy, ne podle vzniku.
        # Nižší ročník = pozdější rok nástupu, na tom stojí nativní řazení ClassCollective.
        for username, last_name, school_class in [('rep5', 'Pata', 5), ('rep1', 'Prvni', 1)]:
            rep_user = create_user(username, first_name='Rodic', last_name=last_name)
            rep_profile = create_profile(rep_user)
            rep_user.groups.add(vr_group)
            ClassRepresentative.objects.create(
                school_class=create_class_collective(year=2026 - school_class, school_class=school_class),
                representative=rep_profile,
                representant_type=ClassRepresentative.RepresentantType.VR,
            )

        viewer = create_user('viewer4')
        create_profile(viewer)
        self.client.force_login(viewer)

        content = self.client.get(reverse('show_vr')).content.decode()
        positions = [
            content.index(needle) for needle in
            ['Predseda Karel', 'Prvni Rodic', 'Pata Rodic', 'Ucitelka Jana', 'Ostatni Pavel']
        ]
        self.assertEqual(positions, sorted(positions))

    def test_member_with_several_roles_lists_them_all(self):
        vr_group, _ = Group.objects.get_or_create(name=VR_MEMBER_GROUP_NAME)
        capo_group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)

        # Předseda je zároveň zástupcem jedné třídy.
        capo_user = create_user('capo3', first_name='Karel', last_name='Predseda')
        capo_profile = create_profile(capo_user)
        capo_user.groups.add(vr_group, capo_group)
        ClassRepresentative.objects.create(
            school_class=create_class_collective(year=2025, school_class=1),
            representative=capo_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        )

        # Jeden zástupce zastupuje dvě třídy.
        rep_user = create_user('rep2', first_name='Anna', last_name='Zastupkyne')
        rep_profile = create_profile(rep_user)
        rep_user.groups.add(vr_group)
        for year, school_class in [(2024, 2), (2021, 5)]:
            ClassRepresentative.objects.create(
                school_class=create_class_collective(year=year, school_class=school_class),
                representative=rep_profile,
                representant_type=ClassRepresentative.RepresentantType.VR,
            )

        viewer = create_user('viewer5')
        create_profile(viewer)
        self.client.force_login(viewer)

        content = self.client.get(reverse('show_vr')).content.decode()
        self.assertIn('Předseda spolku, zástupce 1. (2025)', content)
        self.assertIn('zástupce 2. (2024), zástupce 5. (2021)', content)
