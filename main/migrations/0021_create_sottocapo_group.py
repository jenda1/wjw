from django.db import migrations

from main.permissions import SOTTO_CAPO_GROUP_NAME


def create_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=SOTTO_CAPO_GROUP_NAME)


def delete_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=SOTTO_CAPO_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_mailinglist_pokladnici_view'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_group, delete_group),
    ]
