"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Prompt de baixa qualidade publicado no Hub que vamos baixar e otimizar.
SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = "prompts/bug_to_user_story_v1.yml"


def extract_messages(prompt_template) -> dict:
    """
    Extrai system_prompt e user_prompt de um ChatPromptTemplate puxado do Hub.

    Args:
        prompt_template: Objeto retornado por hub.pull()

    Returns:
        Dict com as chaves 'system_prompt' e 'user_prompt' (strings).
    """
    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt_template, "messages", None)

    if messages:
        for message in messages:
            # Cada item costuma ser um *MessagePromptTemplate com .prompt.template
            template_text = ""
            inner = getattr(message, "prompt", None)
            if inner is not None and hasattr(inner, "template"):
                template_text = inner.template
            elif hasattr(message, "template"):
                template_text = message.template
            elif hasattr(message, "content"):
                template_text = message.content

            role = type(message).__name__.lower()
            if "system" in role:
                system_prompt = template_text
            elif "human" in role or "user" in role:
                user_prompt = template_text
    else:
        # Caso seja um PromptTemplate simples (não-chat)
        system_prompt = getattr(prompt_template, "template", "")

    return {
        "system_prompt": system_prompt.strip() if system_prompt else "",
        "user_prompt": user_prompt.strip() if user_prompt else "",
    }


def pull_prompts_from_langsmith() -> bool:
    """Faz pull do prompt inicial e salva localmente em YAML."""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    print(f"Puxando prompt: {SOURCE_PROMPT}")

    try:
        prompt_template = hub.pull(SOURCE_PROMPT)
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt '{SOURCE_PROMPT}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está correta no .env")
        print("- Você tem conexão com a internet")
        print("- O nome do prompt existe no Hub")
        return False

    print("   ✓ Prompt carregado com sucesso")

    extracted = extract_messages(prompt_template)

    if not extracted["system_prompt"] and not extracted["user_prompt"]:
        print("⚠️  Não foi possível extrair texto do prompt puxado.")
        return False

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt inicial (baixa qualidade) puxado do LangSmith Hub",
            "system_prompt": extracted["system_prompt"],
            "user_prompt": extracted["user_prompt"],
            "version": "v1",
            "source": SOURCE_PROMPT,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if save_yaml(prompt_data, OUTPUT_FILE):
        print(f"   ✓ Prompt salvo em: {OUTPUT_FILE}")
        return True

    return False


def main():
    """Função principal"""
    ok = pull_prompts_from_langsmith()

    if ok:
        print("\n✅ Pull concluído com sucesso!")
        print("\nPróximo passo: editar prompts/bug_to_user_story_v2.yml e rodar 'make push'.")
        return 0

    print("\n❌ Pull falhou. Verifique as mensagens acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
