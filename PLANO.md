# Plano de Execução — Pull, Otimização e Avaliação de Prompts

Documento de planejamento para resolver o desafio descrito no [README.md](./README.md).

> **Decisões já tomadas:**
> - **Provider LLM:** Google Gemini (`gemini-2.5-flash`) — gratuito.
> - **Execução:** ambiente **Docker** orquestrado via **Makefile** (padrão inspirado no
>   repositório [mba-ia-desafio-ingestao-busca](https://github.com/Lucassamuel97/mba-ia-desafio-ingestao-busca)).

---

## 1. Diagnóstico do projeto

### Já está pronto (não alterar)
- `src/evaluate.py` — script de avaliação completo.
- `src/metrics.py` — as métricas (LLM-as-Judge).
- `src/utils.py` — funções auxiliares (`get_llm`, `load_yaml`, `save_yaml`, etc.).
- `datasets/bug_to_user_story.jsonl` — 15 bugs (5 simples, 7 médios, 3 complexos).
- `prompts/bug_to_user_story_v1.yml` — prompt ruim de referência.

### Falta implementar
| Arquivo | Estado | Ação |
|---|---|---|
| `src/pull_prompts.py` | esqueleto (`...`) | implementar corpo |
| `src/push_prompts.py` | esqueleto (`...`) | implementar corpo |
| `prompts/bug_to_user_story_v2.yml` | não existe | criar do zero |
| `tests/test_prompts.py` | 6 testes vazios (`pass`) | implementar |
| `.env` | não existe | criar a partir do `.env.example` |
| `Dockerfile` | não existe | criar |
| `docker-compose.yml` | não existe | criar |
| `Makefile` | não existe | criar |

---

## 2. Mecânica crítica descoberta no código

Três detalhes do código pronto que determinam o sucesso da otimização:

### 2.1. As "5 métricas" são, na prática, 3
Em `evaluate.py` (linhas ~220-221):
```python
helpfulness = (clarity + precision) / 2
correctness = (f1 + precision) / 2
```
**Helpfulness e Correctness são derivadas.** Se garantirmos
`F1 ≥ 0.9`, `Clarity ≥ 0.9` e `Precision ≥ 0.9`, as derivadas passam automaticamente.
→ **Foco da otimização: as 3 métricas base.**

### 2.2. O avaliador compara contra o `reference` do dataset
As referências do `.jsonl` têm formato fixo:
```
Como um [persona], eu quero [ação], para que [benefício].

Critérios de Aceitação:
- Dado que...
- Quando...
- Então...
- E...
```
→ O prompt **v2 precisa produzir exatamente esse formato** (Given-When-Then em
português) para maximizar F1/Precision contra o ground-truth.

### 2.3. Armadilha do template (a que mais quebra o projeto)
`evaluate.py` faz `prompt_template | llm` e injeta `inputs={"bug_report": ...}`.
O prompt é puxado do Hub como `ChatPromptTemplate`. **Qualquer `{` ou `}` literal**
nos exemplos few-shot dentro do prompt será interpretado como variável de template
e quebrará o pull.
→ No v2, usar **apenas `{bug_report}`** como placeholder. Os exemplos few-shot devem
evitar chaves (o formato Given-When-Then não usa chaves, então tudo bem) ou escapá-las
com `{{` `}}`.

→ **Boa prática de System vs User:** colocar todas as instruções + few-shot no
`system_prompt` (sem variáveis) e deixar só `{bug_report}` no `user_prompt`.

---

## 3. Ambiente: Docker + Makefile

O projeto será executado dentro de um container Docker, com todos os comandos
acionados pelo Makefile (mesmo padrão do repo de referência). Como este desafio
**não usa banco de dados** — apenas chama as APIs do LangSmith e do Gemini — o
`docker-compose.yml` terá um único serviço `app`.

### 3.1. `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

CMD ["tail", "-f", "/dev/null"]
```

### 3.2. `docker-compose.yml`
```yaml
services:
  app:
    build: .
    container_name: prompt_eval_app
    env_file:
      - .env
    volumes:
      - ./:/app
    working_dir: /app
    restart: unless-stopped
```

### 3.3. `Makefile`
```makefile
.PHONY: help up down build pull push evaluate test shell

help:
	@echo "Targets:"
	@echo "  make up        - Sobe o container (build + up -d)"
	@echo "  make down      - Para o container"
	@echo "  make pull      - Faz pull do prompt v1 do LangSmith Hub"
	@echo "  make push      - Faz push do prompt v2 otimizado"
	@echo "  make evaluate  - Roda a avaliacao das metricas"
	@echo "  make test      - Roda os testes pytest"
	@echo "  make shell     - Abre um shell no container"

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

test:
	@docker compose exec -T app pytest tests/test_prompts.py -v

shell:
	@docker compose exec app /bin/bash
```

> ⚠️ Nota sobre rate limit do Gemini grátis: a avaliação faz ~60 chamadas
> (15 exemplos × 3 métricas + 15 gerações) e o limite é 15 req/min. Como
> `evaluate.py`/`metrics.py` são travados, pode ser necessário re-rodar
> `make evaluate` se ocorrer erro 429 (os erros viram score 0.0).

---

## 4. Plano passo a passo

### Fase 0 — Setup do ambiente
1. Criar `Dockerfile`, `docker-compose.yml` e `Makefile` (seção 3).
2. Copiar `.env.example` → `.env` e preencher:
   - `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `USERNAME_LANGSMITH_HUB`
   - `GOOGLE_API_KEY`
   - `LLM_PROVIDER=google`, `LLM_MODEL=gemini-2.5-flash`, `EVAL_MODEL=gemini-2.5-flash`
3. `make up` para subir o container.

### Fase 1 — Pull (`src/pull_prompts.py`)
4. Implementar:
   - `check_env_vars(["LANGSMITH_API_KEY"])`
   - `hub.pull("leonanluppi/bug_to_user_story_v1")`
   - extrair `system_prompt`/`user_prompt` do `ChatPromptTemplate`
   - `save_yaml(...)` em `prompts/bug_to_user_story_v1.yml`
5. Rodar `make pull` e conferir o arquivo salvo.

### Fase 2 — Prompt otimizado (`prompts/bug_to_user_story_v2.yml`)
6. Criar o YAML com os campos: `description`, `system_prompt`, `user_prompt`,
   `version`, `tags`, `techniques_applied` (≥ 2 técnicas — exigido pelos testes).
7. Conteúdo do `system_prompt`:
   - **Role Prompting** — persona "Você é um Product Manager Sênior...".
   - **Regras explícitas** de comportamento.
   - **Few-shot (obrigatório)** — 2-3 exemplos entrada→saída no formato exato
     das referências (Como/quero/para que + Critérios Given-When-Then).
   - **Chain of Thought** — instruir raciocínio passo a passo antes de gerar.
   - **Tratamento de edge cases** (bug vago, múltiplos problemas, bug crítico).
   - **Exigência de formato Markdown / User Story padrão** (necessário p/ teste).
   - `user_prompt: "{bug_report}"` (único placeholder).

### Fase 3 — Push (`src/push_prompts.py`)
8. Implementar:
   - `validate_prompt(prompt_data)` (estrutura mínima).
   - montar `ChatPromptTemplate.from_messages([("system", ...), ("user", "{bug_report}")])`.
   - `hub.push("{username}/bug_to_user_story_v2", template, ...)` **público**.
9. Rodar `make push` e conferir no dashboard do LangSmith.
10. Deixar o prompt **público**.

### Fase 4 — Testes (`tests/test_prompts.py`)
11. Implementar os 6 testes exigidos:
    - `test_prompt_has_system_prompt`
    - `test_prompt_has_role_definition`
    - `test_prompt_mentions_format`
    - `test_prompt_has_few_shot_examples`
    - `test_prompt_no_todos`
    - `test_minimum_techniques`
12. Rodar `make test` (verde).

### Fase 5 — Iteração até aprovar
13. `make evaluate` → analisar o `reasoning` das métricas baixas (tracing LangSmith).
14. Ajustar o `v2.yml` → `make push` → `make evaluate`.
15. Repetir (3-5 iterações esperadas) até **TODAS as métricas ≥ 0.9**.

### Fase 6 — Entrega
16. Atualizar o `README.md`:
    - Seção **"Técnicas Aplicadas (Fase 2)"** — quais técnicas, por quê, exemplos.
    - Seção **"Resultados Finais"** — link público do dashboard, screenshots,
      tabela comparativa v1 vs v2.
    - Seção **"Como Executar"** — pré-requisitos e comandos `make`.
17. Garantir evidências no LangSmith: dataset com 15 exemplos, runs do v2 ≥ 0.9,
    tracing de ≥ 3 exemplos.
18. Commit + push para o fork público no GitHub.

---

## 5. Critério de aprovação (lembrete)
```
Helpfulness >= 0.9
Correctness >= 0.9
F1-Score    >= 0.9
Clarity     >= 0.9
Precision   >= 0.9
```
**TODAS** as 5 métricas devem estar ≥ 0.9 (não só a média).

---

## 6. Ordem de execução resumida (via Makefile)
```bash
make up         # sobe o container
make pull       # Fase 1: baixa o prompt v1
# (editar prompts/bug_to_user_story_v2.yml — Fase 2)
make push       # Fase 3: publica o v2
make test       # Fase 4: valida estrutura do prompt
make evaluate   # Fase 5: roda as métricas (iterar até tudo >= 0.9)
```
