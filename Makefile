build-dev:
	docker build --target dev -t application .

up-build:
	docker-compose up -d --build


down:
	docker-compose down

commit:
	cz commit