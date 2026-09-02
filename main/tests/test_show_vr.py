from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import ClassRepresentative
from main.permissions import CAPO_DI_TUTTI_GROUP_NAME, VR_MEMBER_GROUP_NAME

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
        self.assertIn('3. ročník', content)

    def test_non_vr_member_not_listed(self):
        outsider = create_user('outsider1', first_name='Petr', last_name='Nikdo')
        create_profile(outsider)

        viewer = create_user('viewer3')
        create_profile(viewer)
        self.client.force_login(viewer)

        resp = self.client.get(reverse('show_vr'))
        self.assertNotIn('Petr Nikdo', resp.content.decode())
