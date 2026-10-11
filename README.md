# Web Spoleku rodičů základní školy Waldorf Jinonice


## Install

```shell
pip install -e ".[dev,test]"
```


### Exim integration

- run as postgres user:

```sql
CREATE ROLE "Debian-exim" LOGIN;

GRANT CONNECT ON DATABASE wjw TO "Debian-exim";
GRANT USAGE ON SCHEMA public TO "Debian-exim";

GRANT SELECT ON main_mailinglist_members TO "Debian-exim";
GRANT SELECT ON main_mailinglist_vrmembers TO "Debian-exim";
GRANT SELECT ON main_mailinglist_class TO "Debian-exim";
GRANT SELECT ON main_mailinglist_admins TO "Debian-exim";

```

- config file for exim4:

```text
# /etc/exim4/conf.d/main/02_local_pgsql
pgsql_servers = (/var/run/postgresql/.s.PGSQL.5432)/wjw/Debian-exim/
```

```text
# /etc/exim4/conf.d/acl/35_local_mailinglist_senders
#
# Pravidlo: na aliasy (vr@..., trida-X@...) smí psát jen členovi/rodiči

deny
  message = Na tuto adresu mohou psát jen ověření členové spolku.
  log_message = mailinglist: odmitnut neznamy odesilatel $sender_address pro $local_part@$domain
  local_parts = vr : admins : ^trida-\d+[a-z]*$
  domains = +local_domains
  condition = ${lookup pgsql{SELECT 1 FROM main_mailinglist_members WHERE lower(trim(email)) = lower(trim('${quote_pgsql:$sender_address}')) LIMIT 1}{no}{yes}}

defer
  message = Na tento mailing list jde z vaší adresy příliš mnoho zpráv, zkuste to prosím později.
  log_message = mailinglist: ratelimit prekrocen pro $sender_address na $local_part@$domain
  local_parts = vr : admins : ^trida-\d+[a-z]*$
  domains = +local_domains
  ratelimit = 5 / 1h / strict / ${sender_address}:${local_part}
```



```text
# /etc/exim4/conf.d/router/100_local_mailinglists

vr_mailinglist:
  driver = redirect
  domains = +local_domains
  local_parts = vr
  skip_syntax_errors
  data = ${lookup pgsql{SELECT email FROM main_mailinglist_vrmembers}}

admins_mailinglist:
  driver = redirect
  domains = +local_domains
  local_parts = admins
  skip_syntax_errors
  # main_mailinglist_admins view (main/migrations/0018) = jen is_superuser=True,
  # nezávisle na main.Profile.
  data = ${lookup pgsql{SELECT email FROM main_mailinglist_admins}}

trida_mailinglist:
  driver = redirect
  domains = +local_domains
  local_parts = ^trida-\d+[a-z]*$
  allow_fail
  skip_syntax_errors
  data = ${if match{$local_part}{^trida-(\d+)([a-z]*)$}\
      {${lookup pgsql{\
          SELECT email FROM main_mailinglist_class \
          WHERE school_class = $1 \
          AND ( (variant IS NULL OR variant = '') AND '$2' = '' \
                OR lower(variant) = '$2' )\
        }}}\
      {:fail: neplatny format aliasu tridy}}

```
