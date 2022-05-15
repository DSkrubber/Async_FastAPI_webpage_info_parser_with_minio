### Project description

* **This application allows you to get some information and download images from provided array of websites.
  This project tries to use asynchronous functions, libraries, and tools (`aiohttp`, `aiokafka`, `asyncio`, `aiobotocore`, `asyncpg`) 
  where it is possible - to speed up parsing.**


* **There are two main microservices - `web` to interact with client and `parser` - 
  to parse data for webpages (as for now - get html length) and upload webpage images to minio storage. Microservices communicate with each other via kafka topics 
  (both microservices have producer and consumer). You could monitor kafka cluster by using `provectuslabs/kafka-ui` dashboard.**


* **For each of website - there will be created a row in Postgresql database using asyncpg driver. You will get website data as well as 
  parsing status (which will be `UPDATED` to different statuses `pending `-> `in_progress` -> `finished/failed` while parsing).**


* **All database connections could be made by `web` microservice only, while both `web` and `minio` interact with minio. 
  You will be able to `POST` website entity (which will trigger data parsing as well), `GET` info for each website (with updating data) and 
  `DELETE` website entities (all minio data for this website will be deleted as well).**


* **After uploading images to minio you could request S3 `presigned urls` to be able to download this images.**


### Prerequisites

* Make sure that you have installed the latest versions of `python` and `pip` on your computer. 
  Also, you have to install [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/).
  
  *Note: each microservice - `parser` and `web` has own `Dockerfile` and `.dockerignore` with appropriate build stages.*


* This project by default uses [poetry](https://python-poetry.org/) for dependency and virtual environment management.
  Make sure to install it too.

  *Note: each microservice - `parser` and `web` has own poetry files and dependencies specified.*


* Make sure to provide all required environment variables (via `.env` file, `export` command, secrets, etc.) before running application.

  *Note: each microservice - `parser` and `web` should have own .env/secrets variables specified.*


### Development tools

1) For managing pre-commit hooks this project uses [pre-commit](https://pre-commit.com/).


2) For import sorting this project uses [isort](https://pycqa.github.io/isort/).


3) For code format checking this project uses [black](https://github.com/psf/black).


4) For code linting this project uses [flake8](https://flake8.pycqa.org/en/latest/) and [pylint](https://pypi.org/project/pylint/).


5) For type checking his project uses [mypy](https://github.com/python/mypy)


6) For create commits and lint commit messages this project uses [commitizen](https://commitizen-tools.github.io/commitizen/).
   Run `make commit` to use commitizen during commits.


7) There is special `build_dev` stage in Docker file to build dev version of application image.


8) Because there are two separate microservices, all `pre-commit` and Docker `test` build stage checks run both for 
   `parser` and `web` microservices from repo root.


9) New application version should be specified in `web/version.txt` file to update `web` microservice openapi documentation.


### CI/CD

* This project involves [github actions](https://docs.github.com/en/actions) to run all checks and unit-tests on `push` to remote repository.

* There will be two jobs running in one workflow - for `parser` and `web` microservices (built from each of directories separately via `strategy.matrix`).


### Make commands

There are lots of useful commands in `Makefile` included into this project's repo. Use `make <some_command>` syntax to run each of them. 
If your system doesn't support make commands - you may copy commands from `Makefile` directly into terminal.

*Note: there are many commands that will perform actions both for `parser` and `web` microservice. Even so, all Makefile commands 
should be run from repo root directory only.*


### Installation

1) To install all the required dependencies and set up a virtual environment run in the cloned repository directory use:

   `poetry install`

   You can also install project dependencies using `pip install -r requirements.txt` from repo root directory.
   
   *Note: this command will install ALL dependencies for the project - both for `parser` and `web` microservice. 
   Separate dependencies will be installed automatically during Docker image build (or github actions run).*


2) To config pre-commit hooks for code linting, code format checking and linting commit messages run in the cloned directory:

   `poetry run pre-commit install`


3) Build app images (for `parser` and `web`) using

   `make build`

   To build reloadable application locally use `make build_dev` to build images in development environment.


4) Run all necessary Docker containers together using

   `make up`

   Containers will start depending on each other and considering health checks.
   
   *Note: this will also create and attach persistent named volume `logs` for Docker containers. 
   Containers will use this volume to store application `app.log` file.*


5) Stop and remove Docker containers using

    `make down`

    If you also want to remove log volume use `make down_volume`


### Database migrations

* For managing migrations this project uses [alembic](https://alembic.sqlalchemy.org/en/latest/).


* Dockerfile for `web` microservice already includes `alembic upgrade head` command to run all revision migrations, 
  required by current version of application.


* Run `make upgrade` to manually upgrade database tables state. You could also manually upgrade to specific revision with `.py` script 
  (from `web/alembic/versions/`) by running:

  `alembic upgrade <revision id number>`


* You could also downgrade one revision down with `make downgrade` command, to specific revision - by running 
  `alembic downgrade <revision id number>`, or make full downgrade 
  to initial database state with:
  
  `make downgrade_full`


### Running app

1) By default, web application will be accessible at http://localhost:8080, minio storage console - at http://localhost:9001, 
   database - at http://localhost:5432, kafka cluster UI - at http://localhost:9093. You can try all endpoints with SWAGGER
   documentation at http://localhost:8080/docs

   *Note: `parser` microservice will run at http://localhost:8081 but user don't need to interact with it directly.*


2) Make sure to create minio bucket (specified in your .env/secrets) before interaction with web application resources.


3) Use `/websites` resource with `POST` method to create database entities for each URL and start parsing. 
   Created entities with ids will return in response body.
   ![/websites request](https://user-images.githubusercontent.com/79688463/168489151-f4eb9e67-8acb-4e60-ba58-10a47cb5a69e.png)
   ![/websites response](https://user-images.githubusercontent.com/79688463/168489154-4e818f79-40ce-49c4-9aab-bb1e1086a437.png)

2) Use `/websites/{website_id}` resource with `GET` or `DELETE` method to get and delete row in database respectivelly.
   Use get to monitor status of parsing and data updates. Delete also clears minio storage objects associated with URL
   (website URL is used as prefix for picture keys of this webpage)
   ![/websites/{website_id}](https://user-images.githubusercontent.com/79688463/168489157-2eb67fc7-abd2-4abf-bdd8-7fda1d2f1b31.png)


4) Use `/websites/{website_id}/picture_links` to get website database entity with generated S3 presigned URLs array in response body.
   You could use some tool (e.g. POSTMAN, wget, curl, etc.) to download this images via generated URL. URL will expire after 5 minutes.
   ![/websites/{website_id}/picture_links](https://user-images.githubusercontent.com/79688463/168489160-f33d3ced-086e-4e5f-91b3-19a4f41ddc48.png)


### Documentation

* Description of all project's endpoints and API may be viewed without running any services from `documentation/openapi.yaml` file


* You can update web/documentation/openapi.yaml documentation for API at any time by using `make openapi` command.


* All warnings and info messages will be shown in container's stdout and saved in `web.log` and `parser.log` files.


* To minimize chances to be blocked `parser` uses custom user-agents for request headers from `parser/documentation/user_agents.txt` file.


### Running tests.


* Use `make test` to build test images for `parser` and `web` microservices and run all linters checks and unit-tests for each of them. 
  

* After all tests [coverage report](https://pytest-cov.readthedocs.io/en/latest/) will be also shown.


* Staged changes will be checked during commits via pre-commit hook.


* All checks and tests (both for `parser` and `web` microservices) will run on code push to remote repository as part of github actions.
