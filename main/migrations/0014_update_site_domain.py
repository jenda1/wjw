from django.db import migrations

DOMAIN = 'spolek.waldorfjinonice.cz'
NAME = 'Spolek waldorfská školy v Jinonicích'


def update_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(id=1, defaults={'domain': DOMAIN, 'name': NAME})


def revert_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(id=1).update(domain='example.com', name='example.com')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_alter_classcollective_options_and_more'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(update_site, revert_site),
    ]
