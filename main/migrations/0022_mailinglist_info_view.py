from django.db import migrations

from main.permissions import (
    CAPO_DI_TUTTI_GROUP_NAME,
    SECRETARY_OF_THE_TREASURY_GROUP_NAME,
    SOTTO_CAPO_GROUP_NAME,
)

GROUP_NAMES = (CAPO_DI_TUTTI_GROUP_NAME, SOTTO_CAPO_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME)

CREATE_VIEW_SQL = f"""
-- Příjemci pro alias info@... - předseda, místopředseda a hospodář(ka) spolku.
-- Na rozdíl od ostatních aliasů ho exim ACL nekontroluje proti
-- main_mailinglist_members - smí na něj psát i nečlenové (veřejný kontakt).
CREATE VIEW main_mailinglist_info AS
SELECT DISTINCT au.email AS email
FROM auth_user au
JOIN main_profile p ON p.user_id = au.id
WHERE p.status = 'AC' AND au.email <> ''
  AND au.id IN (
      SELECT aug.user_id FROM auth_user_groups aug
      JOIN auth_group ag ON ag.id = aug.group_id
      WHERE ag.name IN ({', '.join(f"'{name}'" for name in GROUP_NAMES)})
  );
"""

DROP_VIEW_SQL = """
DROP VIEW main_mailinglist_info;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_create_sottocapo_group'),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_VIEW_SQL, reverse_sql=DROP_VIEW_SQL),
    ]
