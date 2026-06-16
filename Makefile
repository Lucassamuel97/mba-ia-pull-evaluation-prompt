.PHONY: help up down build pull push evaluate experiment test shell logs

help:
	@echo "Targets:"
	@echo "  make up        - Sobe o container (build + up -d)"
	@echo "  make down      - Para o container"
	@echo "  make build     - Rebuild da imagem"
	@echo "  make pull      - Faz pull do prompt v1 do LangSmith Hub"
	@echo "  make push      - Faz push do prompt v2 otimizado (publico)"
	@echo "  make evaluate  - Roda a avaliacao das 5 metricas (terminal)"
	@echo "  make experiment- Publica um Experiment formal no LangSmith (dashboard)"
	@echo "  make test      - Roda os testes pytest"
	@echo "  make shell     - Abre um shell bash no container"
	@echo "  make logs      - Mostra os logs do container"

up:
	@docker compose up -d --build

down:
	@docker compose down

build:
	@docker compose build

pull:
	@docker compose exec -T app python src/pull_prompts.py

push:
	@docker compose exec -T app python src/push_prompts.py

evaluate:
	@docker compose exec -T app python src/evaluate.py

experiment:
	@docker compose exec -T app python src/run_experiment.py

test:
	@docker compose exec -T app pytest tests/test_prompts.py -v

shell:
	@docker compose exec app /bin/bash

logs:
	@docker compose logs -f app
