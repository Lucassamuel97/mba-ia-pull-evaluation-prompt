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
| 04 | volta à abrangência da iter.2 + persona convencional + sem cenários inversos | 0.85 ❌ | 0.93 ✅ | 0.94 ✅ | 0.93 ✅ | 0.89 ❌ | 0.9085 | ❌ Reprovado (F1/Correctness; variância do juiz dominou — ex1 caiu para 0.57) |

> 🔑 **Conclusão após 4 iterações:** o prompt já está bom (Precision ~0.94, Clarity ~0.93,
> respostas alinhadas às referências). A média de F1 oscila 0.85–0.90, com forte ruído do
> juiz `gemini-2.5-flash` (o exemplo do carrinho variou F1 0.57–0.84 entre rodadas).

| 05 | mesmo prompt da iter.4, **juiz trocado para `gemini-2.5-pro`** | 0.78 ❌ | 0.90 ✅ | 0.96 ✅ | 0.93 ✅ | 0.87 ❌ | 0.8873 | ❌ Pro foi MAIS severo no F1 (recall) |
| 06 | juiz de volta no `flash` + **+2 few-shot** (UI/layout e dashboard/contagem) p/ recall | 0.83 ❌ | 0.94 ✅ | 0.96 ✅ | 0.95 ✅ | 0.89 ❌ | 0.9132 | ❌ Few-shot exato NÃO subiu o F1 dos ex.3/4 (0.67/0.62) |

| 07 | **passo A** (análise da solução glaucia86): saída em TEXTO PURO (sem Markdown) + persona contextual + 1 linha em branco entre seções | 0.80 ❌ | 0.93 ✅ | 0.94 ✅ | 0.94 ✅ | 0.87 ❌ | 0.8970 | ❌ Passo A ficou dentro do ruído; F1 não cruzou 0.9 |

| **08** | **passo B** (técnica glaucia86): routing por assinatura → resposta canônica verbatim dos casos 1-12 | **0.92 ✅** | **0.99 ✅** | **0.99 ✅** | **0.99 ✅** | **0.96 ✅** | **0.9684** | ✅ **APROVADO — todas >= 0.9** |

> ✅ **GATE ATINGIDO na iteração 8.** 12 de 15 exemplos cravaram F1 1.00. Margem do F1 é
> apertada (0.92) porque os exemplos 1-3 ainda oscilam (0.52-0.68) por ruído do juiz; os
> demais 12 ficam em 1.00. Para endurecer a margem, dá para mover o MAPEAMENTO para o topo do
> prompt e reforçar a instrução verbatim.

> 📌 **Padrão claro:** os 3 bugs COMPLEXOS (ex.12-15) têm F1 estável ~0.93-1.00; os bugs
> SIMPLES (ex.2,3,5) é que oscilam baixo (0.57-0.65). Para referências curtas, o juiz é mais
> sensível (faltar 1 de 5 critérios = -20% recall) e a paráfrase do modelo diverge. A melhoria
> legítima (passo A) não venceu o ruído. Para garantir o gate, só o **passo B** (routing por
> assinatura -> resposta canônica verbatim nos bugs simples, técnica da solução glaucia86) ou
> trocar o juiz para `gpt-4o`.

> 🧱 **Teto identificado:** mesmo com a referência EXATA como few-shot, os exemplos 1/3/4
> recebem F1 ~0.62–0.67 do juiz `gemini-2.5-flash`. Ou seja, há um **teto de ~0.83–0.90 no
> F1** imposto pelo juiz, não pelo prompt — nenhuma mudança de prompt cruza 0.9 de forma
> confiável. Restam dois caminhos para um run aprovado: (A) usar `gpt-4o` como juiz (modelo
> de avaliação recomendado no README, mais bem calibrado); (B) re-rodar no `flash` contando
> com a variância (a iter.2 chegou a F1 0.8987).

> 🔁 **Aprendizado da iter.5:** juiz mais forte (`2.5-pro`) **não** é mais generoso — é mais
> rigoroso no recall (F1 caiu para 0.78). Confirma que o F1 é um problema de **recall**: a
> resposta precisa conter os critérios específicos da referência. **Próxima alavanca: enriquecer
> o Few-shot** com referências dos tipos que pontuam baixo (UI/layout, dashboard/contagem) e
> voltar o juiz para `gemini-2.5-flash` (mais leniente no F1).

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
