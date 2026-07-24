from django.db import migrations

from main.permissions import WELCOMING_TEAM_GROUP_NAME


def create_welcomingteam_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=WELCOMING_TEAM_GROUP_NAME)


def delete_welcomingteam_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=WELCOMING_TEAM_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_historicalclasscollective_historicalprofile_and_more'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_welcomingteam_group, delete_welcomingteam_group),
    ]
