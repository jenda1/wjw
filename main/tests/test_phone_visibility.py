from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import Circle, CircleMembership, ClassRepresentative, ParentRelationship
from main.permissions import VR_MEMBER_GROUP_NAME

from .helpers import (
    create_class_collective, create_profile, create_student, create_user, create_vr_member,
)

HIDDEN_PHONE = '+420111222333'


class PhoneVisibilityTests(TestCase):
    """Telefon se ostatním členům smí zobrazit jen tehdy, když to člen dovolil."""

    def _viewer_in_class(self, class_collective, student):
        viewer = create_user('viewer1')
        viewer_profile = create_profile(viewer)
        ParentRelationship.objects.create(parent=viewer_profile, student=student)
        self.client.force_login(viewer)
        return viewer

    def test_show_members_hides_phone_when_not_allowed(self):
        class_collective = create_class_collective()
        student = create_student(school_class=class_collective)

        other = create_user('other1', first_name='Petr', last_name='Tajny')
        other_profile = create_profile(other, phone_number=HIDDEN_PHONE, phone_visible=False)
        ParentRelationship.objects.create(parent=other_profile, student=student)

        self._viewer_in_class(class_collective, student)

        content = self.client.get(reverse('show_members', args=[class_collective.pk])).content.decode()
        self.assertIn('Tajny Petr', content)
        self.assertNotIn(HIDDEN_PHONE, content)

    def test_show_members_shows_phone_when_allowed(self):
        class_collective = create_class_collective()
        student = create_student(school_class=class_collective)

        other = create_user('other2', first_name='Petr', last_name='Verejny')
        other_profile = create_profile(other, phone_number=HIDDEN_PHONE, phone_visible=True)
        ParentRelationship.objects.create(parent=other_profile, student=student)

        self._viewer_in_class(class_collective, student)

        content = self.client.get(reverse('show_members', args=[class_collective.pk])).content.decode()
        self.assertIn(HIDDEN_PHONE, content)

    def test_show_vr_hides_phone_when_not_allowed(self):
        rep_user = create_user('rep1', first_name='Anna', last_name='Zastupkyne')
        rep_profile = create_profile(rep_user, phone_number=HIDDEN_PHONE, phone_visible=False)
        vr_group, _ = Group.objects.get_or_create(name=VR_MEMBER_GROUP_NAME)
        rep_user.groups.add(vr_group)
        ClassRepresentative.objects.create(
            school_class=create_class_collective(), representative=rep_profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        )

        viewer = create_user('viewer2')
        create_profile(viewer)
        self.client.force_login(viewer)

        content = self.client.get(reverse('show_vr')).content.decode()
        self.assertIn('Zastupkyne Anna', content)
        self.assertNotIn(HIDDEN_PHONE, content)

    def test_show_circle_hides_speakers_phone_when_not_allowed(self):
        circle = Circle.objects.create(name='Kruh')
        speaker = create_user('speaker1', first_name='Jana', last_name='Mluvci')
        speaker_profile = create_profile(speaker, phone_number=HIDDEN_PHONE, phone_visible=False)
        CircleMembership.objects.create(
            circle=circle, profile=speaker_profile, speaker_of_circle=True,
        )

        viewer = create_user('viewer3')
        create_profile(viewer)
        self.client.force_login(viewer)

        content = self.client.get(reverse('show_circle', args=[circle.pk])).content.decode()
        self.assertIn('Mluvci Jana', content)
        self.assertNotIn(HIDDEN_PHONE, content)

    def test_orphaned_members_shows_phone_to_leadership(self):
        """Vedení spolku telefon vidí i tak - eviduje členy a musí je kontaktovat."""
        member = create_user('member1', first_name='Petr', last_name='Tajny')
        create_profile(member, phone_number=HIDDEN_PHONE, phone_visible=False)

        self.client.force_login(create_vr_member())

        content = self.client.get(reverse('orphaned_members')).content.decode()
        self.assertIn(HIDDEN_PHONE, content)
