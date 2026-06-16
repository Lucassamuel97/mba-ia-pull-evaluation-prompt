# Resultados das Avaliações

Histórico das iterações de otimização do prompt `bug_to_user_story_v2`, avaliado com
`make evaluate` (provider Google / `gemini-2.5-flash`). Critério de aprovação:
**TODAS** as 5 métricas ≥ 0.9.

Cada iteração tem o output bruto salvo em `results/iteracao-XX.txt`.

## Tabela comparativa

| Iteração | Mudança principal no prompt | F1-Score | Clarity | Precision | Helpfulness | Correctness | Média | Status |
|---|---|---|---|---|---|---|---|---|
| 01 | Versão inicial (Role Prompting + Few-shot + Chain of Thought) | ~0.76 | ✅ | ✅ ~0.95 | ✅ | ❌ | 0.9117 | ❌ Reprovado (F1 e Correctness < 0.9) |
| 02 | + critérios completos (5-7 dimensões) + regras gerais (proíbe números literais) | 0.8987 ❌ | 0.93 ✅ | 0.95 ✅ | 0.94 ✅ | 0.93 ✅ | 0.9294 | ❌ Reprovado (só F1 < 0.9, por 0.0013) |
| 03 | concisão escalada por complexidade (bug simples = conciso, sem cenários extras) + persona convencional | 0.81 ❌ | 0.91 ✅ | 0.93 ✅ | 0.92 ✅ | 0.87 ❌ | 0.8884 | ❌ Regrediu (cortar abrangência piorou os 13) |

> ⚠️ **Insight crítico:** o juiz `gemini-2.5-flash` tem **variância alta** (~±0.14 por
> exemplo entre rodadas). O mesmo output do exemplo 1 oscilou F1 0.78 → 0.84 → 0.70 nas 3
> iterações. Isso significa que a variância entre execuções é maior que o gap para 0.9 —
> uma mesma versão pode reprovar numa rodada e aprovar na seguinte. A iteração 2 (0.8987)
> estava essencialmente no limiar.

## Notas de diagnóstico

### Iteração 01
- **Média 0.9117**, mas reprovado: `F1-Score` e `Correctness` < 0.9 (Correctness = (F1+Precision)/2, então o F1 é o gargalo).
- Per-exemplo (parciais): ex1 F1=0.78, ex2 F1=0.86, ex3 F1=0.77, ex4 F1=0.63.
- Causa raiz (comparando saída × referência):
  1. **Ruído do juiz**: respostas quase idênticas à referência ainda recebiam F1 ~0.78.
  2. **Recall baixo** em alguns casos: critérios de aceitação incompletos (ex4 gerou 4 de 5 critérios) e literais demais (repetindo números do bug em vez de regra geral).

### Iteração 02
- Ajustes: exigir 5-7 critérios cobrindo múltiplas dimensões (correção de dados, tempo
  real, validação/filtragem, feedback, edge case) e critérios comportamentais gerais
  (sem repetir números/IDs do relato).
- Resultado: _(preencher quando a avaliação terminar)_
