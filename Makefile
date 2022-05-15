build:
	DOCKER_BUILDKIT=1 docker build --target build -t web ./web && DOCKER_BUILDKIT=1 docker build --target build -t parser ./parser

build_dev:
	DOCKER_BUILDKIT=1 docker build --target build_dev -t web ./web && DOCKER_BUILDKIT=1 docker build --target build_dev -t parser ./parser

test:
	docker build --target test -t web:test ./web && docker build --target test -t parser:test ./parser

up:
	docker-compose up -d

down:
	docker-compose down

down_volume:
	docker-compose down -v

requirements:
	cd web && poetry export -o requirements.txt --dev && cd ../parser && poetry export -o requirements.txt --dev && cd ..

upgrade:
	cd web && poetry run alembic upgrade head && cd ..

downgrade:
	cd web && poetry run alembic downgrade -1 && cd ..

downgrade_full:
	cd web && poetry run alembic downgrade base && cd ..

openapi:
	cd web && poetry run python -m documentation.openapi_yaml_generator && cd ..

commit:
	cz commit
