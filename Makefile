.PHONY: build run clean

build:
	docker-compose build

run: build
	docker-compose up

clean:
	docker-compose rm -f db
