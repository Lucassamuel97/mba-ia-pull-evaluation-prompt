"""
Script OPCIONAL para publicar um Experiment formal no LangSmith.

Diferente do evaluate.py (que calcula as métricas localmente e só imprime no
terminal), este script usa langsmith.evaluation.evaluate() para registrar um
Experiment na aba "Datasets & Experiments", com as 5 notas (feedback) por exemplo.
Assim a dashboard do LangSmith mostra a tabela de avaliação — ótimo para evidência.

NÃO altera nenhum arquivo travado: apenas REUTILIZA as métricas de metrics.py.

Uso:
    python src/run_experiment.py
    (ou: make experiment)
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from langchain import hub
from utils import check_env_vars, print_section_header, get_llm
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

load_dotenv()


def build_target(prompt_name: str):
    """Cria a função-alvo: recebe os inputs do exemplo e retorna a resposta gerada."""
    prompt = hub.pull(prompt_name)
    llm = get_llm(temperature=0)
    chain = prompt | llm

    def run_prompt(inputs: dict) -> dict:
        response = chain.invoke(inputs)
        return {"answer": response.content}

    return run_prompt


def combined_evaluator(run, example):
    """
    Avaliador único que calcula as 5 métricas (mesma lógica do evaluate.py)
    e retorna todas como feedback do Experiment.
    """
    answer = (run.outputs or {}).get("answer", "")
    reference = (example.outputs or {}).get("reference", "")
    question = (example.inputs or {}).get("bug_report", "")

    f1 = evaluate_f1_score(question, answer, reference)["score"]
    clarity = evaluate_clarity(question, answer, reference)["score"]
    precision = evaluate_precision(question, answer, reference)["score"]

    # Derivadas (idênticas ao evaluate.py)
    helpfulness = (clarity + precision) / 2
    correctness = (f1 + precision) / 2

    return {
        "results": [
            {"key": "f1_score", "score": round(f1, 4)},
            {"key": "clarity", "score": round(clarity, 4)},
            {"key": "precision", "score": round(precision, 4)},
            {"key": "helpfulness", "score": round(helpfulness, 4)},
            {"key": "correctness", "score": round(correctness, 4)},
        ]
    }


def main():
    print_section_header("PUBLICAR EXPERIMENT NO LANGSMITH")

    provider = os.getenv("LLM_PROVIDER", "google")
    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if provider == "openai":
        required_vars.append("OPENAI_API_KEY")
    else:
        required_vars.append("GOOGLE_API_KEY")

    if not check_env_vars(required_vars):
        return 1

    client = Client()
    project_name = os.getenv("LANGSMITH_PROJECT", "FullCycle")
    dataset_name = f"{project_name}-eval"
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/bug_to_user_story_v2"

    # Garante que o dataset existe (criado pelo evaluate.py).
    datasets = list(client.list_datasets(dataset_name=dataset_name))
    if not datasets:
        print(f"❌ Dataset '{dataset_name}' não encontrado.")
        print("   Rode 'make evaluate' uma vez para criar o dataset, depois tente de novo.")
        return 1

    print(f"Dataset: {dataset_name}")
    print(f"Prompt:  {prompt_name}")
    print(f"Modelo de geração: {os.getenv('LLM_MODEL')}")
    print(f"Modelo de avaliação: {os.getenv('EVAL_MODEL')}\n")
    print("Executando experiment (geração + 5 métricas por exemplo)...")
    print("Isso pode levar alguns minutos por causa do rate limit do Gemini.\n")

    target = build_target(prompt_name)

    results = evaluate(
        target,
        data=dataset_name,
        evaluators=[combined_evaluator],
        experiment_prefix="bug_to_user_story_v2",
        metadata={"prompt": prompt_name, "model": os.getenv("LLM_MODEL")},
        max_concurrency=1,  # sequencial p/ respeitar o rate limit do Gemini
        client=client,
    )

    print("\n✅ Experiment publicado com sucesso!")
    print("   Veja em: LangSmith → Datasets & Experiments → "
          f"{dataset_name} → aba Experiments")
    try:
        print(f"   Nome do experiment: {results.experiment_name}")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
