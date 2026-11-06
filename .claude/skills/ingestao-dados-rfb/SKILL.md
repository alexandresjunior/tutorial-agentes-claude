---
name: ingestao-dados-rfb
description: Processa o zip "Dados Abertos - Resultado da Arrecadação Governo Federal" (Receita Federal) com o script do projeto, valida a qualidade e decide se os dados podem ser usados. Use sempre que houver um zip novo em entrada/ ou o usuário pedir para atualizar o boletim.
---

# Ingestão e validação dos Dados Abertos da arrecadação

## Execução
Na raiz do projeto:

    python scripts/processar_arrecadacao.py --zip "<caminho do zip>" --uf-foco <UF opcional>

O script extrai o zip em pasta temporária, trata os CSVs e grava em
`saida/AAAA-MM_fonte-AAAA-MM-DD/`: `planilha.xlsx`, `indicadores.json`, `qualidade.json`
e `dados_tratados/`. Ele também registra o MD5 do zip em `registro/processados.json`.
Se a resposta for `JA_PROCESSADO`, não há nada novo: informe e pare.

## O que o script já trata (e por quê)
- Codificação latin-1 e separador ";".
- Mês em formatos diferentes ("Set", "Set ", "Setembro"): normalizado para número.
- Números em formatos misturados (1.234.567,89 / 1234567,89 / 1234567 / 1,234,567 em 2001-2002).
- Colunas finais sem nome no arquivo por natureza jurídica: descartadas.
- As colunas do arquivo por UF são mutuamente exclusivas no tempo (cada tributo "aparece de X a Y"
  segundo o metadado), por isso o total por UF/mês é a soma de todas as colunas.

## Leitura obrigatória de `qualidade.json`
0. `avisos_escopo` não bloqueia: são limites permanentes do conjunto (ex.: sem dados municipais) e vão para o relatório.
1. `alertas` vazio e `anomalias_numericas` vazio → STATUS OK.
2. Qualquer alerta → STATUS ATENÇÃO. Os alertas vão para o relatório, nunca são omitidos.
3. STATUS BLOQUEADO (pare e informe o motivo) se:
   - faltar `arrecadacao-estado.csv`, `arrecadacao-cnae.csv` ou `arrecadacao-natureza.csv`;
   - o último período tiver menos de 27 UFs;
   - o script terminar com erro.

## Problemas conhecidos neste conjunto de dados (verificados no zip de 19/10/2026)
- `arrecadacao-itr.csv` pode vir idêntico a `arrecadacao-ir-ipi.csv` (conteúdo de IR/IPI,
  não de ITR por município). O script detecta pelo MD5 e ignora o arquivo; o ITR continua disponível
  como coluna nos demais arquivos. Cite isso na nota de limitações.
- No arquivo de IR/IPI, em algumas linhas a conta "bruta + eventos = líquida" não fecha
  (2023 e 2026). O script alerta; o uso dos valores líquidos exige cautela.

## Proibido
- Corrigir ou editar os CSVs originais.
- Preencher dados ausentes por estimativa.
