#!/usr/bin/env python3
"""
Processa o zip "Dados Abertos - Resultado da Arrecadação Governo Federal" (RFB).
Uso:  python scripts/processar_arrecadacao.py [--zip CAMINHO] [--uf-foco SP] [--saida saida]
Gera: saida/AAAA-MM/{dados_tratados/*.csv, indicadores.json, qualidade.json, planilha.xlsx}
"""
import argparse, hashlib, json, re, shutil, sys, tempfile, zipfile, unicodedata
from datetime import datetime
from pathlib import Path
import pandas as pd

MESES = {"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,"jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12}
NOMES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

def sem_acento(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def mes_num(v):
    k = sem_acento(str(v)).strip().lower()[:3]
    return MESES.get(k)

RE_PT   = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$")      # 1.234.567,89
RE_US   = re.compile(r"^-?\d{1,3}(,\d{3}){2,}$")           # 1,234,567 (só 2001-2002)
RE_DEC  = re.compile(r"^-?\d+,\d+$")                       # 1234567,89
RE_INT  = re.compile(r"^-?\d+$")                           # 1234567
def num(v, anomalias=None, ctx=""):
    if v is None or (isinstance(v, float) and pd.isna(v)): return 0.0
    s = str(v).strip().replace("R$", "").replace(" ", "")
    if s in ("", "-"): return 0.0
    if RE_PT.match(s):  return float(s.replace(".", "").replace(",", "."))
    if RE_US.match(s):  return float(s.replace(",", ""))
    if RE_DEC.match(s): return float(s.replace(",", "."))
    if RE_INT.match(s): return float(s)
    if anomalias is not None: anomalias.append(f"valor não reconhecido '{s}' em {ctx}")
    return 0.0

def le_csv(p):
    df = pd.read_csv(p, sep=";", encoding="latin-1", dtype=str)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df.columns = [c.strip() for c in df.columns]
    return df

def md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()

def extrai(zip_path, destino):
    destino.mkdir(parents=True, exist_ok=True)
    arqs = {}
    with zipfile.ZipFile(zip_path) as z:
        for i in z.infolist():
            if i.is_dir(): continue
            nome = re.sub(r"#U([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), i.filename).split("/")[-1]
            if ".." in nome: continue                       # proteção contra path traversal
            (destino / nome).write_bytes(z.read(i)); arqs[nome] = destino / nome
    return arqs

def converte(df, cols, nome, anom):
    for c in cols:
        df[c] = [num(v, anom, f"{nome}/{c}") for v in df[c]]
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip"); ap.add_argument("--uf-foco", default=""); ap.add_argument("--saida", default="saida"); ap.add_argument("--forcar", action="store_true", help="reprocessa mesmo que o zip já conste no registro")
    a = ap.parse_args()
    zp = Path(a.zip) if a.zip else sorted(Path("entrada").glob("*.zip"), key=lambda p: p.stat().st_mtime)[-1]
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", zp.name)
    atualizacao = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else "desconhecida"
    q = {"avisos_escopo": ["O conjunto não contém arrecadação por município: o arquivo de ITR por município veio duplicado do de IR/IPI. Análises municipais exigem outra fonte (Tesouro Nacional, transferências constitucionais)."], "zip": zp.name, "zip_md5": md5(zp), "atualizacao_fonte": atualizacao, "alertas": [], "anomalias_numericas": []}
    reg_path = Path("registro/processados.json"); reg_path.parent.mkdir(exist_ok=True)
    registro = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else []
    if any(r["zip_md5"] == q["zip_md5"] for r in registro) and not a.forcar:
        print(json.dumps({"status": "JA_PROCESSADO", "zip": zp.name, "mensagem": "Este zip (mesmo MD5) já foi processado. Use --forcar para repetir."}, ensure_ascii=False)); return
    tmp = Path(tempfile.mkdtemp(prefix="arrec_"))
    arqs = extrai(zp, tmp)
    need = ["arrecadacao-estado.csv","arrecadacao-cnae.csv","arrecadacao-natureza.csv","arrecadacao-ir-ipi.csv","arrecadacao-itr.csv"]
    for n in need:
        if n not in arqs: q["alertas"].append(f"ARQUIVO AUSENTE: {n}")
    # --- verificação: ITR idêntico ao IR/IPI?
    if "arrecadacao-itr.csv" in arqs and "arrecadacao-ir-ipi.csv" in arqs:
        if md5(arqs["arrecadacao-itr.csv"]) == md5(arqs["arrecadacao-ir-ipi.csv"]):
            q["alertas"].append("arrecadacao-itr.csv é byte-a-byte idêntico a arrecadacao-ir-ipi.csv "
                                "(contém IR/IPI, não ITR por município, como diz o metadado). Arquivo IGNORADO.")
    # ---------------- ESTADO (base do total nacional) ----------------
    est = le_csv(arqs["arrecadacao-estado.csv"]); est["Mês"] = est["Mês"].map(mes_num)
    vcols = list(est.columns[3:]); est = converte(est, vcols, "estado", q["anomalias_numericas"])
    est["Ano"] = est["Ano"].astype(int); est["Total"] = est[vcols].sum(axis=1)
    if est.duplicated(["Ano","Mês","UF"]).any(): q["alertas"].append("Linhas duplicadas (Ano, Mês, UF) em estado.csv")
    ult = est.sort_values(["Ano","Mês"]).iloc[-1]; A, M = int(ult["Ano"]), int(ult["Mês"])
    n_uf = est[(est.Ano==A)&(est.Mês==M)]["UF"].nunique()
    if n_uf != 27: q["alertas"].append(f"Último período {M:02d}/{A} tem {n_uf} UFs (esperado 27)")
    def tot(ano, mes): return float(est[(est.Ano==ano)&(est.Mês==mes)]["Total"].sum())
    def acum(ano, ate): return float(est[(est.Ano==ano)&(est.Mês<=ate)]["Total"].sum())
    pa, pm = (A, M-1) if M > 1 else (A-1, 12)
    var = lambda x, y: None if not y else round((x/y-1)*100, 2)
    ind = {"periodo": f"{A}-{M:02d}", "mes_nome": f"{NOMES[M-1]}/{A}", "atualizacao_fonte": atualizacao,
           "unidade": "R$ correntes (nominais, sem deflacionar)",
           "total_mes": tot(A, M), "total_mes_ano_anterior": tot(A-1, M), "total_mes_anterior": tot(pa, pm),
           "var_yoy_pct": var(tot(A, M), tot(A-1, M)), "var_mom_pct": var(tot(A, M), tot(pa, pm)),
           "acum_ano": acum(A, M), "acum_ano_anterior": acum(A-1, M), "var_acum_pct": var(acum(A, M), acum(A-1, M))}
    # UFs
    uf = est[(est.Ano==A)&(est.Mês==M)][["UF","Total"]].sort_values("Total", ascending=False).reset_index(drop=True)
    uf["Participação %"] = (uf["Total"]/uf["Total"].sum()*100).round(2)
    ufa = est[(est.Ano==A-1)&(est.Mês==M)].set_index("UF")["Total"]
    uf["Mesmo mês ano anterior"] = uf["UF"].map(ufa); uf["Var. a/a %"] = ((uf["Total"]/uf["Mesmo mês ano anterior"]-1)*100).round(2)
    ind["top5_ufs"] = uf.head(5).round(2).to_dict("records")
    ind["concentracao_top3_pct"] = round(float(uf.head(3)["Participação %"].sum()), 2)
    if a.uf_foco:
        r = uf[uf.UF == a.uf_foco.upper()]
        ind["uf_foco"] = r.round(2).to_dict("records")[0] if len(r) else None
        if len(r): ind["uf_foco"]["posicao"] = int(r.index[0]) + 1
    # famílias de tributos (colunas são mutuamente exclusivas no tempo, conforme metadado)
    fam = {"Importação/Exportação": ["IMPORTAÇÃO","EXPORTAÇÃO"], "IPI": ["IPI -"], "IRPF": ["IRPF"], "IRPJ": ["IRPJ"], "IRRF": ["IRRF"],
           "IOF": ["OPERAÇÕES FINANCEIRAS"], "ITR": ["TERRITORIAL RURAL"], "Cofins": ["COFINS"], "PIS/Pasep": ["PIS/PASEP"],
           "CSLL": ["CSLL"], "Cide": ["CIDE"], "Previdenciária": ["PREVIDENCI", "CPSSS", "PLANO SEG"], "Outros": []}
    def familia(c):
        u = c.upper()
        for f, ks in fam.items():
            if any(k in u for k in ks): return f
        return "Outros"
    mapa = {c: familia(c) for c in vcols}
    def por_fam(ano, mes):
        d = est[(est.Ano==ano)&(est.Mês==mes)][vcols].sum()
        return d.groupby(mapa).sum()
    f = pd.DataFrame({"Mês atual": por_fam(A, M), "Mesmo mês ano anterior": por_fam(A-1, M)}).fillna(0)
    f = f[(f["Mês atual"] != 0) | (f["Mesmo mês ano anterior"] != 0)]
    f["Participação %"] = (f["Mês atual"]/f["Mês atual"].sum()*100).round(2)
    f["Var. a/a %"] = ((f["Mês atual"]/f["Mesmo mês ano anterior"]-1)*100).replace([float("inf")], None).round(2)
    f = f.sort_values("Mês atual", ascending=False).reset_index(names="Tributo")
    ind["tributos"] = f.round(2).to_dict("records")

    # ---------------- Perfil da UF de foco (opcional) ----------------
    perfil_tabs = {}
    if a.uf_foco:
        F = a.uf_foco.upper(); NE = ["MA","PI","CE","RN","PB","PE","AL","SE","BA"]
        eu = est[est.UF == F]
        if eu.empty:
            q["alertas"].append(f"UF de foco '{F}' não encontrada")
        else:
            ut = lambda ano, mes: float(eu[(eu.Ano==ano)&(eu.Mês==mes)]["Total"].sum())
            ua = lambda ano, ate: float(eu[(eu.Ano==ano)&(eu.Mês<=ate)]["Total"].sum())
            mes_ne = est[(est.Ano==A)&(est.Mês==M)&(est.UF.isin(NE))].groupby("UF")["Total"].sum().sort_values(ascending=False)
            tot_ne = float(mes_ne.sum())
            fam_uf = pd.DataFrame({"Mês atual": eu[(eu.Ano==A)&(eu.Mês==M)][vcols].sum().groupby(mapa).sum(),
                                   "Mesmo mês ano anterior": eu[(eu.Ano==A-1)&(eu.Mês==M)][vcols].sum().groupby(mapa).sum()}).fillna(0)
            fam_uf = fam_uf[(fam_uf["Mês atual"] != 0) | (fam_uf["Mesmo mês ano anterior"] != 0)]
            fam_uf["Participação %"] = (fam_uf["Mês atual"]/fam_uf["Mês atual"].sum()*100).round(2)
            fam_uf["Var. a/a %"] = ((fam_uf["Mês atual"]/fam_uf["Mesmo mês ano anterior"]-1)*100).replace([float("inf")], None).round(2)
            fam_uf = fam_uf.sort_values("Mês atual", ascending=False).reset_index(names="Tributo")
            ser = eu.sort_values(["Ano","Mês"]).tail(13)[["Ano","Mês","Total"]].copy()
            ser["Período"] = ser.apply(lambda r: f"{int(r.Ano)}-{int(r.Mês):02d}", axis=1)
            ant = {(int(r.Ano), int(r.Mês)): r.Total for r in eu.itertuples()}
            ser["Var. a/a %"] = [round((r.Total/ant[(int(r.Ano)-1, int(r.Mês))]-1)*100, 2) if ant.get((int(r.Ano)-1, int(r.Mês))) else None for r in ser.itertuples()]
            perfil = {"uf": F, "total_mes": ut(A, M), "total_mes_ano_anterior": ut(A-1, M), "total_mes_anterior": ut(pa, pm),
                      "var_yoy_pct": var(ut(A, M), ut(A-1, M)), "var_mom_pct": var(ut(A, M), ut(pa, pm)),
                      "acum_ano": ua(A, M), "acum_ano_anterior": ua(A-1, M), "var_acum_pct": var(ua(A, M), ua(A-1, M)),
                      "participacao_nacional_pct": round(ut(A, M)/ind["total_mes"]*100, 2),
                      "posicao_nacional": int(uf.index[uf.UF == F][0]) + 1 if F in set(uf.UF) else None,
                      "posicao_nordeste": (list(mes_ne.index).index(F) + 1) if F in NE else None,
                      "participacao_nordeste_pct": round(float(mes_ne.get(F, 0))/tot_ne*100, 2) if F in NE else None,
                      "tributos": fam_uf.round(2).to_dict("records"),
                      "serie_13_meses": ser[["Período","Total","Var. a/a %"]].round(2).to_dict("records")}
            ind["perfil_uf_foco"] = perfil
            perfil_tabs = {"UF de foco - Resumo": pd.DataFrame({"Indicador": [k for k, v in perfil.items() if not isinstance(v, list)],
                                                               "Valor": [v for k, v in perfil.items() if not isinstance(v, list)]}),
                           "UF de foco - Tributos": fam_uf, "UF de foco - Série": ser[["Período","Total","Var. a/a %"]]}
    # série mensal últimos 24 meses
    serie = est.groupby(["Ano","Mês"])["Total"].sum().reset_index().sort_values(["Ano","Mês"]).tail(24)
    serie["Período"] = serie.apply(lambda r: f"{int(r.Ano)}-{int(r.Mês):02d}", axis=1)
    # ---------------- CNAE e Natureza (somente Darf) ----------------
    def darf(nome, chave_cols):
        d = le_csv(arqs[nome]); d["Mês"] = d["Mês"].map(mes_num)
        vc = [c for c in d.columns if c not in ("Ano","Mês") and c not in chave_cols]
        d = converte(d, vc, nome, q["anomalias_numericas"]); d["Ano"] = d["Ano"].astype(int); d["Total"] = d[vc].sum(axis=1)
        return d
    cn = darf("arrecadacao-cnae.csv", ["Seção - Sigla","Seção - Nome"])
    cm = cn[(cn.Ano==A)&(cn.Mês==M)]
    if cm.empty: q["alertas"].append(f"CNAE sem dados para {M:02d}/{A}")
    cm = cm.groupby(["Seção - Sigla","Seção - Nome"])["Total"].sum().reset_index().sort_values("Total", ascending=False)
    cm["Participação %"] = (cm["Total"]/cm["Total"].sum()*100).round(2)
    ind["cnae_top5"] = cm.head(5).round(2).to_dict("records"); ind["cnae_total_darf"] = float(cm["Total"].sum())
    nj = darf("arrecadacao-natureza.csv", ["Natureza Jurídica - Código","Natureza Jurídica - Nome"])
    nm = nj[(nj.Ano==A)&(nj.Mês==M)].groupby("Natureza Jurídica - Nome")["Total"].sum().reset_index().sort_values("Total", ascending=False)
    nm["Participação %"] = (nm["Total"]/nm["Total"].sum()*100).round(2)
    ind["natureza_top5"] = nm.head(5).round(2).to_dict("records")
    # validação cruzada: Darf (cnae) não pode exceder total por UF
    if ind["cnae_total_darf"] > ind["total_mes"]*1.001:
        q["alertas"].append("Total CNAE (Darf) excede o total por UF: revisar fontes")
    ind["razao_darf_sobre_total_pct"] = round(ind["cnae_total_darf"]/ind["total_mes"]*100, 2)
    # ---------------- IR / IPI por decêndio ----------------
    ri = le_csv(arqs["arrecadacao-ir-ipi.csv"]); ri["Mês"] = ri["Mês"].map(mes_num); ri["Ano"] = ri["Ano"].astype(int)
    rc = ["Arrecadação Bruta","Retificação","Compensação","Restituição","Outros","Arrecadação Líquida"]
    ri = converte(ri, rc, "ir-ipi", q["anomalias_numericas"])
    ri["dif"] = ri["Arrecadação Bruta"]+ri["Retificação"]+ri["Compensação"]+ri["Restituição"]+ri["Outros"]-ri["Arrecadação Líquida"]
    ruins = ri[ri["dif"].abs() > 1.0]
    if len(ruins): q["alertas"].append(f"IR/IPI: {len(ruins)} linhas em que bruta+eventos ≠ líquida (tolerância R$ 1)")
    rm = ri[(ri.Ano==A)&(ri.Mês==M)].groupby("Tributo")[rc].sum().reset_index()
    ind["ir_ipi_decendial"] = rm.round(2).to_dict("records")
    # ---------------- saída ----------------
    out = Path(a.saida)/f"{A}-{M:02d}_fonte-{atualizacao}"; (out/"dados_tratados").mkdir(parents=True, exist_ok=True)
    est[["Ano","Mês","UF","Total"]].to_csv(out/"dados_tratados/estado_total.csv", index=False, encoding="utf-8")
    (out/"indicadores.json").write_text(json.dumps(ind, ensure_ascii=False, indent=2), encoding="utf-8")
    q["status"] = "ATENÇÃO" if q["alertas"] or q["anomalias_numericas"] else "OK"
    q["linhas_lidas"] = {"estado": len(est), "cnae": len(cn), "natureza": len(nj), "ir_ipi": len(ri)}
    (out/"qualidade.json").write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
    with pd.ExcelWriter(out/"planilha.xlsx", engine="openpyxl") as xw:
        pd.DataFrame({"Item": ["Período","Fonte","Atualização da fonte","Arquivo zip","MD5 do zip","Unidade","Status da validação"],
                      "Valor": [ind["mes_nome"], "Receita Federal do Brasil — Dados Abertos (Resultado da Arrecadação)", atualizacao, zp.name, q["zip_md5"], ind["unidade"], q["status"]]}
                     ).to_excel(xw, sheet_name="Controle", index=False)
        pd.DataFrame([{k: v for k, v in ind.items() if not isinstance(v, (list, dict))}]).T.reset_index().rename(columns={"index":"Indicador",0:"Valor"}).to_excel(xw, sheet_name="Resumo", index=False)
        uf.to_excel(xw, sheet_name="Por UF", index=False); f.to_excel(xw, sheet_name="Por tributo", index=False)
        cm.to_excel(xw, sheet_name="Por CNAE (Darf)", index=False); nm.to_excel(xw, sheet_name="Por natureza jurídica", index=False)
        rm.to_excel(xw, sheet_name="IR e IPI (decêndios)", index=False); serie[["Período","Total"]].to_excel(xw, sheet_name="Série 24 meses", index=False)
        for nome_aba, dfp in perfil_tabs.items(): dfp.to_excel(xw, sheet_name=nome_aba, index=False)
        pd.DataFrame({"Alertas": q["alertas"] or ["Nenhum"]}).to_excel(xw, sheet_name="Alertas", index=False)
    from openpyxl import load_workbook
    from openpyxl.styles import Font
    wb = load_workbook(out/"planilha.xlsx")
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        for c in ws[1]: c.font = Font(bold=True)
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(60, max(12, max(len(str(c.value)) if c.value is not None else 0 for c in col[:60]) + 2))
            for c in col[1:]:
                if isinstance(c.value, float): c.number_format = "#,##0.00"
    wb.save(out/"planilha.xlsx")
    registro.append({"zip": zp.name, "zip_md5": q["zip_md5"], "atualizacao_fonte": atualizacao, "periodo": ind["periodo"],
                     "saida": str(out), "status": q["status"], "processado_em": datetime.now().isoformat(timespec="seconds")})
    reg_path.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"saida": str(out), "status": q["status"], "alertas": q["alertas"], "n_anomalias_numericas": len(q["anomalias_numericas"])}, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
