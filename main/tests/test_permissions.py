from django.contrib.auth.models import Group
from django.test import TestCase

from main.permissions import (
    CAPO_DI_TUTTI_GROUP_NAME,
    SECRETARY_OF_THE_TREASURY_GROUP_NAME,
    can_approve_requests,
    can_view_others,
)

from .helpers import create_user


class CapoDiTuttiAndSecretaryPermissionTests(TestCase):
    def test_capo_di_tutti_can_approve_requests_and_view_others(self):
        user = create_user('capo1')
        group, _ = Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
        user.groups.add(group)

        self.assertTrue(can_approve_requests(user))
        self.assertTrue(can_view_others(user))

    def test_secretary_of_the_treasury_can_approve_requests_and_view_others(self):
        user = create_user('secretary1')
        group, _ = Group.objects.get_or_create(name=SECRETARY_OF_THE_TREASURY_GROUP_NAME)
        user.groups.add(group)

        self.assertTrue(can_approve_requests(user))
        self.assertTrue(can_view_others(user))

    def test_plain_member_cannot_approve_requests_or_view_others(self):
        user = create_user('member1')

        self.assertFalse(can_approve_requests(user))
        self.assertFalse(can_view_others(user))
