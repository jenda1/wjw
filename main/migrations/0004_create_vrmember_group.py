from django.db import migrations

from main.permissions import VR_MEMBER_GROUP_NAME


def create_vrmember_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=VR_MEMBER_GROUP_NAME)


def delete_vrmember_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=VR_MEMBER_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_create_welcomingteam_group'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_vrmember_group, delete_vrmember_group),
    ]
