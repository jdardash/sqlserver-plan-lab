.PHONY: up seed run test down clean

up:
	docker compose up -d
	@until [ "$$(docker inspect --format '{{.State.Health.Status}}' planlab-mssql)" = "healthy" ]; do \n		printf '.'; sleep 2; \n	done; echo " ready"

seed: up
	python -m lab seed

run: seed
	python -m lab run

test:
	python -m pytest tests/ -q

down:
	docker compose down

clean: down
	rm -rf results/*.sqlplan
