from django.db import migrations

from main.permissions import KOLEGIUM_GROUP_NAME


def create_kolegium_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=KOLEGIUM_GROUP_NAME)


def delete_kolegium_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=KOLEGIUM_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_update_site_domain'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_kolegium_group, delete_kolegium_group),
    ]
