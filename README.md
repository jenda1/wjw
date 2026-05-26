# Waldorf Jinonice Web


## Install

```shell
pip install -e ".[dev,test]"
```

### .env

    DEBUG=False
    SECRET_KEY=...
    DATABASE_URL=sqlite:///db.sqlite3
    GOOGLE_OAUTH_CLIENT_ID=...
    GOOGLE_OAUTH_CLIENT_SECRET=...

## Schema

```shell
python manage.py graph_models prispevky --no-inheritance --hide-relations-from-fields -o schema.png
```

