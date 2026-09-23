from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from wagtail.models import Site

from doc.models import AgendaPage, _default_participants
from main.permissions import VR_MEMBER_GROUP_NAME
from main.tests.helpers import create_profile, create_user


class AgendaPagePeopleTests(TestCase):
    """Osoby (předkladatelé i účastníci) jsou plochý stream - jedna položka = jeden člověk."""

    def setUp(self):
        self.home = Site.objects.get(is_default_site=True).root_page
        self.vr_group, _ = Group.objects.get_or_create(name=VR_MEMBER_GROUP_NAME)

    def _create_vr_member(self, username, first_name, last_name):
        user = create_user(username, first_name=first_name, last_name=last_name)
        create_profile(user)
        user.groups.add(self.vr_group)
        return user

    def test_agenda_item_can_have_several_presenters(self):
        anna = self._create_vr_member('vr1', 'Anna', 'Prvni')
        bara = self._create_vr_member('vr2', 'Bara', 'Druha')

        page = AgendaPage(
            title="Jednání VR",
            meeting_date=date(2026, 3, 1),
            participants=[],
            items=[{'type': 'item', 'value': {
                'heading': "Rozpočet",
                'presenter': [
                    {'type': 'vr_member', 'value': str(anna.pk)},
                    {'type': 'vr_member', 'value': str(bara.pk)},
                    {'type': 'other', 'value': "Hana Hostova"},
                ],
            }}],
        )
        self.home.add_child(instance=page)

        content = self.client.get(page.url).content.decode()
        self.assertIn('Prvni Anna', content)
        self.assertIn('Druha Bara', content)
        self.assertIn('Hana Hostova', content)

    def test_participants_are_listed(self):
        self._create_vr_member('vr3', 'Cyril', 'Treti')

        page = AgendaPage(
            title="Jednání VR",
            meeting_date=date(2026, 3, 1),
            participants=_default_participants(),
        )
        self.home.add_child(instance=page)

        self.assertIn('Treti Cyril', self.client.get(page.url).content.decode())
