from django.db import migrations

from main.permissions import SECRETARY_OF_THE_TREASURY_GROUP_NAME

# main.models.ClassRepresentative.RepresentantType.TREASURER - hodnota se
# (stejně jako 'AC' pro Profile.ProfileStatus.ACTIVE v main/migrations/0017)
# zapisuje natvrdo, aby migrace nezávisela na současné definici modelu.
TREASURER_CODE = 'P'

CREATE_VIEW_SQL = f"""
-- Příjemci pro alias pokladnici@... - aktuální třídní pokladníci
-- (main_classrepresentative, platný záznam k dnešnímu dni) a/nebo členové
-- skupiny {SECRETARY_OF_THE_TREASURY_GROUP_NAME} (hlavní pokladník spolku).
CREATE VIEW main_mailinglist_pokladnici AS
SELECT DISTINCT au.email AS email
FROM auth_user au
JOIN main_profile p ON p.user_id = au.id
WHERE p.status = 'AC' AND au.email <> ''
  AND (
    p.id IN (
        SELECT cr.representative_id FROM main_classrepresentative cr
        WHERE cr.representant_type = '{TREASURER_CODE}'
          AND (cr.valid_until IS NULL OR cr.valid_until >= CURRENT_DATE)
    )
    OR au.id IN (
        SELECT aug.user_id FROM auth_user_groups aug
        JOIN auth_group ag ON ag.id = aug.group_id
        WHERE ag.name = '{SECRETARY_OF_THE_TREASURY_GROUP_NAME}'
    )
  );
"""

DROP_VIEW_SQL = """
DROP VIEW main_mailinglist_pokladnici;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_mailinglist_class_add_year'),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_VIEW_SQL, reverse_sql=DROP_VIEW_SQL),
    ]
