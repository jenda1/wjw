from django.db import migrations

from main.permissions import CAPO_DI_TUTTI_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=CAPO_DI_TUTTI_GROUP_NAME)
    Group.objects.get_or_create(name=SECRETARY_OF_THE_TREASURY_GROUP_NAME)


def delete_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=[CAPO_DI_TUTTI_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_classrepresentative_classcollective_representatives_and_more'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]
