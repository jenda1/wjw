import datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import Profile, ProfileMergeRequest, ProfileStudentRequest
from main.permissions import KOLEGIUM_GROUP_NAME

from .helpers import create_approver, create_profile, create_user, create_vr_member


class PendingRequestsCountContextProcessorTests(TestCase):
    def _create_pending_requests(self):
        pending_user = create_user('pending1')
        create_profile(pending_user, status=Profile.ProfileStatus.PENDING)

        requester = create_user('requester1')
        ProfileMergeRequest.objects.create(
            user=requester, old_email='old@example.com',
            first_name='Kid', last_name='X',
        )

        student_requester = create_user('student_requester1')
        student_requester_profile = create_profile(student_requester, status=Profile.ProfileStatus.ACTIVE)
        ProfileStudentRequest.objects.create(
            profile=student_requester_profile, first_name='Another', last_name='Kid',
            birth_date=datetime.date(2017, 1, 1),
        )

    def test_anonymous_sees_no_counts(self):
        self._create_pending_requests()
        resp = self.client.get(reverse('index'))
        self.assertNotIn('pending_requests_count', resp.context)

    def test_non_approver_sees_no_counts(self):
        self._create_pending_requests()
        member = create_user('member1')
        create_profile(member, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(member)

        resp = self.client.get(reverse('index'))
        self.assertNotIn('pending_requests_count', resp.context)

    def test_approver_sees_correct_counts(self):
        self._create_pending_requests()
        approver = create_approver()
        self.client.force_login(approver)

        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.context['pending_membership_requests_count'], 1)
        self.assertEqual(resp.context['pending_merge_requests_count'], 1)
        self.assertEqual(resp.context['pending_student_requests_count'], 1)
        self.assertEqual(resp.context['pending_requests_count'], 3)


class OrphanedMembersCountContextProcessorTests(TestCase):
    """Počet v hlavičce musí odpovídat výpisu ve view - kolegium se nepočítá."""

    def test_kolegium_member_without_student_is_not_counted(self):
        kolegium_user = create_user('kolegium1')
        create_profile(kolegium_user, status=Profile.ProfileStatus.ACTIVE)
        group, _ = Group.objects.get_or_create(name=KOLEGIUM_GROUP_NAME)
        kolegium_user.groups.add(group)

        viewer = create_vr_member()
        create_profile(viewer, status=Profile.ProfileStatus.ACTIVE)
        self.client.force_login(viewer)

        # index aktivního člena přesměruje na home, proto počítadlo z hlavičky
        # čteme rovnou ze stránky s výpisem.
        resp = self.client.get(reverse('orphaned_members'))
        rows = resp.context['profiles']

        self.assertNotIn(kolegium_user.profile, rows)
        self.assertEqual(resp.context['orphaned_members_count'], len(rows))

    def test_regular_member_without_student_is_counted(self):
        childless = create_user('childless1')
        create_profile(childless, status=Profile.ProfileStatus.ACTIVE)

        viewer = create_vr_member()
        create_profile(viewer, status=Profile.ProfileStatus.ACTIVE)
        self.client.force_login(viewer)

        # index aktivního člena přesměruje na home, proto počítadlo z hlavičky
        # čteme rovnou ze stránky s výpisem.
        resp = self.client.get(reverse('orphaned_members'))
        rows = resp.context['profiles']

        self.assertIn(childless.profile, rows)
        self.assertEqual(resp.context['orphaned_members_count'], len(rows))
