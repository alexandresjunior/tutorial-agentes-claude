---
name: indicadores-arrecadacao
description: Define e confere os indicadores do boletim de arrecadação federal (total, variações, acumulado, composição por tributo, UF, setor e natureza jurídica) e publica a planilha no Google Sheets. Use depois da ingestão dos dados, ao montar ou publicar a planilha do período.
---

# Indicadores e planilha do período

## Definições (valores em R$ correntes, ou seja, NOMINAIS, sem deflacionar)
- **Total do mês**: soma de todas as colunas de arrecadação, de todas as UFs, no mês.
- **Variação a/a**: mês atual ÷ mesmo mês do ano anterior − 1.
- **Variação m/m**: mês atual ÷ mês anterior − 1.
- **Acumulado no ano**: janeiro até o mês atual; comparado ao mesmo intervalo do ano anterior.
- **Composição por tributo**: famílias (Previdenciária, Cofins, IRRF, IRPJ, IRPF, CSLL, PIS/Pasep,
  IOF, IPI, ITR, Cide, Importação/Exportação, Outros) com participação e variação a/a.
- **Setores (CNAE) e natureza jurídica**: baseados só em recolhimentos por Darf; trazem
  a razão Darf ÷ total por UF como controle de consistência.

- **Perfil da UF de foco** (`perfil_uf_foco` no JSON, quando há `uf_foco`): total, variações a/a e m/m,
  acumulado, participação nacional e no Nordeste, posição nacional e regional, composição por tributo
  e série dos últimos 13 meses com variação a/a.

## Limite de escopo: municípios
O zip NÃO traz arrecadação por município (o arquivo de ITR por município veio duplicado do de IR/IPI).
Nunca estime valores municipais a partir de dados estaduais. Análise municipal usa outra fonte
(transferências constitucionais do Tesouro Nacional: FPM, ITR etc.) e deve ser identificada como tal.

## Regras de leitura
- Variação por UF acima de ±30% a/a: marque como "verificar" e não explique a causa.
  O arquivo não traz informação para atribuir motivo.
- Nunca compare valores nominais de anos distantes como se fossem reais. Se o usuário pedir
  análise real, explique que seria preciso um índice de preços (ex.: IPCA) fora do zip.
- Toda variação percentual acompanha os valores absolutos que a originam.

## Planilha (já gerada em `planilha.xlsx` pelo script)
Abas: Controle, Resumo, Por UF, Por tributo, Por CNAE (Darf), Por natureza jurídica,
IR e IPI (decêndios), Série 24 meses, UF de foco - Resumo, UF de foco - Tributos,
UF de foco - Série (estas três só existem quando há uf_foco), Alertas.

## Publicação no Google Sheets
1. Envie `planilha.xlsx` ao Drive com a ferramenta de criar arquivo do conector, pedindo conversão
   para Google Sheets. Use a pasta de `config/parametros.json` (pasta_drive_id), se houver.
2. Nome: `Arrecadação Federal - Planilha - AAAA-MM (fonte DD-MM-AAAA)`.
3. Confira 3 células (total do mês, uma UF em "Por UF", um tributo em "Por tributo") com `get_values`
   contra `indicadores.json`. Divergência → STATUS ATENÇÃO e relato.
4. Nunca sobrescreva planilhas de períodos anteriores.
5. Se o conector não converter o .xlsx, informe o caminho do arquivo local e peça ao usuário para importá-lo
   (Arquivo > Importar no Google Sheets); registre isso no retorno.
