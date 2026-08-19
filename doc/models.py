from datetime import time

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.formats import date_format
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from main.models import Profile
from main.permissions import VR_MEMBER_GROUP_NAME


class DocPageTag(TaggedItemBase):
    content_object = ParentalKey('DocPage', on_delete=models.CASCADE, related_name='tagged_items')


class DocPage(Page):
    """Obecná obsahová stránka."""

    body = RichTextField(blank=True)
    tags = ClusterTaggableManager(through=DocPageTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
        FieldPanel('tags'),
    ]


class AgendaPageTag(TaggedItemBase):
    content_object = ParentalKey('AgendaPage', on_delete=models.CASCADE, related_name='tagged_items')


def _vr_member_choices():
    """Aktuální členové skupiny VRmember."""
    users = (
        get_user_model().objects
        .filter(groups__name=VR_MEMBER_GROUP_NAME, profile__isnull=False)
        .select_related('profile')
        .order_by('first_name', 'last_name')
    )
    return [(str(user.pk), str(user.profile)) for user in users]


def _other_member_choices():
    """Aktivní členové spolku, kteří nejsou ve skupině VRmember."""
    users = (
        get_user_model().objects
        .filter(profile__status=Profile.ProfileStatus.ACTIVE)
        .exclude(groups__name=VR_MEMBER_GROUP_NAME)
        .select_related('profile')
        .order_by('first_name', 'last_name')
    )
    return [(str(user.pk), str(user.profile)) for user in users]


def _profile_display(user_id):
    if not user_id:
        return None
    user = (
        get_user_model().objects
        .filter(pk=user_id, profile__isnull=False)
        .select_related('profile')
        .first()
    )
    return str(user.profile) if user is not None else None


def person_display(person):
    """person je StreamValue s právě jedním blokem (viz Person.Meta.min_num/max_num)."""
    if not len(person):
        return ''
    block = person[0]
    if block.block_type in ('vr_member', 'member'):
        return _profile_display(block.value) or ''
    return block.value


class Person(blocks.StreamBlock):
    """Jedna osoba - buď člen VR, nebo jiný člen spolku, nebo (výjimečně) někdo mimo členy volným textem.
    Editor vybírá právě jednu z variant (max_num/min_num = 1), takže výlučnost je vynucená strukturou,
    ne až dodatečnou validací."""

    vr_member = blocks.ChoiceBlock(choices=_vr_member_choices, label="Člen VR")
    member = blocks.ChoiceBlock(choices=_other_member_choices, label="Jiný člen")
    other = blocks.CharBlock(max_length=255, label="Jiná osoba")

    class Meta:
        icon = "user"
        label = "Osoba"
        min_num = 1
        max_num = 1


class AgendaItemBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=255, label="Název bodu")
    presenter = blocks.ListBlock(Person(), min_num=1, label="Předkládá")
    body = blocks.RichTextBlock(required=False, label="Popis")
    outcome = blocks.RichTextBlock(required=False, label="Výstup")

    class Meta:
        icon = "list-ul"
        label = "Bod programu"


class AgendaItemsBlock(blocks.StreamBlock):
    """Body programu jednání VR. Další typy bodů (např. informativní blok bez
    předkladatele) lze v budoucnu přidat jako další pojmenované bloky sem."""

    item = AgendaItemBlock()

    class Meta:
        label = "Body programu"


def _default_participants():
    """Výchozí seznam účastníků nového jednání = aktuální členové skupiny VRmember.
    'id' u jednotlivých bloků se doplní automaticky při prvním uložení."""
    return [
        {'type': 'participant', 'value': [{'type': 'vr_member', 'value': pk}]}
        for pk, _ in _vr_member_choices()
    ]


class AgendaPage(Page):
    """Program jednání Výkonné rady - datum, místo konání a seznam bodů programu."""

    meeting_date = models.DateField(verbose_name="Datum jednání")
    meeting_time = models.TimeField(default=time(19, 0), verbose_name="Začátek")
    location = models.CharField(
        max_length=255, blank=True, default="sborovna v hlavní budově", verbose_name="Místo konání"
    )
    tags = ClusterTaggableManager(through=AgendaPageTag, blank=True)
    participants = StreamField(
        [('participant', Person())],
        blank=True,
        default=_default_participants,
        verbose_name="Seznam účastníků",
    )
    items = StreamField(AgendaItemsBlock(), blank=True, verbose_name="Body programu")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Výchozí titulek pro nově vytvářenou (dosud neuloženou) stránku - title je zděděné
        # konkrétní pole z wagtailcore.Page, takže ho nejde přepsat jako model field s default=.
        if self.pk is None and not self.title:
            self.title = "Jednání VR"

    @property
    def display_title(self):
        """Titulek doplněný o datum jednání, použitý na frontendu místo holého page.title."""
        if not self.meeting_date:
            return self.title
        return f"{self.title} ({date_format(self.meeting_date, 'j.n.Y')})"

    content_panels = Page.content_panels + [
        FieldPanel('meeting_date'),
        FieldPanel('meeting_time'),
        FieldPanel('location'),
        FieldPanel('tags'),
        FieldPanel('participants'),
        FieldPanel('items'),
    ]
