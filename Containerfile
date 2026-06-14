# builder
FROM python:3.11-slim AS builder

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

RUN uv venv /opt/venv && uv sync --no-dev --no-install-project

# Zkopírování zdrojového kódu aplikace
COPY wjw/ /app/wjw/
COPY templates /app/templates/
COPY main/ /app/main/
COPY users/ /app/users/
COPY manage.py pyproject.toml /app/

RUN uv pip install --no-deps .


# finalni obraz
FROM python:3.11-slim AS runner

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

# Sběr statických souborů (všechny příkazy nyní automaticky běží ve venv díky PATH)
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

# Spuštění aplikace (Gunicorn musí být součástí pyproject.toml)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wjw.wsgi:application"]
