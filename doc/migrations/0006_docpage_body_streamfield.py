import uuid

import wagtail.fields
from django.db import migrations

BODY_STREAMFIELD = wagtail.fields.StreamField(
    [('paragraph', 0), ('table', 1)],
    blank=True,
    block_lookup={
        0: ('wagtail.blocks.RichTextBlock', (), {'label': 'Text'}),
        1: ('wagtail.contrib.table_block.blocks.TableBlock', (), {'label': 'Tabulka'}),
    },
    default=list,
    verbose_name='Obsah',
)


def copy_old_to_stream(apps, schema_editor):
    """`body` (RichTextField) a `body_stream` (nový StreamField) existují na chvíli vedle sebe -
    zkopíruje původní HTML jako jediný 'paragraph' blok, než se starý sloupec zahodí."""
    DocPage = apps.get_model('doc', 'DocPage')
    for page in DocPage.objects.all():
        old_body = page.body
        page.body_stream = [{'type': 'paragraph', 'value': old_body, 'id': str(uuid.uuid4())}] if old_body else []
        page.save(update_fields=['body_stream'])


def copy_stream_to_old(apps, schema_editor):
    """Zpětná migrace - vrátí text ze všech 'paragraph' bloků do RichTextField
    (obsah tabulek se při downgradu ztratí, tabulky ve staré verzi neexistovaly)."""
    DocPage = apps.get_model('doc', 'DocPage')
    for page in DocPage.objects.all():
        paragraphs = [child.value.source for child in page.body_stream if child.block_type == 'paragraph']
        page.body = '\n'.join(paragraphs)
        page.save(update_fields=['body'])


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0005_alter_agendapage_items'),
    ]

    operations = [
        # RichTextField obsahuje syrové HTML, které nesplňuje JSON_VALID constraint StreamFieldu -
        # přímý AlterField proto na existujících řádcích selže. Místo toho se vedle založí nové
        # pole, data se do něj zkopírují a staré pole se pak zahodí a nové přejmenuje na `body`.
        migrations.AddField(
            model_name='docpage',
            name='body_stream',
            field=BODY_STREAMFIELD,
            preserve_default=False,
        ),
        migrations.RunPython(copy_old_to_stream, copy_stream_to_old),
        migrations.RemoveField(
            model_name='docpage',
            name='body',
        ),
        migrations.RenameField(
            model_name='docpage',
            old_name='body_stream',
            new_name='body',
        ),
    ]
