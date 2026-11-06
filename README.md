# Tutorial: Boletim de Arrecadação Federal (Claude Code + Google Workspace)

1. Copie esta pasta para o seu projeto (mantenha `.claude/`, `scripts/`, `config/`).
2. Edite `config/parametros.json`.
3. Instale: `pip install pandas openpyxl`.
4. Conecte os conectores do Google (veja o tutorial) e confira os nomes das ferramentas em `/mcp`.
5. Coloque o `.zip` com a base de dados em `entrada/`.
6. Rode: `claude --agent coordenador-boletim` e peça "Gere o boletim da atualização mais recente".

Teste só o script (sem Claude, sem Google):

```
python scripts/processar_arrecadacao.py --zip entrada/<arquivo>.zip --uf-foco SP
```

A pasta `exemplo/` traz o resultado real gerado com o `.zip` de 19/10/2026 e UF de foco PE.
