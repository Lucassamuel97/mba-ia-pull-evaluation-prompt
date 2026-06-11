"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

# Caminho do prompt otimizado (v2) que será validado.
V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
V2_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def prompt():
    """Retorna o dicionário do prompt v2 (conteúdo interno da chave raiz)."""
    data = load_prompts(V2_PATH)
    assert V2_KEY in data, f"Chave '{V2_KEY}' não encontrada em {V2_PATH}"
    return data[V2_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "Campo 'system_prompt' não existe"
        assert prompt["system_prompt"].strip(), "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt.get("system_prompt", "").lower()
        assert "você é um" in system_prompt or "voce e um" in system_prompt, \
            "O prompt não define uma persona (ex: 'Você é um...')"

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt.get("system_prompt", "").lower()
        mentions_markdown = "markdown" in system_prompt
        mentions_user_story = "como um" in system_prompt and "eu quero" in system_prompt
        assert mentions_markdown or mentions_user_story, \
            "O prompt não exige formato Markdown nem o template de User Story padrão"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt.get("system_prompt", "").lower()
        has_examples = "exemplo" in system_prompt or "few-shot" in system_prompt
        # Deve haver pelo menos um par entrada->saída demonstrado.
        has_io_pair = "user story:" in system_prompt and "bug" in system_prompt
        assert has_examples and has_io_pair, \
            "O prompt não contém exemplos de entrada/saída (Few-shot)"

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        system_prompt = prompt.get("system_prompt", "")
        assert "TODO" not in system_prompt, "O prompt ainda contém um [TODO]"
        assert "[TODO]" not in system_prompt, "O prompt ainda contém um [TODO]"

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, \
            f"São necessárias pelo menos 2 técnicas, encontradas: {len(techniques)}"

    def test_prompt_structure_is_valid(self, prompt):
        """Valida a estrutura completa do prompt via utils.validate_prompt_structure."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, f"Estrutura inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
