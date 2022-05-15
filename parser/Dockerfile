FROM python:3.8-slim as base

WORKDIR /opt/parser
RUN apt update && apt install -y curl
RUN export POETRY_HOME=/opt/poetry && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - \
  && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false
COPY ./app ./app
COPY ./documentation/user_agents.txt ./documentation/


FROM base AS build

RUN poetry update && poetry install --no-root --no-dev
CMD poetry run python -m app.main


FROM base AS test

RUN poetry update && poetry install --no-root
COPY tests ./tests
RUN isort --check --profile=black --line-length=79 .
RUN black --check --line-length=79 .
RUN flake8 .
RUN mypy --ignore-missing-imports --scripts-are-modules --allow-untyped-decorators --strict --no-strict-optional --exclude tests/ .
RUN pylint --max-line-length=79 --errors-only --disable=E0401,E0611 .
RUN python3 -m pytest --cov=parser tests/


FROM base AS build_dev

RUN poetry update && poetry install --no-root
CMD poetry run python -m app.main
