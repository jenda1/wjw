from django.db import migrations

DROP_VIEW_SQL = "DROP VIEW main_mailinglist_members;"

# allauth SocialAccount.extra_data je JSONField - PostgreSQL (jsonb ->>) a sqlite
# (json_extract, používaný lokálně/v testech) mají pro přístup ke klíči jinou
# syntax, proto RunPython s větvením podle schema_editor.connection.vendor
# (stejný důvod jako u DROP+CREATE místo CREATE OR REPLACE VIEW v main/migrations/0019).

CREATE_VIEW_SQL_BY_VENDOR = {
    'postgresql': """
        CREATE VIEW main_mailinglist_members AS
        SELECT DISTINCT au.email AS email
        FROM auth_user au
        JOIN main_profile p ON p.user_id = au.id
        WHERE p.status = 'AC' AND au.email <> ''

        UNION

        SELECT DISTINCT sa.extra_data ->> 'email' AS email
        FROM socialaccount_socialaccount sa
        JOIN main_profile p ON p.user_id = sa.user_id
        WHERE p.status = 'AC'
          AND sa.extra_data ->> 'email' IS NOT NULL
          AND sa.extra_data ->> 'email' <> '';
    """,
    'sqlite': """
        CREATE VIEW main_mailinglist_members AS
        SELECT DISTINCT au.email AS email
        FROM auth_user au
        JOIN main_profile p ON p.user_id = au.id
        WHERE p.status = 'AC' AND au.email <> ''

        UNION

        SELECT DISTINCT json_extract(sa.extra_data, '$.email') AS email
        FROM socialaccount_socialaccount sa
        JOIN main_profile p ON p.user_id = sa.user_id
        WHERE p.status = 'AC'
          AND json_extract(sa.extra_data, '$.email') IS NOT NULL
          AND json_extract(sa.extra_data, '$.email') <> '';
    """,
}

ORIGINAL_CREATE_VIEW_SQL = """
    CREATE VIEW main_mailinglist_members AS
    SELECT DISTINCT au.email AS email
    FROM auth_user au
    JOIN main_profile p ON p.user_id = au.id
    WHERE p.status = 'AC' AND au.email <> '';
"""


def create_view_with_social_emails(apps, schema_editor):
    schema_editor.execute(DROP_VIEW_SQL)
    schema_editor.execute(CREATE_VIEW_SQL_BY_VENDOR[schema_editor.connection.vendor])


def revert_view(apps, schema_editor):
    schema_editor.execute(DROP_VIEW_SQL)
    schema_editor.execute(ORIGINAL_CREATE_VIEW_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_mailinglist_info_view'),
        ('socialaccount', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_view_with_social_emails, revert_view),
    ]
