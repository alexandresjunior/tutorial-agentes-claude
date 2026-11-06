---
name: boletim-gerencial
description: Estrutura, tom e regras de redação do Boletim de Arrecadação Federal para gestores públicos, a partir dos indicadores já calculados. Use ao redigir o relatório mensal no Google Docs.
---

# Boletim de Arrecadação Federal

## Estrutura (nesta ordem)
1. **Título**: "Boletim de Arrecadação Federal: <Mês/Ano>" e subtítulo com órgão e data de elaboração.
2. **Síntese**: até 5 linhas: total do mês, variação a/a e m/m, acumulado no ano e um fato de destaque.
3. **Indicadores principais**: tabela (Indicador | Valor | Comparação).
4. **Composição por tributo**: tabela com valor, participação e variação a/a; 2 a 3 frases de leitura.
5. **Distribuição territorial**: 5 maiores UFs, concentração das 3 maiores e o **perfil da UF de foco**
   (`perfil_uf_foco`): total, variações, acumulado, posição nacional e no Nordeste, composição por tributo
   e série de 13 meses. Variações acima de ±30% entram como "a verificar".
6. **Setores econômicos (CNAE) e natureza jurídica**: 5 maiores de cada, com ressalva de que se baseiam em Darf.
7. **IR e IPI por decêndio**: bruta e líquida do mês, com o alerta de consistência quando houver.
8. **Alertas e limitações**: todos os itens de `alertas` e `avisos_escopo` de `qualidade.json`, em linguagem simples.
   Inclua sempre a nota de que o conjunto não tem dados por município.
9. **Fonte e metodologia**: ver skill conferencia-e-rastreabilidade.

## Tom e estilo
- Impessoal, objetivo, em português do Brasil, frases curtas. Um número por afirmação.
- Valores em R$ bilhões com 2 casas (ex.: R$ 239,38 bilhões); percentuais com 1 casa.
- Escreva sempre "valores nominais".
- Descreva o que ocorreu; não explique por quê, a menos que o dado esteja no arquivo.
- Sem adjetivos de avaliação ("excelente", "preocupante") e sem juízo político.

## Proibido
- Números que não estejam em `indicadores.json` ou `qualidade.json`.
- Previsões, projeções ou recomendações de política fiscal.
- Omitir alertas de qualidade para "melhorar" o texto.

## Formatação no Google Docs
Título, Título 1 para seções, tabelas com cabeçalho em negrito, no máximo 3 páginas.
Inclua o link da planilha do período na seção de fonte.
