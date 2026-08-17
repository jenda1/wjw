import datetime

from django.test import TestCase
from django.urls import reverse

from main.models import ClassRepresentative

from .helpers import create_class_collective, create_profile, create_user, create_vr_member


class OrphanClassesViewTests(TestCase):
    def test_requires_approver_group(self):
        user = create_user('parent1')
        create_profile(user)
        self.client.force_login(user)

        resp = self.client.get(reverse('orphan_classes'))
        self.assertNotEqual(resp.status_code, 200)

    def test_class_with_both_roles_filled_is_not_listed(self):
        complete_class = create_class_collective(school_class=3)
        vr_user = create_user('vr_rep')
        vr_profile = create_profile(vr_user)
        ClassRepresentative.objects.create(
            school_class=complete_class, representative=vr_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        )
        treasurer_user = create_user('treasurer')
        treasurer_profile = create_profile(treasurer_user)
        ClassRepresentative.objects.create(
            school_class=complete_class, representative=treasurer_profile,
            representant_type=ClassRepresentative.RepresentantType.TREASURER,
        )

        vr_member = create_vr_member()
        self.client.force_login(vr_member)

        resp = self.client.get(reverse('orphan_classes'))
        content = resp.content.decode()
        self.assertNotIn('3. ročník', content)

    def test_class_missing_treasurer_is_listed(self):
        incomplete_class = create_class_collective(school_class=4)
        vr_user = create_user('vr_rep2')
        vr_profile = create_profile(vr_user)
        ClassRepresentative.objects.create(
            school_class=incomplete_class, representative=vr_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        )

        vr_member = create_vr_member()
        self.client.force_login(vr_member)

        resp = self.client.get(reverse('orphan_classes'))
        content = resp.content.decode()
        self.assertIn('4. ročník', content)

    def test_expired_representative_does_not_count(self):
        incomplete_class = create_class_collective(school_class=5)
        vr_user = create_user('vr_rep3')
        vr_profile = create_profile(vr_user)
        ClassRepresentative.objects.create(
            school_class=incomplete_class, representative=vr_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
            valid_until=datetime.date(2000, 1, 1),
        )
        treasurer_user = create_user('treasurer3')
        treasurer_profile = create_profile(treasurer_user)
        ClassRepresentative.objects.create(
            school_class=incomplete_class, representative=treasurer_profile,
            representant_type=ClassRepresentative.RepresentantType.TREASURER,
        )

        vr_member = create_vr_member()
        self.client.force_login(vr_member)

        resp = self.client.get(reverse('orphan_classes'))
        content = resp.content.decode()
        self.assertIn('5. ročník', content)
