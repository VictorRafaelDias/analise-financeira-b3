"""Módulo 4 · Solidez Financeira — carregamento da base oficial, filtros e formatação.

Regra do módulo: nenhum valor da B3 é alterado. Aqui só há leitura da base pronta
(`data/B3_Solidez_Financeira_base_oficial.xlsx`) e contas padrão sobre as linhas
oficiais (somas, diferenças, razões, LTM).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "B3_Solidez_Financeira_base_oficial.xlsx"

# --------------------------------------------------------------------------------------
# Cascatas (usadas nos gráficos e nos testes de validação)
# --------------------------------------------------------------------------------------
# Bloco 3 · do lucro ao FCO (DFC). A soma fecha exatamente com `fco`.
CASCATA_FCO = [
    ("lucro_liquido_dfc", "Lucro líquido"),
    ("depreciacao_amortizacao", "Depreciação e amortização"),
    ("ir_diferido_total_dfc", "IR diferido"),
    ("despesas_juros_dfc", "Despesas de juros"),
    ("outros_ajustes_dfc", "Outros ajustes"),
    ("capital_de_giro_dfc", "Capital de giro"),
    ("ir_cs_pago", "IR e CS pagos"),
    ("var_aplicacoes_financeiras", "Aplicações financeiras"),
    ("var_garantias_recebidas", "Garantias recebidas"),
    ("var_proventos_custodia", "Proventos em custódia"),
]

# Bloco 2 · da receita ao EBITDA recorrente (DRE).
CASCATA_RECEITA = [("receita_total", "Receita total"), ("deducoes_receita", "Deduções")]
CASCATA_DESPESAS = [
    ("desp_pessoal", "Pessoal"),
    ("desp_ti", "TI"),
    ("desp_atrelada_faturamento", "Atrelada ao faturamento"),
    ("desp_outras", "Outras despesas"),
]

# Bloco 1 · dívida por instrumento (ITR 2T26, nota 9, p. 32–35). Não está na planilha.
DIVIDA_INSTRUMENTOS = pd.DataFrame(
    [
        ("8ª emissão de debêntures", "CDI + 0,62%", "Mai/2027, Mai/2028, Mai/2029", 4548.3, "Debêntures"),
        ("Bond no exterior (USD 700 mi, sustainability-linked)", "4,125% a.a. em USD", "Set/2031", 3101.9, "Bond"),
        ("10ª emissão de debêntures", "CDI + 0,45%", "Set/2029 e Set/2030", 2696.3, "Debêntures"),
        ("9ª emissão de debêntures", "CDI + 0,59%", "Jan/2030 e Jan/2031", 1814.2, "Debêntures"),
        ("Empréstimos bancários B3 Inova (5 contratos em USD)", "SOFR + 1,5–2,0% ou 4–7%", "Ago/2026 a Nov/2027", 1299.4, "Empréstimos"),
        ("2ª emissão de debêntures", "CDI + 0,58%", "Nov/2029 (repactuação)", 1226.9, "Debêntures"),
        ("4ª emissão, série IPCA", "IPCA + 3,90%", "Dez/2028 a Dez/2030", 181.2, "Debêntures"),
        ("4ª emissão, série DI", "CDI + 1,30%", "Dez/2030", 41.6, "Debêntures"),
        ("Outros (arrendamentos)", "—", "—", 23.4, "Outros"),
    ],
    columns=["instrumento", "taxa", "vencimento", "saldo_mi", "tipo"],
)

# Faixas do radar (Moody's Local Brasil)
ALAV_CONFORTAVEL, ALAV_GATILHO = 2.0, 2.5
COBERTURA_MIN = 4.0
FCO_DIVIDA_MIN = 0.25


# --------------------------------------------------------------------------------------
# Carregamento
# --------------------------------------------------------------------------------------
@st.cache_data
def load():
    x = pd.read_excel(DATA_PATH, sheet_name=["Trimestral", "Anual"])
    tri, anual = x["Trimestral"].copy(), x["Anual"].copy()

    tri["ano"] = tri["ano"].astype(int)
    tri["tri"] = tri["tri"].astype(int)
    tri = tri.sort_values(["ano", "tri"]).reset_index(drop=True)
    tri["periodo"] = tri["trimestre"]
    tri["parcial"] = False

    anual["ano"] = anual["ano"].astype(int)
    anual["n_trimestres"] = anual["n_trimestres"].astype(int)
    anual = anual.sort_values("ano").reset_index(drop=True)
    anual["parcial"] = anual["n_trimestres"] < 4
    anual["periodo"] = np.where(anual["parcial"], anual["ano"].astype(str) + " (YTD)", anual["ano"].astype(str))
    return tri, anual


def validar(tri, anual):
    """Testes da seção 13. Devolve a lista de falhas (vazia = tudo certo)."""
    erros = []
    u = tri.iloc[-1]
    if u["trimestre"] != "2T26":
        erros.append(f"Último trimestre da base é {u['trimestre']}, esperado 2T26.")
    if round(u["divida_bruta"]) != 14_933_316:
        erros.append(f"divida_bruta do 2T26 = {u['divida_bruta']:,.0f}, esperado 14.933.316.")
    if abs(DIVIDA_INSTRUMENTOS["saldo_mi"].sum() * 1e3 - u["divida_bruta"]) > 500:
        erros.append("Soma da tabela de instrumentos não bate com divida_bruta do 2T26.")
    if round(u["caixa_total"]) != 19_291_292:
        erros.append(f"caixa_total do 2T26 = {u['caixa_total']:,.0f}, esperado 19.291.292.")
    if abs(u["divida_bruta_ebitda_ltm"] - 1.98) > 0.005:
        erros.append(f"divida_bruta_ebitda_ltm do 2T26 = {u['divida_bruta_ebitda_ltm']:.3f}, esperado ≈ 1,98.")
    for _, r in anual.iterrows():
        dif_fco = sum(r[c] for c, _ in CASCATA_FCO) - r["fco"]
        if abs(dif_fco) > 0.5:
            erros.append(f"Cascata do FCO não fecha em {r['periodo']} (diferença {dif_fco:,.1f}).")
        dif_ebitda = (
            sum(r[c] for c, _ in CASCATA_RECEITA + CASCATA_DESPESAS)
            + r["ajustes_nao_recorrentes_ebitda"]
            - r["ebitda_recorrente"]
        )
        if abs(dif_ebitda) > 0.5:
            erros.append(f"Cascata do EBITDA não fecha em {r['periodo']} (diferença {dif_ebitda:,.1f}).")
    return erros


# --------------------------------------------------------------------------------------
# Séries por granularidade
# --------------------------------------------------------------------------------------
def ltm(tri, col):
    """Coluna LTM oficial da base, ou soma móvel de 4 trimestres se a base não tiver."""
    c = f"{col}_ltm"
    return tri[c] if c in tri.columns else tri[col].rolling(4).sum()


def serie(tri, anual, gran, anos, flows=(), stocks=()):
    """Monta um DataFrame com `periodo`, `ano`, `parcial` + fluxos e saldos pedidos.

    - Anual: aba Anual (2026 é YTD, marcado em `parcial`).
    - Trimestral: valores do trimestre.
    - LTM: colunas *_ltm (ou soma móvel), a partir do 4T20.
    Saldos (BP) são sempre o valor do fim do período.
    """
    flows, stocks = list(flows), list(stocks)
    if gran == "Anual":
        df = anual[["ano", "periodo", "parcial", *flows, *stocks]].copy()
    else:
        df = tri[["ano", "tri", "periodo", "parcial", *stocks]].copy()
        for c in flows:
            df[c] = ltm(tri, c) if gran == "LTM" else tri[c]
        if gran == "LTM" and flows:
            df = df[df["ano"] * 10 + df["tri"] >= 20204]
    return df[(df["ano"] >= anos[0]) & (df["ano"] <= anos[1])].reset_index(drop=True)


def fim_de_ano(tri, anos):
    """Trimestres de fim de ano (4T) + o último trimestre disponível, para razões LTM na visão anual."""
    df = tri[(tri["ano"] >= anos[0]) & (tri["ano"] <= anos[1])]
    ult = df.index.max()
    df = df[(df["tri"] == 4) | (df.index == ult)].copy()
    df["periodo"] = np.where(df["tri"] == 4, df["ano"].astype(str), df["trimestre"] + " (LTM)")
    return df.reset_index(drop=True)


def ref_idx(tri, ano_fim):
    """Índice do último trimestre dentro do filtro de anos e do mesmo trimestre 1 ano antes."""
    i = tri.index[tri["ano"] <= ano_fim].max()
    return i, (i - 4 if i - 4 >= 0 else None)


# --------------------------------------------------------------------------------------
# Formatação (padrão brasileiro)
# --------------------------------------------------------------------------------------
def br(v, dec=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def escala(unidade):
    """(divisor sobre R$ mil, sufixo, casas decimais padrão)."""
    return (1e6, "bi", 1) if unidade == "R$ bi" else (1e3, "mi", 0)


def dinheiro(v_mil, unidade, dec=None, sinal=False, md=True):
    """Valor em R$ mil -> texto. md=True escapa o cifrão para st.markdown (dois "$" viram LaTeX)."""
    div, suf, d = escala(unidade)
    if v_mil is None or pd.isna(v_mil):
        return "—"
    v = v_mil / div
    d = d if dec is None else dec
    moeda = "R\\$" if md else "R$"
    txt = f"{moeda} {br(abs(v), d)} {suf}"
    if v < 0:
        return f"-{txt}"
    return f"+{txt}" if sinal else txt


def mult(v, dec=2, sinal=False):
    if v is None or pd.isna(v):
        return "—"
    s = br(v, dec) + "x"
    return ("+" + s) if (sinal and v >= 0) else s


def pct(v, dec=0, sinal=False):
    if v is None or pd.isna(v):
        return "—"
    s = br(v * 100, dec) + "%"
    return ("+" + s) if (sinal and v >= 0) else s


def para_csv(df):
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
