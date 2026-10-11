from django.db import migrations

from main.permissions import VR_MEMBER_GROUP_NAME

CREATE_VIEWS_SQL = f"""
-- Všichni aktivní členové s e-mailem - slouží jako "allow-list" odesílatelů
-- pro mailing listy (viz exim ACL), aby na ně nemohl psát kdokoli zvenčí.
CREATE VIEW main_mailinglist_members AS
SELECT DISTINCT au.email AS email
FROM auth_user au
JOIN main_profile p ON p.user_id = au.id
WHERE p.status = 'AC' AND au.email <> '';

-- Příjemci pro alias vr@... (skupina {VR_MEMBER_GROUP_NAME}).
CREATE VIEW main_mailinglist_vrmembers AS
SELECT DISTINCT au.email AS email
FROM auth_user au
JOIN auth_user_groups aug ON aug.user_id = au.id
JOIN auth_group ag ON ag.id = aug.group_id
JOIN main_profile p ON p.user_id = au.id
WHERE ag.name = '{VR_MEMBER_GROUP_NAME}' AND p.status = 'AC' AND au.email <> '';

-- Příjemci pro aliasy trida-<rocnik><varianta>@... - zákonní zástupci aktuálně
-- zapsaných žáků dané třídy (platný ParentRelationship k dnešnímu dni).
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

-- Příjemci pro alias admins@... - jen skuteční superuživatelé (is_superuser),
-- bez ohledu na to, jestli mají (nebo nemají) navázaný main.Profile.
CREATE VIEW main_mailinglist_admins AS
SELECT DISTINCT au.email AS email
FROM auth_user au
WHERE au.is_superuser = true AND au.email <> '';
"""

DROP_VIEWS_SQL = """
DROP VIEW IF EXISTS main_mailinglist_admins;
DROP VIEW IF EXISTS main_mailinglist_class;
DROP VIEW IF EXISTS main_mailinglist_vrmembers;
DROP VIEW IF EXISTS main_mailinglist_members;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_historicalprofile_phone_visible_and_more'),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_VIEWS_SQL, reverse_sql=DROP_VIEWS_SQL),
    ]
