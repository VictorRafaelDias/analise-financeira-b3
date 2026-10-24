"""Aba 2 · Enzo — Receita, Diversificação & Apetite por Produtos.

Gráficos e leituras do Streamlit original do Enzo, agora lendo a DRE oficial (IS New Seg, 2T26) pelo
rótulo de cada linha, em vez de colunas fixas de um arquivo local.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import comum as c
from utils import dre
from utils.comum import br, pct

ABA = "Receita & Diversificação"

CORES_SEGMENTOS = {
    "Mercados": "#1f77b4",
    "Soluções para Mercado de Capitais": "#ff7f0e",
    "Soluções Analíticas de Dados": "#2ca02c",
    "Tecnologia": "#d62728",
    "Serviços de Apoio ao Mercado": "#8c564b",
    "Outros": "#7f7f7f",
    "Outras receitas": "#9467bd",
}
COR_RAIZ = "#4d4d4d"
COR_ANO = "#17becf"

CORES_PART = {
    "Renda Variável": "#54a24b",
    "Derivativos": "#4c78a8",
    "Renda Fixa e Crédito": "#f58518",
    "Soluções de Dados/Tecnologia": "#b279a2",
    "Demais receitas": "#9e9e9e",
}


def _participacao(t):
    """Valores e % da receita total por trimestre (Demais = total − 4 grupos, fecha 100%)."""
    total = t["receita_total"]
    v = pd.DataFrame({
        "Renda Variável": t["renda_variavel"],
        "Derivativos": t["derivativos"],
        "Renda Fixa e Crédito": t["rf_credito"],
        "Soluções de Dados/Tecnologia": t["solucoes_dados"] + t["tecnologia"],
    })
    v["Demais receitas"] = total - v.sum(axis=1)
    return v, v.div(total, axis=0)


def formatar_valor(v):
    """Formato do Enzo: 'R$ 9.327.395 mil' (entrada em R$ mil)."""
    return f"R$ {v:,.0f}".replace(",", ".") + " mil"


def construir_sankey(valores, periodos, titulo):
    """Sankey do Enzo (cores, rótulos em R$ mil e estrutura dele), para os períodos pedidos.

    Vários períodos: Receita total do intervalo → cada período → os 7 componentes de cada período.
    Um período só: Receita total do período → os 7 componentes (sem repetir a coluna do meio).
    As colunas usam a largura toda e cada componente fica na altura proporcional ao valor, para não se
    amontoar. Vários anos: rótulo só no maior componente de cada ano; um período: em todos com 3% ou mais.
    Os valores de todos os componentes ficam no balão do mouse.
    valores: DataFrame período x chaves da DRE (R$ mil).
    """
    labels, dados, cores_no, x_no, y_no = [], [], [], [], []
    source, target, value, link_color = [], [], [], []
    n = len(periodos)
    total = valores.loc[periodos, "receita_total"]
    x_raiz, x_periodo, x_seg = (0.001, 0.36, 0.999) if n > 1 else (0.001, None, 0.999)
    minimo = 0.30 if n > 1 else 0.03  # rótulo visível: só o maior componente na visão de vários anos

    idx_raiz = 0
    rotulo_raiz = f"{periodos[0]}-{periodos[-1]}" if n > 1 else str(periodos[0])
    labels.append(f"Receita Total {rotulo_raiz}<br>{formatar_valor(float(total.sum()))}")
    dados.append(f"Receita Total {rotulo_raiz}: {formatar_valor(float(total.sum()))}")
    cores_no.append(COR_RAIZ); x_no.append(x_raiz); y_no.append(0.5)

    faixa = 1 / n
    idx_periodo = {}
    if n > 1:
        for i, p in enumerate(periodos):
            idx_periodo[p] = len(labels)
            labels.append(f"{p}<br>{formatar_valor(float(total[p]))}")
            dados.append(f"Receita Total {p}: {formatar_valor(float(total[p]))}")
            cores_no.append(COR_ANO); x_no.append(x_periodo); y_no.append((i + 0.5) * faixa)
    else:
        idx_periodo[periodos[0]] = idx_raiz

    for i, p in enumerate(periodos):
        segs = [(k, nome) for k, nome in dre.SEGMENTOS if float(valores.loc[p, k]) > 0]
        soma = sum(float(valores.loc[p, k]) for k, _ in segs)
        acum = 0.0
        for k, nome in segs:
            v = float(valores.loc[p, k])
            centro = i * faixa + faixa * (0.05 + 0.9 * (acum + v / 2) / soma)  # posição proporcional ao valor
            acum += v
            labels.append(formatar_valor(v) if v / soma >= minimo else "")
            dados.append(f"{nome} · {p}: {formatar_valor(v)} ({br(v / soma * 100, 1)}%)")
            cores_no.append(CORES_SEGMENTOS[nome]); x_no.append(x_seg); y_no.append(centro)
            source.append(idx_periodo[p]); target.append(len(labels) - 1); value.append(v)
            h = CORES_SEGMENTOS[nome].lstrip("#")
            link_color.append(f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},0.4)")
        if n > 1:
            source.append(idx_raiz); target.append(idx_periodo[p]); value.append(float(total[p]))
            link_color.append("rgba(150,150,150,0.4)")

    fig = go.Figure(go.Sankey(
        arrangement="perpendicular",
        domain=dict(x=[0.12, 0.88], y=[0, 1]),  # mais estreito e centralizado
        textfont=dict(size=12),
        node=dict(pad=6, thickness=16, line=dict(color="black", width=0.4), label=labels, color=cores_no,
                  x=x_no, y=y_no, customdata=dados, hovertemplate="%{customdata}<extra></extra>"),
        link=dict(source=source, target=target, value=value, color=link_color,
                  hovertemplate="%{source.customdata} → %{target.customdata}<extra></extra>"),
    ))
    fig.update_layout(title=dict(text=titulo, y=1, yref="container", yanchor="top", pad=dict(t=34)),
                      margin=dict(l=10, r=10, t=80, b=10), font=dict(size=13), height=560 if n > 1 else 440,
                      separators=",.")
    return fig


def render(janela):
    st.markdown("## 💰 Receita, Diversificação & Apetite por Produtos")
    st.caption("Como a B3 gera receita e como o modelo se protege da volatilidade do mercado de "
               "ações.")
    st.markdown("<div class='tese'>Tese: a queda da receita de Renda Variável foi compensada por Derivativos, Renda "
                "Fixa e Crédito e Dados/Tecnologia — a receita total cresceu mesmo com a perda de peso das ações."
                "</div>", unsafe_allow_html=True)
    c.glossario("enzo")
    c.aviso_parcial(janela, "; os gráficos trimestrais incluem 1T26 e 2T26")

    valores, _, _ = dre.carregar_dre()
    anos = janela.anos_fechados
    if not anos:
        st.warning("A janela escolhida não tem ano fechado (2020–2025).")
        return
    t = dre.trimestral(valores, janela.ano_ini, janela.ano_fim)

    # Filtros próprios do painel original do Enzo (dentro da janela global da barra lateral)
    f1, f2 = st.columns(2)
    with f1:
        if len(anos) > 1:
            a_ini, a_fim = st.select_slider("Período anual (KPIs e gráficos anuais)", options=anos,
                                            value=(anos[0], anos[-1]), key=f"enz_anual_{anos[0]}_{anos[-1]}")
            anos = [x for x in anos if a_ini <= x <= a_fim]
    with f2:
        trimestres_janela = list(t.index)
        if len(trimestres_janela) > 1:
            t_ini, t_fim = st.select_slider("Período trimestral (gráficos trimestrais)", options=trimestres_janela,
                                            value=(trimestres_janela[0], trimestres_janela[-1]),
                                            key=f"enz_tri_{trimestres_janela[0]}_{trimestres_janela[-1]}")
            t = t.loc[t_ini:t_fim]
    a = dre.anual(valores, anos)
    ini, fim = anos[0], anos[-1]
    ant = fim - 1 if fim - 1 in a.index else None
    n = fim - ini

    rb, rl = a["receita_total"], a["receita_liquida"]
    rv = a["renda_variavel"]
    fora_rv = 1 - rv / rb
    marg = a["ebitda"] / rl
    dados_tec = a["solucoes_dados"] + a["tecnologia"]

    # ---------------------------------------------------------------- Indicadores-chave
    st.markdown(f"#### Indicadores-chave · {fim}")
    c.kpis([
        dict(rotulo=f"Receita bruta {fim}", valor=c.bi(rb[fim], md=False),
             delta=c.delta_txt(c.var(rb[fim], rb[ant]), ant) if ant else None, termo="Receita bruta"),
        dict(rotulo=f"Receita líquida {fim}", valor=c.bi(rl[fim], md=False),
             delta=c.delta_txt(c.var(rl[fim], rl[ant]), ant) if ant else None, termo="Receita líquida"),
        dict(rotulo=f"CAGR receita bruta ({ini}–{fim})",
             valor=pct(c.cagr(rb[ini], rb[fim], n), 1, sinal=True) if n else "—", termo="CAGR"),
        dict(rotulo=f"Receita fora de Renda Variável ({fim})", valor=pct(fora_rv[fim], 1),
             delta=c.delta_txt(fora_rv[fim] - fora_rv[ini], ini, "p.p.") if n else None,
             termo="Receita fora de Renda Variável"),
    ])

    # ---------------------------------------------------------------- Painel de alertas
    yoy_rb = c.var(rb[fim], rb[ant]) if ant else None
    yoy_dt = c.var(dados_tec[fim], dados_tec[ant]) if ant else None
    d_marg = marg[fim] - marg[ant] if ant else None
    peso_rv = rv[fim] / rb[fim]
    ded = -a["deducoes"] / rb
    rv_t = t["renda_variavel"]
    amp = rv_t.max() / rv_t.min() - 1 if len(rv_t) > 1 else None
    alertas = [
        dict(nome="Receita bruta no ano", valor=pct(yoy_rb, 1, sinal=True), delta=f"{ant}→{fim}" if ant else "",
             status=c.status_faixa(yoy_rb, 0.05, 0.0), desc=c.explica("Receita bruta"),
             regra="≥ 5% Confortável · 0–5% Atenção · < 0 Alerta"),
        dict(nome="Peso da Renda Variável", valor=pct(peso_rv, 1), delta=f"era {pct(rv[ini] / rb[ini], 1)} em {ini}",
             status=c.status_faixa(peso_rv, 0.25, 0.35, maior_melhor=False),
             desc="Quanto da receita depende do volume de ações negociado. Quanto menor, menos volátil.",
             regra="≤ 25% Confortável · 25–35% Atenção · > 35% Alerta"),
        dict(nome="Margem EBITDA (variação)", valor=c.pp(d_marg) if d_marg is not None else "—",
             delta=f"{pct(marg[ant], 1)} → {pct(marg[fim], 1)}" if ant else "",
             status=c.status_faixa(d_marg, 0.0, -0.03), desc=c.explica("Margem EBITDA"),
             regra="≥ 0 Confortável · até −3 p.p. Atenção · < −3 p.p. Alerta"),
        dict(nome="Dados e Tecnologia no ano", valor=pct(yoy_dt, 1, sinal=True),
             delta=f"{c.bi(dados_tec[fim], md=False)} em {fim}", status=c.status_faixa(yoy_dt, 0.05, 0.0),
             desc="Crescimento das receitas de Soluções Analíticas de Dados + Tecnologia (diversificação).",
             regra="≥ 5% Confortável · 0–5% Atenção · < 0 Alerta"),
        dict(nome="Deduções sobre a receita", valor=pct(ded[fim], 1), delta=f"entre {pct(ded.min(), 1)} e "
             f"{pct(ded.max(), 1)} na janela", status="Informativo", desc=c.explica("Deduções da receita"),
             regra="informativo"),
        dict(nome="Oscilação trimestral da RV", valor=pct(amp, 0) if amp is not None else "—",
             delta=f"melhor x pior trimestre ({t.index[0]}–{t.index[-1]})", status="Informativo",
             desc="Diferença entre o melhor e o pior trimestre de receita de Renda Variável: mede a volatilidade.",
             regra="informativo"),
    ]
    c.painel_alertas(alertas, leitura=c.leitura_alertas(alertas[:4], f"em {fim}"), por_linha=3,
                     rodape="Regras definidas pelo grupo para leitura rápida; não são metas oficiais da B3.")

    # ---------------------------------------------------------------- 1. Sankey + oportunidade por segmento
    c.cabecalho_secao("Distribuição da receita bruta", "De onde vem cada real da receita da B3",
                      "Do total do período para cada ano e, em cada ano, para os 7 componentes que somam exatamente a "
                      "receita total.")
    leg = st.columns(len(CORES_SEGMENTOS))
    for col, (seg, cor) in zip(leg, CORES_SEGMENTOS.items()):
        col.markdown(f"<div style='display:flex;align-items:center;gap:6px' title=\"{c.explica(seg)}\">"
                     f"<div style='width:12px;height:12px;background:{cor};border-radius:3px;flex-shrink:0'></div>"
                     f"<span style='font-size:12px'>{seg}</span></div>", unsafe_allow_html=True)
    ver = st.segmented_control("Ver o fluxo por", ["Todos os anos", "Ano", "Trimestre"], default="Todos os anos",
                               key="enz_sk_modo") or "Todos os anos"
    if ver == "Ano":
        ano_sk = st.segmented_control("Ano", [str(x) for x in anos[::-1]], default=str(fim), key="enz_sk_ano") or str(fim)
        fig_sk = construir_sankey(a.rename(index=str), [ano_sk], f"B3 - Composição da Receita Total ({ano_sk})")
    elif ver == "Trimestre":
        trimestres = list(t.index)
        tri_sk = c.bloco_trimestre("Trimestre", trimestres, trimestres[-1], key="enz_sk_tri")
        fig_sk = construir_sankey(t, [tri_sk], f"B3 - Composição da Receita Total ({tri_sk})")
    else:
        fig_sk = construir_sankey(a.rename(index=str), [str(x) for x in anos],
                                  f"B3 - Composição da Receita Total ({ini}-{fim})")
    c.mostrar_grafico(fig_sk, key="enz_sankey")
    st.caption("Cada cor é um componente da receita (legenda acima). Em \"Todos os anos\" só o maior "
               "componente (Mercados) tem rótulo; escolha um ano ou trimestre para ver todos os valores, ou passe o "
               "mouse sobre as faixas.")

    st.markdown("**Crescimento de cada segmento na janela (cor = oportunidade)**")
    seg = pd.DataFrame([(nome, a.loc[ini, k], a.loc[fim, k]) for k, nome in dre.SEGMENTOS
                        if a.loc[ini, k] > 0 and a.loc[fim, k] > 0], columns=["seg", "ini", "fim"])
    seg["cagr"] = [c.cagr(i, f, n) if n else c.var(f, i) for i, f in zip(seg["ini"], seg["fim"])]
    rv_cagr = c.cagr(rv[ini], rv[fim], n) if n else None
    linhas = pd.concat([seg, pd.DataFrame([("Renda Variável (dentro de Mercados)", rv[ini], rv[fim], rv_cagr)],
                                          columns=seg.columns)]).sort_values("cagr")
    niv = ["Nulo" if s_ == "Outras receitas" else c.nivel_por_variacao(v) for s_, v in zip(linhas["seg"], linhas["cagr"])]
    fig = go.Figure(go.Bar(
        y=linhas["seg"], x=linhas["cagr"] * 100, orientation="h", marker_color=[c.cor_oport(x) for x in niv],
        text=[pct(v, 1, sinal=True) for v in linhas["cagr"]], textposition="outside", cliponaxis=False,
        hovertext=[f"<b>{s}</b><br>{c.bi(i, md=False)} → {c.bi(f_, md=False)}<br>CAGR {pct(v, 1, sinal=True)} a.a."
                   f"<br>Oportunidade: {nv} ({c.OPORT_DESC[nv]})" + c.dica(s.split(' (')[0])
                   for s, i, f_, v, nv in zip(linhas["seg"], linhas["ini"], linhas["fim"], linhas["cagr"], niv)],
        hoverinfo="text"))
    c.layout_base(fig, altura=380, legenda=False)
    fig.update_xaxes(title_text=f"Crescimento médio ao ano, {ini}–{fim} (%)", ticksuffix="%", zeroline=True)
    fig.update_yaxes(type="category")
    c.mostrar_grafico(fig, key="enz_cagr")
    c.legenda_oportunidade(("Alto", "Médio", "Nulo", "Forte"))
    st.caption("“Outras receitas” é a reversão de provisões e recuperação de despesas: efeito contábil, por isso "
               "aparece como Nulo.")
    c.leitura(f"Em {fim}, <b>{pct(fora_rv[fim], 1)}</b> da receita veio de fora da Renda Variável "
              f"(era {pct(fora_rv[ini], 1)} em {ini}). Renda Variável variou {pct(rv_cagr, 1, sinal=True)} ao ano.")
    c.diagnostico([
        "Mercados (derivativos, renda variável, renda fixa e empréstimo de ativos) seguem como a maior parte da receita.",
        "Soluções Analíticas de Dados e Tecnologia são as linhas que mais cresceram: a diversificação está acontecendo.",
        "Renda Variável é o único grande componente em queda: a receita ficou menos dependente do volume de ações.",
    ])
    c.fonte([("Receita total e segmentos", "Planilha B3 · IS (New Seg)", "Linhas 4, 5, 10, 14, 18, 19, 20 e 21"),
             ("Renda Variável", "Planilha B3 · IS (New Seg)", "Linha 7 (dentro de Mercados)")],
            nota="Validação ao carregar: os 7 componentes somam exatamente a Receita total em todos os anos.")

    # ---------------------------------------------------------------- 2. Bruta vs líquida e RV vs RF
    c.cabecalho_secao("Receita bruta, líquida e o equilíbrio entre Renda Variável e Renda Fixa")
    g1, g2 = st.columns(2)
    x = [str(y) for y in anos]
    with g1:
        fig = go.Figure()
        fig.add_scatter(x=x, y=rb / 1e6, name="Receita bruta", mode="lines+markers+text",
                        texttemplate="%{y:.2f}", textposition="top center", line=dict(color="#4c78a8", width=3),
                        hovertext=[f"<b>{y}</b><br>Receita bruta: R$ {br(v / 1e6, 2)} bi" + c.dica("Receita bruta")
                                   for y, v in rb.items()], hoverinfo="text")
        fig.add_scatter(x=x, y=rl / 1e6, name="Receita líquida", mode="lines+markers+text",
                        texttemplate="%{y:.2f}", textposition="bottom center",
                        line=dict(color="#e45756", width=3, dash="dash"),
                        hovertext=[f"<b>{y}</b><br>Receita líquida: R$ {br(v / 1e6, 2)} bi<br>Deduções: "
                                   f"{pct(ded[y], 1)} da bruta" + c.dica("Receita líquida") for y, v in rl.items()],
                        hoverinfo="text")
        c.layout_base(fig, "Evolução da receita: bruta vs. líquida", y_titulo="R$ bilhões")
        fig.update_yaxes(range=[min(rl.min(), rb.min()) / 1e6 * 0.92, max(rl.max(), rb.max()) / 1e6 * 1.06])
        fig.update_xaxes(type="category")
        c.mostrar_grafico(fig, key="enz_brliq")
        if n:
            c.leitura(f"De {ini} a {fim}, a receita bruta variou {pct(c.var(rb[fim], rb[ini]), 1, sinal=True)} e a "
                      f"líquida {pct(c.var(rl[fim], rl[ini]), 1, sinal=True)}. As deduções oscilaram entre "
                      f"{pct(ded.min(), 1)} e {pct(ded.max(), 1)} da receita bruta.")
    with g2:
        rf = a["rf_credito"]
        fig = go.Figure()
        for serie, nome, padrao in ((rv, "Renda Variável (lisa)", ""), (rf, "Renda Fixa e Crédito (hachurada)", "/")):
            yoy = serie / serie.shift(1) - 1
            niv = [c.nivel_por_variacao(v) if pd.notna(v) else "Baixo" for v in yoy]
            termo = nome.split(" (")[0]
            fig.add_bar(x=x, y=serie / 1e6, name=nome, marker_color=[c.cor_oport(v) for v in niv],
                        marker_pattern_shape=padrao, marker_line=dict(color="#333", width=0.6),
                        texttemplate="%{y:.2f}", textposition="outside",
                        hovertext=[f"<b>{termo} · {y}</b><br>R$ {br(v / 1e6, 2)} bi"
                                   + (f"<br>Variação: {pct(yy, 1, sinal=True)}" if pd.notna(yy) else "")
                                   + f"<br>Oportunidade: {nv}" + c.dica(termo)
                                   for y, v, yy, nv in zip(serie.index, serie, yoy, niv)], hoverinfo="text")
        fig.update_layout(barmode="group")
        c.layout_base(fig, "Renda Variável vs. Renda Fixa e Crédito (cor = variação no ano)", y_titulo="R$ bilhões")
        fig.update_yaxes(range=[0, max(rv.max(), rf.max()) / 1e6 * 1.18])
        fig.update_xaxes(type="category")
        c.mostrar_grafico(fig, key="enz_rvrf")
        c.leitura(f"Renda Fixa e Crédito equivalia a {pct(rf[ini] / rv[ini], 0)} da Renda Variável em {ini} e a "
                  f"<b>{pct(rf[fim] / rv[fim], 0)}</b> em {fim}.")
    c.legenda_oportunidade(("Alto", "Médio", "Forte"))
    c.diagnostico([
        "As deduções (PIS/Cofins e ISS) ficam estáveis perto de 10% da receita bruta: pouca alavanca de gestão.",
        "Renda Fixa e Crédito mais que dobrou e se aproximou da Renda Variável: o 'apetite' migrou para renda fixa "
        "com juros altos.",
    ])
    c.fonte([("Receita bruta e líquida", "Planilha B3 · IS (New Seg)", "Linhas 4 e 25"),
             ("Deduções", "Planilha B3 · IS (New Seg)", "Linha 22 (PIS/Cofins 23, ISS 24)"),
             ("Renda Variável; Renda Fixa e Crédito", "Planilha B3 · IS (New Seg)", "Linhas 7 e 8")])

    # ---------------------------------------------------------------- 3. Trimestral
    c.cabecalho_secao("Ritmo trimestral", "A Renda Variável oscila; os demais segmentos estabilizam a receita")
    valores_t, part = _participacao(t)
    tri = list(t.index)
    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        for s in part.columns:
            fig.add_scatter(x=tri, y=part[s] * 100, name=s, mode="lines", stackgroup="um",
                            line=dict(width=0.6, color=CORES_PART[s]), fillcolor=CORES_PART[s],
                            hovertext=[f"<b>{s} · {q}</b><br>{pct(p, 1)} da receita · R$ {br(v / 1e3, 0)} mi"
                                       + c.dica(s.split("/")[0].replace("Soluções de Dados", "Soluções Analíticas de Dados"))
                                       for q, p, v in zip(tri, part[s], valores_t[s])], hoverinfo="text")
        c.layout_base(fig, "Participação de cada segmento na receita (trimestral)", y_titulo="% da receita total")
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        fig.update_xaxes(type="category", tickangle=-45, nticks=14)
        c.mostrar_grafico(fig, key="enz_part")
        c.leitura(f"Renda Variável: {pct(part['Renda Variável'].iloc[0], 1)} ({tri[0]}) → "
                  f"<b>{pct(part['Renda Variável'].iloc[-1], 1)}</b> ({tri[-1]}). Dados/Tecnologia: "
                  f"{pct(part['Soluções de Dados/Tecnologia'].iloc[0], 1)} → "
                  f"<b>{pct(part['Soluções de Dados/Tecnologia'].iloc[-1], 1)}</b>.")
    with g2:
        todos = valores.loc["renda_variavel", dre.trimestres_dre(valores)]
        aa = todos / todos.shift(4) - 1
        serie = rv_t / 1e3
        niv = [c.nivel_por_variacao(aa[q]) if pd.notna(aa[q]) else "Baixo" for q in tri]
        fig = go.Figure()
        fig.add_scatter(x=tri, y=serie, name="Receita de Renda Variável", mode="lines+markers",
                        line=dict(color=CORES_PART["Renda Variável"], width=3),
                        marker=dict(size=11, color=[c.cor_oport(v) for v in niv], line=dict(color="white", width=1)),
                        hovertext=[f"<b>{q}</b><br>R$ {br(v, 0)} mi<br>Var. a/a: "
                                   f"{pct(aa[q], 1, sinal=True) if pd.notna(aa[q]) else 'n/d'}<br>Oportunidade: {nv}"
                                   + c.dica("Renda Variável") for q, v, nv in zip(tri, serie, niv)], hoverinfo="text")
        media = float(serie.mean())
        fig.add_hline(y=media, line_dash="dash", line_color="#9e9e9e",
                      annotation_text=f"Média: R$ {br(media, 0)} mi", annotation_position="top right",
                      annotation_font=dict(size=11))
        c.layout_base(fig, "Receita de Renda Variável por trimestre (cor = variação a/a)", y_titulo="R$ milhões",
                      legenda=False)
        fig.update_yaxes(range=[serie.min() * 0.85, serie.max() * 1.1])
        fig.update_xaxes(type="category", tickangle=-45, nticks=14)
        c.mostrar_grafico(fig, key="enz_rvtri")
        c.leitura(f"Pico em {serie.idxmax()} (R$ {br(serie.max(), 0)} mi) e vale em {serie.idxmin()} "
                  f"(R$ {br(serie.min(), 0)} mi). O ADTV não consta na DRE; a receita de Renda Variável é a referência.")
    c.diagnostico([
        "A participação da Renda Variável cai de forma contínua; Renda Fixa e Crédito e Dados/Tecnologia ocupam o espaço.",
        "A receita de Renda Variável varia bastante entre trimestres (volume de negociação), enquanto a receita total é "
        "mais estável: a diversificação reduz a volatilidade.",
    ])
    c.fonte([("Segmentos por trimestre", "Planilha B3 · IS (New Seg)", "Linhas 4, 6, 7, 8, 14 e 18; colunas 1T20–2T26")])

    # ---------------------------------------------------------------- 4. Do faturamento ao resultado
    c.cabecalho_secao("Do faturamento ao resultado", "Quanto sobra da receita, e a que custo")
    g1, g2 = st.columns(2)
    r = a.loc[fim]
    with g1:
        outros = r["lair"] - r["resultado_operacional"]
        passos = [
            dict(rotulo="Receita bruta", valor=r["receita_total"], tipo="total", cor=c.AZUL,
                 hover=f"<b>Receita bruta</b><br>{c.bi(r['receita_total'], md=False)}" + c.dica("Receita bruta")),
            dict(rotulo="Deduções", valor=r["deducoes"], tipo="passo", cor=c.cor_oport("Médio"),
                 hover=f"<b>Deduções</b><br>{pct(-r['deducoes'] / r['receita_total'], 1)} da bruta<br>Oportunidade: Médio"
                       + c.dica("Deduções da receita")),
            dict(rotulo="Despesas operacionais", valor=r["despesas"], tipo="passo", cor=c.cor_oport("Médio"),
                 hover=f"<b>Despesas (com D&A)</b><br>{pct(-r['despesas'] / r['receita_total'], 1)} da bruta"
                       "<br>Oportunidade: Médio (detalhe na aba de Eficiência)" + c.dica("Despesas operacionais")),
            dict(rotulo="Resultado financeiro e outros", valor=outros, tipo="passo",
                 cor=c.cor_oport("Forte" if outros >= 0 else "Médio"),
                 hover=f"<b>Resultado financeiro e outros</b><br>{c.bi(outros, md=False)}" + c.dica("Resultado financeiro")),
            dict(rotulo="IR e CS", valor=r["ir"], tipo="passo", cor=c.cor_oport("Médio"),
                 hover=f"<b>IR e CS</b><br>{pct(-r['ir'] / r['receita_total'], 1)} da bruta<br>Oportunidade: Médio"
                       + c.dica("Imposto de renda e contribuição social")),
            dict(rotulo="Lucro líquido", valor=r["lucro"], tipo="total", cor=c.AZUL,
                 hover=f"<b>Lucro líquido</b><br>{c.bi(r['lucro'], md=False)} · {pct(r['lucro'] / r['receita_total'], 1)}"
                       " da receita bruta"),
        ]
        c.mostrar_grafico(c.cascata(passos, f"Da receita bruta ao lucro líquido ({fim})"), key="enz_cascata")
        c.leitura(f"Em {fim}, da receita bruta: {pct(-r['deducoes'] / r['receita_total'], 1)} vão para deduções, "
                  f"{pct(-r['despesas'] / r['receita_total'], 1)} para despesas e {pct(-r['ir'] / r['receita_total'], 1)} "
                  f"para IR/CS. O lucro fica com <b>{pct(r['lucro'] / r['receita_total'], 1)}</b>.")
    with g2:
        ml = a["lucro"] / rl
        fig = go.Figure()
        fig.add_bar(x=x, y=rl / 1e6, name="Receita líquida (R$ bi)", marker_color="#c9d6e8",
                    texttemplate="%{y:.2f}", textposition="inside", insidetextanchor="start",
                    hovertext=[f"<b>{y}</b><br>Receita líquida: R$ {br(v / 1e6, 2)} bi" + c.dica("Receita líquida")
                               for y, v in rl.items()], hoverinfo="text")
        for serie, nome, cor, dash, termo in ((marg, "Margem EBITDA", "#4c78a8", None, "Margem EBITDA"),
                                              (ml, "Margem líquida", "#e45756", "dash", "Margem líquida")):
            dif = serie - serie.shift(1)
            niv = [("Alto" if v < -0.01 else "Médio" if v < 0 else "Forte") if pd.notna(v) else "Baixo" for v in dif]
            fig.add_scatter(x=x, y=serie * 100, name=nome, yaxis="y2", mode="lines+markers+text",
                            texttemplate="%{y:.1f}%", textposition="top center",
                            line=dict(color=cor, width=3, dash=dash),
                            marker=dict(size=11, color=[c.cor_oport(v) for v in niv], line=dict(color=cor, width=2)),
                            hovertext=[f"<b>{nome} · {y}</b><br>{pct(v, 1)}"
                                       + (f" ({c.pp(dd)})" if pd.notna(dd) else "") + f"<br>Oportunidade: {nv}"
                                       + c.dica(termo) for y, v, dd, nv in zip(serie.index, serie, dif, niv)],
                            hoverinfo="text")
        c.layout_base(fig, "Receita líquida vs. margens (marcador = variação)", y_titulo="R$ bilhões")
        lo = max(0, min(ml.min(), marg.min()) * 100 - 12)
        hi = min(100, max(ml.max(), marg.max()) * 100 + 8)
        fig.update_layout(yaxis2=dict(title=dict(text="% da receita líquida"), overlaying="y", side="right",
                                      showgrid=False, ticksuffix="%", range=[lo, hi]))
        fig.update_layout(yaxis=dict(range=[0, rl.max() / 1e6 * 1.15]))
        fig.update_xaxes(type="category")
        c.mostrar_grafico(fig, key="enz_margens")
        peso = dados_tec / rb
        c.leitura(f"Margem EBITDA: {pct(marg[ini], 1)} ({ini}) → <b>{pct(marg[fim], 1)}</b> ({fim}); "
                  f"Dados/Tecnologia: {pct(peso[ini], 1)} → {pct(peso[fim], 1)} da receita bruta."
                  + (" Uma leitura possível: a diversificação trouxe receitas de margem menor, ainda em patamar elevado."
                     if marg[fim] < marg[ini] and peso[fim] > peso[ini] else ""))
    c.legenda_oportunidade()
    c.diagnostico([
        "Mesmo com a receita crescendo, a margem EBITDA caiu: as novas linhas (dados, tecnologia) têm custo maior.",
        "O resultado financeiro ficou positivo nos últimos anos e ajudou o lucro.",
    ])
    c.fonte([("Despesas, resultado operacional, LAIR, IR, lucro", "Planilha B3 · IS (New Seg)",
              "Linhas 26, 39, 50, 51 e 56"), ("EBITDA", "Planilha B3 · IS (New Seg)", "Linha 66")],
            nota="Mudança em relação ao Streamlit original: os dados vêm da planilha oficial 2T26 (B3 RI), lidos pelo "
                 "rótulo da linha, em vez de um caminho local com colunas fixas.")

    with st.expander("Ver tabela de segmentos usada no gráfico"):
        tab = pd.DataFrame({nome: a[k] for k, nome in dre.SEGMENTOS}).T
        tab.loc["Receita total"] = a["receita_total"]
        st.dataframe((tab / 1e3).round(1).rename(columns=str), width="stretch")
        st.caption("R$ milhões.")

    # ---------------------------------------------------------------- Oportunidades
    if n:
        c.oportunidade(janela, ABA, "Alto" if rv_cagr is not None and rv_cagr < 0 else "Médio",
                       "Receita de Renda Variável em queda",
                       f"A receita de Renda Variável variou {pct(rv_cagr, 1, sinal=True)} ao ano ({ini}–{fim}) e caiu "
                       f"para {pct(peso_rv, 1)} da receita.",
                       "Estimular volume de ações (novos produtos, ETFs/BDRs, varejo) e revisar a tarifação por faixa de volume.",
                       f"{c.bi(rv[fim], md=False)} em {fim}")
        c.oportunidade(janela, ABA, "Médio" if marg[fim] < marg[ini] else "Forte", "Margem menor na diversificação",
                       f"A margem EBITDA foi de {pct(marg[ini], 1)} para {pct(marg[fim], 1)} enquanto Dados/Tecnologia "
                       "ganhou peso.",
                       "Acompanhar a rentabilidade das novas linhas (dados, tecnologia) e escalar as de maior margem.")
        c.oportunidade(janela, ABA, "Forte", "Diversificação da receita",
                       f"{pct(fora_rv[fim], 1)} da receita vem de fora da Renda Variável (era {pct(fora_rv[ini], 1)}).",
                       "Manter: Renda Fixa e Crédito e Dados/Tecnologia reduzem a dependência do volume de ações.")
        c.oportunidade(janela, ABA, "Médio", "Volatilidade trimestral",
                       f"A receita de Renda Variável variou {pct(amp, 0)} entre o melhor e o pior trimestre.",
                       "Ampliar receitas recorrentes (assinaturas de dados, tecnologia) para suavizar o resultado.")
    c.bloco_oportunidades(janela, ABA)
