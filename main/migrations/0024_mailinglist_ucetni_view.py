from django.db import migrations

from main.permissions import SECRETARY_OF_THE_TREASURY_GROUP_NAME

CREATE_VIEW_SQL = f"""
-- Příjemci pro alias ucetni@... - hospodář(ka) spolku (skupina {SECRETARY_OF_THE_TREASURY_GROUP_NAME}).
-- Stejně jako info@ (main/migrations/0022) ho exim ACL nekontroluje proti
-- main_mailinglist_members - smí na něj psát i nečlenové (veřejný kontakt).
CREATE VIEW main_mailinglist_ucetni AS
SELECT DISTINCT au.email AS email
FROM auth_user au
JOIN main_profile p ON p.user_id = au.id
WHERE p.status = 'AC' AND au.email <> ''
  AND au.id IN (
      SELECT aug.user_id FROM auth_user_groups aug
      JOIN auth_group ag ON ag.id = aug.group_id
      WHERE ag.name = '{SECRETARY_OF_THE_TREASURY_GROUP_NAME}'
  );
"""

DROP_VIEW_SQL = """
DROP VIEW main_mailinglist_ucetni;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_mailinglist_members_social_emails'),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_VIEW_SQL, reverse_sql=DROP_VIEW_SQL),
    ]
