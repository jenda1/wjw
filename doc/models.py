from datetime import time

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.formats import date_format
from django.utils.functional import cached_property
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
    """person je jeden blok ze streamu osob (viz People)."""
    if person.block_type in ('vr_member', 'member'):
        return _profile_display(person.value) or ''
    return person.value


class People(blocks.StreamBlock):
    """Seznam osob - každá položka streamu je jeden člověk: buď člen VR, nebo jiný člen spolku,
    nebo (výjimečně) někdo mimo členy volným textem. Osoba a volba varianty jsou jeden a týž blok,
    takže výlučnost variant je vynucená strukturou (ne dodatečnou validací) a editor přidává
    další osobu pořád stejným tlačítkem - žádné vnořené 'přidat' s limitem jedné položky."""

    vr_member = blocks.ChoiceBlock(choices=_vr_member_choices, label="Člen VR")
    member = blocks.ChoiceBlock(choices=_other_member_choices, label="Jiný člen")
    other = blocks.CharBlock(max_length=255, label="Jiná osoba")

    class Meta:
        icon = "user"
        label = "Osoby"


class AgendaItemBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=255, label="Název bodu")
    presenter = People(min_num=1, label="Předkládá")
    item = blocks.RichTextBlock(required=False, label="Popis")
    discussion = blocks.RichTextBlock(required=False, label="Debata")
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


AGENDA_DISPLAY_FIELDS = ('item', 'outcome')


def _default_participants():
    """Výchozí seznam účastníků nového jednání = aktuální členové skupiny VRmember.
    'id' u jednotlivých bloků se doplní automaticky při prvním uložení."""
    return [{'type': 'vr_member', 'value': pk} for pk, _ in _vr_member_choices()]


class AgendaPage(Page):
    """Program jednání Výkonné rady - datum, místo konání a seznam bodů programu."""

    meeting_date = models.DateField(verbose_name="Datum jednání")
    meeting_time = models.TimeField(default=time(19, 0), verbose_name="Začátek")
    location = models.CharField(
        max_length=255, blank=True, default="sborovna v hlavní budově", verbose_name="Místo konání"
    )
    tags = ClusterTaggableManager(through=AgendaPageTag, blank=True)
    participants = StreamField(
        People(),
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

    def _display_title(self, title):
        if not self.meeting_date:
            return title
        return f"{title} ({date_format(self.meeting_date, 'j.n.Y')})"

    @property
    def display_title(self):
        """Titulek doplněný o datum jednání, použitý na frontendu místo holého page.title."""
        return self._display_title(self.title)

    @cached_property
    def numbered_items(self):
        """Bloky z `items` doplněné o pořadové číslo bodu programu - používá se
        pro přehled na začátku stránky i pro číslování v samotném výpisu bodů."""
        return [{'block': block, 'number': number} for number, block in enumerate(self.items, start=1)]

    def get_context(self, request, *args, **kwargs):
        """`zobrazit=item`/`zobrazit=outcome` v query stringu omezí výpis jen na daný typ
        obsahu (popis, nebo výstup) - pro rychlý přehled bez zbytku zápisu."""
        context = super().get_context(request, *args, **kwargs)
        zobrazit = request.GET.get('zobrazit')
        context['zobrazit'] = zobrazit if zobrazit in AGENDA_DISPLAY_FIELDS else None
        return context

    def get_admin_display_title(self):
        """Stejné doplnění o datum jednání i v adminu (explorer, vyhledávání, breadcrumbs) -
        podle draft_title, aby se projevily i needzveřejněné změny názvu."""
        return self._display_title(self.draft_title or self.title)

    content_panels = Page.content_panels + [
        FieldPanel('meeting_date'),
        FieldPanel('meeting_time'),
        FieldPanel('location'),
        FieldPanel('tags'),
        FieldPanel('participants'),
        FieldPanel('items'),
    ]
