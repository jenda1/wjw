from django.db import migrations

# DROP+CREATE (ne "CREATE OR REPLACE VIEW") - to je PostgreSQL-specifická
# syntax, kterou sqlite (používaný lokálně/v testech) nezná.
ADD_YEAR_SQL = """
DROP VIEW main_mailinglist_class;

-- Doplňuje "year" - umožňuje druhý mailing list pro stejnou třídu podle roku
-- nástupu (<rok><varianta>@...), který se na rozdíl od adresy podle ročníku
-- nemění při postupu do dalšího ročníku.
CREATE VIEW main_mailinglist_class AS
SELECT DISTINCT
    cc.school_class AS school_class,
    cc.variant AS variant,
    au.email AS email,
    cc.year AS year
FROM main_classcollective cc
JOIN main_student s ON s.school_class_id = cc.id
JOIN main_parentrelationship pr ON pr.student_id = s.id
JOIN main_profile p ON p.id = pr.parent_id
JOIN auth_user au ON au.id = p.user_id
WHERE p.status = 'AC'
  AND au.email <> ''
  AND (pr.valid_until IS NULL OR pr.valid_until >= CURRENT_DATE);
"""

REVERT_YEAR_SQL = """
DROP VIEW main_mailinglist_class;

CREATE VIEW main_mailinglist_class AS
SELECT DISTINCT
    cc.school_class AS school_class,
    cc.variant AS variant,
    au.email AS email
FROM main_classcollective cc
JOIN main_student s ON s.school_class_id = cc.id
JOIN main_parentrelationship pr ON pr.student_id = s.id
JOIN main_profile p ON p.id = pr.parent_id
JOIN auth_user au ON au.id = p.user_id
WHERE p.status = 'AC'
  AND au.email <> ''
  AND (pr.valid_until IS NULL OR pr.valid_until >= CURRENT_DATE);
"""


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_set_username_format'),
    ]

    operations = [
        migrations.RunSQL(sql=ADD_YEAR_SQL, reverse_sql=REVERT_YEAR_SQL),
    ]
