---
name: conferencia-e-rastreabilidade
description: Confere número por número o boletim contra os indicadores e registra a rastreabilidade da fonte (arquivo, data de atualização, versão). Use como última etapa antes de entregar qualquer relatório de arrecadação.
---

# Conferência e rastreabilidade

## Checklist numérico
1. Leia o documento criado (read_doc) e liste todos os números e percentuais citados.
2. Compare cada um com `indicadores.json` (e `qualidade.json`). Arredondamento permitido: 2 casas em R$ bilhões, 1 casa em %.
3. Verifique coerência: participações somam ~100%; variação a/a bate com os valores absolutos citados.
4. Corrija divergências e liste o que foi corrigido.

## Checklist de texto
- Nome do mês, UFs e tributos grafados de forma idêntica ao longo do documento.
- Nenhuma frase atribui causa não presente nos dados.
- Todos os alertas de `qualidade.json` aparecem na seção "Alertas e limitações".

## Nota de fonte (obrigatória, ao final do documento)
- Fonte: Receita Federal do Brasil, Dados Abertos, Resultado da Arrecadação do Governo Federal.
- Data de atualização da fonte e nome do arquivo zip (campos `atualizacao_fonte` e `zip`).
- MD5 do zip (`zip_md5`), para auditoria.
- Unidade: R$ correntes (nominais).
- Link da planilha do período.
- Data de elaboração e versão: "AAAA-MM (fonte DD-MM-AAAA)".

## Nome do documento
`Boletim de Arrecadação Federal - AAAA-MM (fonte DD-MM-AAAA)`. Nunca reutilize nome de edição anterior.

## Retorno
Link do documento, correções feitas e pendências (se houver).
