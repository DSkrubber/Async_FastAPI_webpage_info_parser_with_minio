FROM python:3.8-slim as base


WORKDIR /opt/application

RUN apt update && apt install -y curl
RUN export POETRY_HOME=/opt/poetry && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - \
  && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry update && poetry install --no-root

COPY ./app ./app


FROM base as build

CMD poetry run uvicorn --host "0.0.0.0" --port 8082 app.main:app


FROM base as dev

CMD poetry run uvicorn --host "0.0.0.0" --port 8082 app.main:app --reload
