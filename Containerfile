# builder
FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalace systémových závislostí nutných pro kompilaci
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock* ./

# VIRTUAL_ENV je potřeba i pro `uv pip` níže — UV_PROJECT_ENVIRONMENT platí jen pro `uv sync`.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV VIRTUAL_ENV=/opt/venv
RUN uv venv /opt/venv && uv sync --no-dev --no-install-project

# Zkopírování zdrojového kódu aplikace
# Všechny aplikace z INSTALLED_APPS (wjw/settings.py) + prispevky (zatím bez URL,
# ale je součástí balíčku podle [tool.setuptools.packages.find]).
COPY wjw/ /app/wjw/
COPY templates /app/templates/
COPY main/ /app/main/
COPY doc/ /app/doc/
COPY prispevky/ /app/prispevky/
COPY seznam_provider/ /app/seznam_provider/
COPY manage.py pyproject.toml README.md /app/

RUN uv pip install --no-deps .


# finalni obraz
FROM python:3.13-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Aktivace virtuálního prostředí vytvořeného v první fázi
ENV PATH="/opt/venv/bin:$PATH"

# Instalace runtime knihoven pro PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Zkopírování celého virtuálního prostředí z builder fáze (neobsahuje uv ani build tools)
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Vytvoření ne-root uživatele pro bezpečnost
RUN useradd -u 1001 django-user && chown -R django-user:django-user /app
USER django-user

# Sběr statických souborů (všechny příkazy nyní automaticky běží ve venv díky PATH).
# Proměnné jsou jen zástupné hodnoty pro build – za běhu je dodá prostředí kontejneru.
RUN SECRET_KEY=build-time-dummy DEBUG=False DATABASE_URL="sqlite:///:memory:" \
    python manage.py collectstatic --noinput --clear

EXPOSE 8000

# Spuštění aplikace (Gunicorn musí být součástí pyproject.toml)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wjw.wsgi:application"]
