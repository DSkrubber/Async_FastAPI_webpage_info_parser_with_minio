FROM python:3.8-slim as base

WORKDIR /opt/web
RUN apt update && apt install -y curl
RUN export POETRY_HOME=/opt/poetry && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - \
  && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry
COPY poetry.lock pyproject.toml alembic.ini ./
RUN poetry config virtualenvs.create false
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./documentation/openapi.yaml ./documentation/


FROM base AS build

RUN poetry update && poetry install --no-root --no-dev
CMD alembic upgrade head && uvicorn app.main:app --host ${APP_HOST:-"0.0.0.0"} --port ${APP_PORT:-8080}


FROM base AS test

RUN poetry update && poetry install --no-root
COPY ./tests ./tests
RUN isort --check --profile=black --line-length=79 .
RUN black --check --line-length=79 .
RUN flake8 .
RUN mypy --ignore-missing-imports --scripts-are-modules --allow-untyped-decorators --strict --no-strict-optional app/
RUN pylint --max-line-length=79 --errors-only --disable=E0401,E0611 app/
RUN python3 -m pytest --cov=app tests/


FROM base AS build_dev

RUN poetry update && poetry install --no-root
CMD alembic upgrade head && uvicorn app.main:app --host ${APP_HOST:-"0.0.0.0"} --port ${APP_PORT:-8080} --reload
