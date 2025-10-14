PWD := $(shell pwd)

build:
	docker build -t m-e-w.dev/docker-dash:latest .

run:
	docker run -d --name docker-dash -p 127.0.0.1:8050:8050 -v $(PWD)/data:/app/data:ro m-e-w.dev/docker-dash:latest

stop:
	docker stop docker-dash || true
	docker rm docker-dash || true
