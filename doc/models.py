from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

NASTENKA_MENU_TAG = "nastenka"


class DocPageTag(TaggedItemBase):
    content_object = ParentalKey('DocPage', on_delete=models.CASCADE, related_name='tagged_items')


class DocPage(Page):
    """Obecná obsahová stránka. Přidáním tagu "nastenka" se stránka objeví
    v menu Nástěnka na hlavní stránce - viz main.context_processors.nastenka_pages."""

    body = RichTextField(blank=True)
    tags = ClusterTaggableManager(through=DocPageTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
        FieldPanel('tags'),
    ]
