"""Módulo 4 · Solidez Financeira — uma função por gráfico (Plotly)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils.solidez_data import (
    ALAV_CONFORTAVEL,
    ALAV_GATILHO,
    CASCATA_DESPESAS,
    CASCATA_FCO,
    CASCATA_RECEITA,
    DIVIDA_INSTRUMENTOS,
    br,
    escala,
)
from utils.comum import cor_oport, dica

# Cor de oportunidade de cada componente das cascatas (mesmo critério da aba do João)
OPORT_COMPONENTE = {
    "Pessoal": "Médio", "TI": "Alto", "Atrelada ao faturamento": "Baixo", "Outras despesas": "Médio",
    "Deduções": "Médio", "Não recorrentes": "Baixo",
    "Depreciação e amortização": "Nulo", "IR diferido": "Nulo", "IR e CS pagos": "Médio", "CAPEX": "Baixo",
    "Juros": "Médio", "Proventos pagos": "Médio", "Recompras pagas": "Alto", "Aquisições e outros invest.": "Baixo",
    "Dívida CP": "Médio", "FCL": "Forte", "Efeito EBITDA": "Forte",
}
# Termo do glossário explicado no balão de cada rótulo
TERMO = {
    "Caixa total": "Caixa total", "Caixa líquido": "Folga (caixa − dívida)", "Dívida CP": "Dívida bruta",
    "Dívida LP": "Dívida bruta", "Receita total": "Receita bruta", "Deduções": "Deduções da receita",
    "Receita líquida": "Receita líquida", "Pessoal": "Pessoal e encargos", "TI": "Tecnologia da informação",
    "Atrelada ao faturamento": "Atrelada ao faturamento", "EBITDA": "EBITDA",
    "Não recorrentes": "Ajustes não recorrentes", "EBITDA recorrente": "EBITDA recorrente",
    "Lucro líquido": "Lucro líquido", "Depreciação e amortização": "Depreciação e amortização",
    "FCO": "FCO", "CAPEX": "CAPEX", "FCL": "FCL", "FCL depois dos juros": "FCL depois dos juros",
    "Recompras pagas": "Recompra", "Proventos pagos": "JCP", "Juros": "Resultado financeiro",
}
INCOERENCIA = dict(color="rgba(242,183,5,0.45)", pattern=dict(shape="/", fgcolor="#9A7400", solidity=0.35),
                   line=dict(color="#9A7400", width=1.5))

# Paleta única do módulo
AZUL = "#1F5FAD"
AZUL_CLARO = "#8DB6E6"
CINZA_CLARO = "#C5CBD3"
CINZA_ESCURO = "#4B5563"
CINZA = "#9AA3AE"
VERDE = "#2E9E5B"
VERMELHO = "#D64545"
ROXO = "#7B5EA7"
AMARELO = "#F2B705"


def _layout(fig, height=430, y_title=None, legenda=True):
    fig.update_layout(
        separators=",.",
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0) if legenda else None,
        showlegend=legenda,
        hovermode="x unified",
        yaxis_title=y_title,
        font=dict(size=13),
    )
    fig.update_xaxes(type="category")
    return fig


def _dica_linha(termo):
    return dica(termo, largura=70).replace("{", "").replace("}", "")


def _rotular_barras(fig, dec, posicao):
    """Valor escrito em cada barra (padrão desta aba). posicao: 'outside', 'inside_end' ou 'inside'."""
    for t in fig.data:
        if t.type != "bar":
            continue
        t.texttemplate = f"%{{y:,.{dec}f}}"
        if posicao == "outside":
            t.textposition = "outside"
            t.cliponaxis = False
        else:
            t.textposition = "inside"
            t.insidetextanchor = "end" if posicao == "inside_end" else "middle"
        muitos = t.x is not None and len(t.x) > 12  # trimestral: texto vertical e menor
        t.textfont = dict(size=8 if muitos else 11)
        if muitos:
            t.textangle = -90
    fig.update_layout(uniformtext=dict(minsize=7, mode="hide"))
    return fig


def _opac(df):
    """2026 (YTD) com opacidade 0,5."""
    return [0.5 if p else 1.0 for p in df["parcial"]]


def _cascata(passos, unidade, destaque=(), inverter=False, height=460, dec=None, sufixo="", oport=True):
    """Cascata genérica.

    passos: lista de (rótulo, valor em R$ mil, medida) com medida em
    'absolute' (ponto de partida), 'relative' (passo) ou 'total' (subtotal).
    destaque: rótulos de incoerência, desenhados hachurados em amarelo por cima.
    oport: pinta por cima os componentes de OPORT_COMPONENTE com a cor de oportunidade.
    inverter: verde para queda e vermelho para alta (ex.: alavancagem).
    unidade=None: valores já na escala final (ex.: múltiplos), com `sufixo` nos rótulos.
    """
    div, suf, d = escala(unidade) if unidade else (1, "", 2)
    if dec is None:
        dec = 2 if suf in ("bi", "") else 0
    x, y, medidas, textos, bases = [], [], [], [], []
    acum = 0.0
    for rotulo, valor, medida in passos:
        v = valor / div
        x.append(rotulo)
        medidas.append(medida)
        if medida == "total":
            y.append(acum)
            bases.append(0)
            textos.append(br(acum, dec) + sufixo)
        elif medida == "absolute":
            acum = v
            y.append(v)
            bases.append(0)
            textos.append(br(v, dec) + sufixo)
        else:
            bases.append(acum)
            acum += v
            y.append(v)
            textos.append(("+" if v >= 0 else "−") + br(abs(v), dec) + sufixo)

    def _chave(rot):
        return rot.split(" (")[0]

    def _nivel(rot):
        return OPORT_COMPONENTE.get(_chave(rot)) if oport else None

    hover = []
    for rot, t in zip(x, textos):
        nv = _nivel(rot)
        h = f"<b>{rot}</b><br>{t}" + (f" R$ {suf}" if suf else "")
        if rot in destaque:
            h += "<br><b>Incoerência destacada</b> (linha oficial, sem correção)"
        elif nv:
            h += f"<br>Oportunidade: {nv}"
        hover.append(h + dica(TERMO.get(_chave(rot), _chave(rot))))

    sobe, desce = (VERMELHO, VERDE) if inverter else (VERDE, VERMELHO)
    fig = go.Figure(
        go.Waterfall(
            x=x,
            y=y,
            measure=medidas,
            text=textos,
            textposition="outside",
            width=0.6,
            increasing=dict(marker_color=sobe),
            decreasing=dict(marker_color=desce),
            totals=dict(marker_color=CINZA),
            connector=dict(line=dict(color=CINZA_CLARO, width=1)),
            hovertext=hover,
            hoverinfo="text",
            showlegend=False,
        )
    )
    for i, rotulo in enumerate(x):
        nv = _nivel(rotulo)
        if rotulo in destaque:
            marker = INCOERENCIA
        elif nv and medidas[i] == "relative":
            marker = dict(color=cor_oport(nv), line=dict(color="rgba(0,0,0,0.3)", width=0.5))
        else:
            continue
        fig.add_bar(x=[rotulo], y=[y[i]], base=[bases[i]], width=0.6, marker=marker, hovertext=[hover[i]],
                    hoverinfo="text", showlegend=False)
    fig.update_layout(barmode="overlay", waterfallgap=0.4)
    _layout(fig, height=height, y_title=f"R$ {suf}" if suf else None, legenda=False)
    fig.update_layout(hovermode="closest")
    fig.update_yaxes(rangemode="tozero")
    return fig


# --------------------------------------------------------------------------------------
# Bloco 1 · Estrutura de capital
# --------------------------------------------------------------------------------------
def macro_bloco1(df, unidade):
    div, suf, dec = escala(unidade)
    op = _opac(df)
    folga = -df["divida_liquida"] / div
    fig = go.Figure()
    fig.add_bar(x=df["periodo"], y=df["caixa_total"] / div, name="Caixa total", marker_color=CINZA_CLARO,
                marker_opacity=op, hovertemplate="%{y:,.1f}" + _dica_linha("Caixa total"))
    fig.add_bar(x=df["periodo"], y=df["divida_bruta"] / div, name="Dívida bruta", marker_color=CINZA_ESCURO,
                marker_opacity=op, hovertemplate="%{y:,.1f}" + _dica_linha("Dívida bruta"))
    rotulos = [br(v, dec) for v in folga] if len(df) <= 10 else [
        br(v, dec) if i in (0, len(df) - 1, int(np.argmin(folga.values))) else "" for i, v in enumerate(folga)
    ]
    niv = ["Baixo" if pd.isna(v) else ("Alto" if v < 0 else "Forte") for v in folga.diff()]
    fig.add_scatter(x=df["periodo"], y=folga, name="Folga (caixa − dívida) · marcador = variação",
                    mode="lines+markers+text", line=dict(color=AZUL, width=3),
                    marker=dict(size=11, color=[cor_oport(v) for v in niv], line=dict(color=AZUL, width=2)),
                    text=[f"<b>{t}</b>" if t else "" for t in rotulos], textposition="top center",
                    textfont=dict(color=AZUL, size=13),
                    hovertemplate="%{y:,.1f}" + _dica_linha("Folga (caixa − dívida)"))
    fig.update_layout(barmode="group", bargap=0.25)
    _rotular_barras(fig, dec, "outside")
    _layout(fig, y_title=f"R$ {suf}")
    fig.update_yaxes(range=[0, df["caixa_total"].max() / div * 1.15])
    return fig


def micro_bloco1_cascata(r, unidade):
    passos = [
        ("Disponibilidades", r["caixa_disponibilidades"], "relative"),
        ("Aplicações CP", r["aplic_fin_cp"], "relative"),
        ("Aplicações LP", r["aplic_fin_lp"], "relative"),
        ("Caixa total", 0, "total"),
        ("Dívida CP", -r["divida_bruta_cp"], "relative"),
        ("Dívida LP", -r["divida_bruta_lp"], "relative"),
        ("Caixa líquido", 0, "total"),
    ]
    return _cascata(passos, unidade)


def micro_bloco1_instrumentos():
    df = DIVIDA_INSTRUMENTOS.sort_values("saldo_mi")
    cores = {"Debêntures": AZUL, "Bond": ROXO, "Empréstimos": VERDE, "Outros": CINZA}
    fig = go.Figure(
        go.Bar(
            y=df["instrumento"],
            x=df["saldo_mi"],
            orientation="h",
            marker_color=[cores[t] for t in df["tipo"]],
            text=[f"R$ {br(v, 0)} mi · {t} · {vc}" for v, t, vc in zip(df["saldo_mi"], df["taxa"], df["vencimento"])],
            textposition="outside",
            textfont=dict(size=11),
            cliponaxis=False,
            hovertemplate="%{y}<br>R$ %{x:,.1f} mi<extra></extra>",
        )
    )
    _layout(fig, height=440, legenda=False)
    fig.update_layout(hovermode="closest", margin=dict(l=10, r=10, t=20, b=10))
    fig.update_xaxes(type="linear", title="R$ mi", range=[0, df["saldo_mi"].max() * 2.6])
    fig.update_yaxes(type="category")
    return fig


# --------------------------------------------------------------------------------------
# Bloco 2 · Alavancagem
# --------------------------------------------------------------------------------------
def macro_bloco2(df, projecao=None):
    """df: periodo, divida_bruta_ebitda_ltm, divida_liquida_ebitda_ltm.
    projecao (opcional): DataFrame periodo, alav — desenhado tracejado."""
    fig = go.Figure()
    fig.add_hrect(y0=ALAV_CONFORTAVEL, y1=ALAV_GATILHO, fillcolor=CINZA_CLARO, opacity=0.35, line_width=0,
                  annotation_text="Moody's: até 2,0x histórico · 2,5x gatilho", annotation_position="top left",
                  annotation_font=dict(size=11, color=CINZA_ESCURO))
    fig.add_hline(y=0, line=dict(color=CINZA, width=1))

    bruta = df["divida_bruta_ebitda_ltm"].values
    i_pico = int(np.nanargmax(bruta))
    rot = ["" for _ in bruta]
    for i in {0, i_pico, len(bruta) - 1}:
        rot[i] = br(bruta[i], 2) + "x"
    niv = ["Forte" if v <= ALAV_CONFORTAVEL else ("Médio" if v <= ALAV_GATILHO else "Alto") for v in bruta]
    fig.add_scatter(x=df["periodo"], y=bruta, name="Dívida bruta ÷ EBITDA LTM", mode="lines+markers+text",
                    line=dict(color=AZUL, width=3), text=rot, textposition="top center",
                    marker=dict(size=10, color=[cor_oport(v) for v in niv], line=dict(color=AZUL, width=1.5)),
                    textfont=dict(color=AZUL), hovertemplate="%{y:.2f}x" + _dica_linha("Alavancagem"))
    fig.add_scatter(x=df["periodo"], y=df["divida_liquida_ebitda_ltm"], name="Dívida líquida ÷ EBITDA LTM",
                    mode="lines", line=dict(color=CINZA, width=2, dash="dash"),
                    hovertemplate="%{y:.2f}x" + _dica_linha("Dívida líquida"))
    if projecao is not None and len(projecao):
        x = [df["periodo"].iloc[-1], *projecao["periodo"]]
        y = [bruta[-1], *projecao["alav"]]
        fig.add_scatter(x=x, y=y, name="Projeção (simulador)", mode="lines+markers+text",
                        line=dict(color=AZUL, width=3, dash="dot"), marker=dict(symbol="circle-open", size=9),
                        text=[""] * len(projecao) + [br(projecao["alav"].iloc[-1], 2) + "x"], textposition="top right",
                        textfont=dict(color=AZUL), hovertemplate="%{y:.2f}x")
    _layout(fig, y_title="x EBITDA")
    fig.update_yaxes(range=[min(-2.0, np.nanmin(df["divida_liquida_ebitda_ltm"]) - 0.2), 3.0], tickformat=".1f",
                     ticksuffix="x")
    return fig


def micro_bloco2_ponte(r0, r1, rot0, rot1):
    d0, e0 = r0["divida_bruta"], r0["ebitda_recorrente_ltm"]
    d1, e1 = r1["divida_bruta"], r1["ebitda_recorrente_ltm"]
    ef_ebitda = d0 / e1 - d0 / e0
    ef_divida = d1 / e1 - d0 / e1
    passos = [
        (f"{rot0}", d0 / e0, "absolute"),
        (f"Efeito EBITDA ({'+' if e1 >= e0 else '−'}{br(abs(e1 / e0 - 1) * 100, 0)}%)", ef_ebitda, "relative"),
        (f"Efeito dívida ({'+' if d1 >= d0 else '−'}{br(abs(d1 / d0 - 1) * 100, 0)}%)", ef_divida, "relative"),
        (f"{rot1}", 0, "total"),
    ]
    fig = _cascata(passos, None, inverter=True, height=400, dec=2, sufixo="x")
    fig.update_yaxes(title="x EBITDA", ticksuffix="x")
    return fig


def micro_bloco2_ebitda(r, unidade):
    passos = [(rot, r[c], "relative") for c, rot in CASCATA_RECEITA]
    passos[0] = (passos[0][0], passos[0][1], "absolute")
    passos.append(("Receita líquida", 0, "total"))
    passos += [(rot, r[c], "relative") for c, rot in CASCATA_DESPESAS]
    passos.append(("EBITDA", 0, "total"))
    passos.append(("Não recorrentes", r["ajustes_nao_recorrentes_ebitda"], "relative"))
    passos.append(("EBITDA recorrente", 0, "total"))
    return _cascata(passos, unidade)


# --------------------------------------------------------------------------------------
# Bloco 3 · Conversão de caixa
# --------------------------------------------------------------------------------------
def macro_bloco3(df, unidade, destacar):
    div, suf, dec = escala(unidade)
    op = _opac(df)
    fig = go.Figure()
    fig.add_bar(x=df["periodo"], y=df["lucro_liquido_acionistas"] / div, name="Lucro líquido",
                marker_color=CINZA_CLARO, marker_opacity=op, hovertemplate="%{y:,.1f}" + _dica_linha("Lucro líquido"))
    fig.add_bar(x=df["periodo"], y=df["fco"] / div, name="FCO (oficial)", marker_color=AZUL,
                marker_opacity=op, hovertemplate="%{y:,.1f}" + _dica_linha("FCO"))
    fig.add_bar(x=df["periodo"], y=df["fcl"] / div, name="FCL", marker_color=AZUL_CLARO,
                marker_opacity=op, hovertemplate="%{y:,.1f}" + _dica_linha("FCL"))
    fig.update_layout(barmode="group", bargap=0.2)
    _rotular_barras(fig, dec, "inside_end")
    _layout(fig, height=470, y_title=f"R$ {suf}")

    topo = df[["lucro_liquido_acionistas", "fco", "fcl"]].max(axis=1) / div
    conv = df["fco"] / df["lucro_liquido_acionistas"]
    fs = 12 if len(df) <= 10 else 9
    # x das anotações = índice da categoria (texto como "2020" seria lido como índice 2020)
    for p, t, c in zip(range(len(df)), topo, conv):
        fig.add_annotation(x=p, y=t, text=f"<b>{br(c, 2)}x</b>", showarrow=False, yshift=12,
                           font=dict(size=fs, color=AZUL))
    if destacar:
        for p, v in enumerate(df["var_aplicacoes_financeiras"] / div):
            fig.add_annotation(x=p, y=0, yref="paper", yshift=-38, showarrow=False,
                               text=f"{'+' if v >= 0 else '−'}{br(abs(v), dec if suf == 'mi' else 2)}",
                               font=dict(size=fs, color=VERDE if v >= 0 else VERMELHO))
        fig.add_annotation(x=0, xref="paper", y=0, yref="paper", yshift=-60, xanchor="left", showarrow=False,
                           text=f"↑ Variação de aplicações financeiras que a B3 lança dentro do FCO "
                                f"(DFC, linha 32), R$ {suf}",
                           font=dict(size=11, color=CINZA_ESCURO))
        fig.update_layout(margin=dict(b=75))
    fig.update_yaxes(range=[0, topo.max() * 1.15])
    return fig


def micro_bloco3(r, unidade):
    passos = [(rot, r[c], "relative") for c, rot in CASCATA_FCO]
    passos[0] = (passos[0][0], passos[0][1], "absolute")
    passos += [
        ("FCO", 0, "total"),
        ("CAPEX", r["capex_total"], "relative"),
        ("FCL", 0, "total"),
        ("Juros", -r["despesas_juros_dfc"], "relative"),
        ("FCL depois dos juros", 0, "total"),
    ]
    return _cascata(passos, unidade, destaque=["Aplicações financeiras"], height=500)


# --------------------------------------------------------------------------------------
# Bloco 4 · Retorno ao acionista
# --------------------------------------------------------------------------------------
def macro_bloco4(df, unidade, regime):
    div, suf, dec = escala(unidade)
    op = _opac(df)
    fig = go.Figure()
    if regime == "Declarado":
        partes = [("dividendos_declarados", "Dividendos", AZUL), ("jcp_declarados", "JCP", VERDE),
                  ("recompras_dist", "Recompras", ROXO)]
    else:
        partes = [("proventos_pagos_caixa", "Dividendos + JCP pagos", AZUL), ("recompra_caixa", "Recompras pagas", ROXO)]
    for c, nome, cor in partes:
        fig.add_bar(x=df["periodo"], y=df[c] / div, name=nome, marker_color=cor, marker_opacity=op,
                    hovertemplate="%{y:,.1f}")
    total = sum(df[c] for c, _, _ in partes)
    lucro = df["lucro_liquido_acionistas"]
    n = len(df)
    fig.add_scatter(x=df["periodo"], y=lucro / div, name="Lucro líquido (100%)", mode="markers",
                    marker=dict(symbol="line-ew", size=max(14, int(420 / max(n, 1))),
                                line=dict(width=3, color=CINZA_ESCURO)),
                    hovertemplate="%{y:,.1f}")
    fig.update_layout(barmode="stack", bargap=0.3)
    _rotular_barras(fig, dec, "inside")
    _layout(fig, y_title=f"R$ {suf}")
    payout = total / lucro
    topo = np.maximum(total, lucro) / div
    fs = 12 if n <= 10 else 9
    for p, t, v in zip(range(n), topo, payout):
        nv = "Alto" if v > 1.2 else ("Médio" if v > 1.0 else "Forte")
        cor_txt = {"Alto": "#B03A1E", "Médio": "#9A6B00", "Forte": VERDE}[nv]
        fig.add_annotation(x=p, y=t, text=f"<b>{br(v * 100, 0)}%</b>", showarrow=False, yshift=12,
                           font=dict(size=fs, color=cor_txt))
    fig.update_yaxes(range=[0, float(np.nanmax(topo)) * 1.15])
    return fig


def micro_bloco4_ponte(tri, i0, i1, unidade):
    """Ponte da folga entre os trimestres i0 e i1 (fluxos somados em (i0, i1])."""
    r0, r1 = tri.loc[i0], tri.loc[i1]
    fl = tri.loc[i0 + 1:i1]
    folga0, folga1 = -r0["divida_liquida"], -r1["divida_liquida"]
    passos = [
        (f"Folga {r0['trimestre']}", folga0, "absolute"),
        ("FCL", fl["fcl"].sum(), "relative"),
        ("Aplicações no FCO", -fl["var_aplicacoes_financeiras"].sum(), "relative"),
        ("Proventos pagos", -fl["proventos_pagos_caixa"].sum(), "relative"),
        ("Recompras pagas", -fl["recompra_caixa"].sum(), "relative"),
        ("Juros", -fl["despesas_juros_dfc"].sum(), "relative"),
        ("Aquisições e outros invest.", fl["aquisicoes_outros_invest"].sum(), "relative"),
    ]
    residuo = folga1 - (folga0 + sum(v for _, v, m in passos[1:]))
    passos.append(("Câmbio e outros", residuo, "relative"))
    passos.append((f"Folga {r1['trimestre']}", 0, "total"))
    fig = _cascata(passos, unidade, destaque=["Aplicações no FCO"], dec=1 if escala(unidade)[1] == "bi" else 0)
    return fig, {p[0]: p[1] for p in passos}


def micro_bloco4_acumulado(anual, unidade, anos=(2021, 2025)):
    div, suf, dec = escala(unidade)
    df = anual[(anual["ano"] >= anos[0]) & (anual["ano"] <= anos[1])]
    a = df["fcl_pos_juros"].cumsum() / div
    b = df["retorno_acionista_caixa"].cumsum() / div
    x = df["periodo"]
    fig = go.Figure()
    fig.add_scatter(x=x, y=a, name="FCL depois dos juros (acumulado)", mode="lines+markers",
                    line=dict(color=CINZA, width=3), hovertemplate="%{y:,.1f}")
    fig.add_scatter(x=x, y=b, name="Devolvido ao acionista, pago (acumulado)", mode="lines+markers",
                    line=dict(color=AZUL, width=3), fill="tonexty", fillcolor="rgba(214,69,69,0.10)",
                    hovertemplate="%{y:,.1f}")
    # valores em todos os pontos: padrão aplicado em mostrar_grafico (utils/comum.py)
    _layout(fig, height=400, y_title=f"R$ {suf}")
    fig.update_yaxes(rangemode="tozero")
    return fig
