from datetime import date, time

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.table_block.blocks import DEFAULT_TABLE_OPTIONS, TableBlock
from wagtail.fields import StreamField
from wagtail.models import Page

from main.models import ClassRepresentative, Profile
from main.permissions import CAPO_DI_TUTTI_GROUP_NAME, KOLEGIUM_GROUP_NAME, VR_MEMBER_GROUP_NAME


class DocPageTag(TaggedItemBase):
    content_object = ParentalKey('DocPage', on_delete=models.CASCADE, related_name='tagged_items')


class SubpagesBlock(blocks.StaticBlock):
    """Blok bez nastavení - při zobrazení stránky automaticky vypíše odkazy na její
    živé podstránky (v pořadí, jak jsou v adminu zařazené ve stromu stránek)."""

    class Meta:
        label = "Odkazy na podstránky"
        icon = "list-ul"
        template = "doc/blocks/subpages_block.html"
        admin_text = "Při zobrazení stránky se automaticky vypíší odkazy na všechny živé podstránky - nic se nevybírá ručně."


class DocBodyBlock(blocks.StreamBlock):
    """Obsah obecné stránky - text, tabulky a odkazy na podstránky lze v libovolném pořadí a počtu prostřídat."""

    paragraph = blocks.RichTextBlock(label="Text")
    table = TableBlock(
        label="Tabulka",
        table_options={
            "mergeCells": True,
            "contextMenu": DEFAULT_TABLE_OPTIONS["contextMenu"] + [
                "---------",
                "mergeCells",
                "alignment",
            ],
        },
    )
    subpages = SubpagesBlock()


class DocPage(Page):
    """Obecná obsahová stránka."""

    body = StreamField(DocBodyBlock(), blank=True, verbose_name="Obsah")
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


def _currently_valid(today=None):
    return models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=today or date.today())


def _vr_role_display(user_id):
    """Funkce člena VR pro zobrazení v závorce za jménem - stejná pravidla jako řazení
    do sekcí v main.views.show_vr (předseda, zástupce třídy/tříd, kolegium)."""
    user = (
        get_user_model().objects
        .filter(pk=user_id, profile__isnull=False)
        .select_related('profile')
        .prefetch_related('groups')
        .first()
    )
    if user is None:
        return ''

    group_names = {group.name for group in user.groups.all()}
    classes = [
        rep.school_class
        for rep in ClassRepresentative.objects.filter(
            _currently_valid(),
            representant_type=ClassRepresentative.RepresentantType.VR,
            representative=user.profile,
        ).select_related('school_class').order_by('school_class__school_class', 'school_class__variant')
    ]

    roles = []
    if CAPO_DI_TUTTI_GROUP_NAME in group_names:
        roles.append("předseda spolku")
    roles.extend(f"zástupce {class_collective}" for class_collective in classes)
    if KOLEGIUM_GROUP_NAME in group_names:
        roles.append("kolegium")
    return ", ".join(roles)


_HOST_LABEL = mark_safe("<strong>host</strong>")  # noqa: S308 - pevný literál, nic z uživatelského vstupu


def person_display(person):
    """person je jeden blok ze streamu osob (viz People). Za jméno se do závorky doplní
    funkce ve VR (u člena VR), nebo tučně 'host' (u kohokoliv, kdo není z VR)."""
    if person.block_type == 'vr_member':
        display = _profile_display(person.value)
        if not display:
            return ''
        role = _vr_role_display(person.value)
        return format_html("{} ({})", display, role) if role else display
    if person.block_type == 'member':
        display = _profile_display(person.value)
        if not display:
            return ''
        return format_html("{} ({})", display, _HOST_LABEL)
    return format_html("{} ({})", person.value, _HOST_LABEL)


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
    """Výchozí seznam účastníků nového jednání = aktuální členové skupiny VRmember -
    nejprve zástupci jednotlivých tříd (seřazení podle ročníku zastupované třídy),
    pak zbylí členové VR v abecedním pořadí. 'id' u jednotlivých bloků se doplní
    automaticky při prvním uložení."""
    class_rep_pks: list[str] = []
    for rep in ClassRepresentative.objects.filter(
        _currently_valid(),
        representant_type=ClassRepresentative.RepresentantType.VR,
        representative__user__groups__name=VR_MEMBER_GROUP_NAME,
    ).select_related('representative__user', 'school_class').order_by(
        'school_class__school_class', 'school_class__variant'
    ):
        pk = str(rep.representative.user_id)
        if pk not in class_rep_pks:
            class_rep_pks.append(pk)

    other_pks = [pk for pk, _ in _vr_member_choices() if pk not in class_rep_pks]
    return [{'type': 'vr_member', 'value': pk} for pk in class_rep_pks + other_pks]


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
    excused = StreamField(
        People(),
        blank=True,
        verbose_name="Omluveni",
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
        FieldPanel('excused'),
        FieldPanel('items'),
    ]
