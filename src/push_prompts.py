"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

# Arquivo local com o prompt otimizado e nome base do repositorio no Hub.
V2_FILE = "prompts/bug_to_user_story_v2.yml"
V2_KEY = "bug_to_user_story_v2"
REPO_BASENAME = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    user_prompt = (prompt_data.get("user_prompt") or "").strip()

    if not system_prompt:
        errors.append("system_prompt está vazio")
    if "TODO" in system_prompt:
        errors.append("system_prompt ainda contém TODOs")
    if not user_prompt:
        errors.append("user_prompt está vazio")
    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}")

    # O system_prompt não pode ter chaves soltas (quebraria o ChatPromptTemplate).
    if "{" in system_prompt or "}" in system_prompt:
        errors.append("system_prompt não pode conter chaves { } (use apenas no user_prompt)")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome completo do prompt no Hub (ex: usuario/bug_to_user_story_v2)
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    system_prompt = prompt_data["system_prompt"].strip()
    user_prompt = prompt_data["user_prompt"].strip()

    # Monta o ChatPromptTemplate: system (sem variaveis) + user ({bug_report}).
    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data.get("description", "")
    if techniques:
        description = f"{description} | Técnicas: {', '.join(techniques)}"

    tags = prompt_data.get("tags", [])

    try:
        url = hub.push(
            prompt_name,
            template,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=tags,
        )
        print(f"   ✓ Push realizado com sucesso (PÚBLICO)")
        print(f"   ✓ URL: {url}")
        return True

    except Exception as e:
        print(f"❌ Erro ao fazer push do prompt '{prompt_name}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está correta no .env")
        print("- USERNAME_LANGSMITH_HUB corresponde ao seu usuário do Hub")
        return False


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    prompt_name = f"{username}/{REPO_BASENAME}"

    # Carrega o YAML otimizado.
    data = load_yaml(V2_FILE)
    if not data or V2_KEY not in data:
        print(f"❌ Não foi possível carregar '{V2_KEY}' de {V2_FILE}")
        return 1

    prompt_data = data[V2_KEY]

    # Valida antes de enviar.
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido. Corrija os erros antes do push:")
        for err in errors:
            print(f"   - {err}")
        return 1

    print(f"Publicando: {prompt_name}")
    print(f"Técnicas: {', '.join(prompt_data.get('techniques_applied', []))}\n")

    if push_prompt_to_langsmith(prompt_name, prompt_data):
        print("\n✅ Push concluído com sucesso!")
        print("\nPróximo passo: rodar 'make evaluate' para avaliar as métricas.")
        return 0

    print("\n❌ Push falhou. Verifique as mensagens acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
