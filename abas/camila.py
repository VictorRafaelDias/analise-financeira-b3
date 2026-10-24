"""Aba 1 · Camila — Desenvolvimento de Mercado, Impacto Econômico & ODS.

Dados digitados pela Camila no Streamlit original (fontes B3 citadas por ela). Mantidos sem alteração.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from abas import camila_mercado
from utils import comum as c
from utils.comum import br, pct

ABA = "Desenvolvimento de Mercado"

# Investidores pessoa física em renda variável (milhões de CPFs, fim de ano), custódia (R$ bi, fim de ano)
# e emissões públicas de dívida corporativa (R$ bi no ano). Emissões de 2020–2022 ficam vazias para não
# misturar séries com definições diferentes (decisão da Camila).
DADOS = pd.DataFrame({
    "ano": [2020, 2021, 2022, 2023, 2024, 2025],
    "investidores": [2.7, 4.2, 5.0, 5.0, 5.3, 5.5],
    "custodia": [457.1, 500.1, 459.5, 550.8, 528.3, 636.2],
    "emissoes": [None, None, None, 345.4, 608.1, 647.5],
})
COMPOSICAO = pd.DataFrame({
    "ano": [2024] * 4 + [2025] * 4,
    "instrumento": ["Debêntures", "CRI", "CRA", "Notas comerciais"] * 2,
    "valor": [465.8, 57.5, 40.8, 44.0, 496.3, 50.8, 46.0, 54.0],
})
TERMO_INSTR = {"Debêntures": "Debêntures", "CRI": "CRI", "CRA": "CRA", "Notas comerciais": "Notas comerciais"}


def _yoy(serie):
    return serie / serie.shift(1) - 1


def _fig_serie(df, col, nome, termo, tipo, unidade_txt, fmt):
    """Linha ou barras com cada ponto colorido pela variação anual (cor de oportunidade)."""
    d = df.dropna(subset=[col]).copy()
    d["yoy"] = _yoy(d[col])
    niveis = [c.nivel_por_variacao(v) if pd.notna(v) else "Baixo" for v in d["yoy"]]
    cores = [c.cor_oport(n) for n in niveis]
    hover = [
        f"<b>{a}</b><br>{nome}: {fmt(v)}"
        + (f"<br>Variação no ano: {pct(y, 1, sinal=True)}" if pd.notna(y) else "<br>Primeiro ano da série")
        + f"<br>Oportunidade: {n} ({c.OPORT_DESC[n]})" + c.dica(termo)
        for a, v, y, n in zip(d["ano"], d[col], d["yoy"], niveis)
    ]
    x = d["ano"].astype(str)
    fig = go.Figure()
    if tipo == "linha":
        fig.add_scatter(x=x, y=d[col], mode="lines+markers+text", text=[fmt(v) for v in d[col]],
                        textposition="top center", line=dict(color=c.AZUL, width=3),
                        marker=dict(size=14, color=cores, line=dict(color="white", width=1.5)),
                        hovertext=hover, hoverinfo="text", name=nome)
    else:
        fig.add_bar(x=x, y=d[col], marker_color=cores, text=[fmt(v) for v in d[col]], textposition="outside",
                    hovertext=hover, hoverinfo="text", name=nome, cliponaxis=False)
        fig.update_yaxes(range=[0, d[col].max() * 1.18])
    c.layout_base(fig, altura=420, y_titulo=unidade_txt, legenda=False)
    fig.update_xaxes(type="category")
    return fig, d


def render(janela):
    st.markdown("## 📊 Desenvolvimento de Mercado, Impacto Econômico & ODS")
    st.caption("Como a base de investidores, a custódia e as emissões de dívida evoluíram, e o "
               "que isso diz sobre o financiamento das empresas e os ODS.")
    st.info("Investidores e custódia são **posições no fim de cada ano** (saldos). Emissões são o **volume emitido "
            "ao longo do ano** (fluxo). Por isso, são indicadores diferentes e não se somam.")
    c.glossario("camila")
    c.aviso_parcial(janela)

    df = DADOS[(DADOS["ano"] >= janela.ano_ini) & (DADOS["ano"] <= janela.ano_ref)].reset_index(drop=True)
    if df.empty:
        st.warning("Não há dados desta aba na janela escolhida (série de 2020 a 2025).")
        return
    ini, fim = df.iloc[0], df.iloc[-1]
    ant = df.iloc[-2] if len(df) > 1 else None
    n = int(fim["ano"] - ini["ano"])
    cust_inv = df["custodia"] / df["investidores"]  # R$ bi / milhões = R$ mil por investidor

    # ---------------------------------------------------------------- Indicadores-chave
    st.markdown(f"#### Indicadores-chave · {int(fim['ano'])}")
    v_inv = c.var(fim["investidores"], ini["investidores"])
    v_cus = c.var(fim["custodia"], ini["custodia"])
    v_emi = c.var(fim["emissoes"], ant["emissoes"]) if ant is not None else None
    c.kpis([
        dict(rotulo=f"Investidores em {int(fim['ano'])}", valor=f"{br(fim['investidores'], 1)} milhões",
             delta=None if n == 0 else c.delta_txt(v_inv, int(ini["ano"])), termo="Investidores em renda variável"),
        dict(rotulo=f"Custódia em {int(fim['ano'])}", valor=f"R$ {br(fim['custodia'], 1)} bi",
             delta=None if n == 0 else c.delta_txt(v_cus, int(ini["ano"])), termo="Valor em custódia"),
        dict(rotulo=f"Emissões em {int(fim['ano'])}",
             valor="—" if pd.isna(fim["emissoes"]) else f"R$ {br(fim['emissoes'], 1)} bi",
             delta=c.delta_txt(v_emi, int(ant["ano"])) if ant is not None else None,
             termo="Emissões de dívida corporativa"),
        dict(rotulo="Custódia por investidor", valor=f"R$ {br(cust_inv.iloc[-1], 0)} mil",
             delta=None if n == 0 else c.delta_txt(c.var(cust_inv.iloc[-1], cust_inv.iloc[0]), int(ini["ano"])),
             termo="Custódia por investidor"),
    ])
    st.caption("Fonte: B3 — pessoas físicas em renda variável e emissões públicas de dívida corporativa. "
               "Deltas contra o primeiro ano da janela (emissões: contra o ano anterior).")

    # ---------------------------------------------------------------- Painel de alertas
    yoy_inv = c.var(fim["investidores"], ant["investidores"]) if ant is not None else None
    yoy_cus = c.var(fim["custodia"], ant["custodia"]) if ant is not None else None
    cagr_inv = c.cagr(ini["investidores"], fim["investidores"], n)
    cagr_cus = c.cagr(ini["custodia"], fim["custodia"], n)
    ref_ant = int(ant["ano"]) if ant is not None else "—"
    alertas = [
        dict(nome="Novos investidores no ano", valor=pct(yoy_inv, 1, sinal=True),
             delta=f"{br(ant['investidores'], 1)} → {br(fim['investidores'], 1)} mi ({ref_ant}→{int(fim['ano'])})"
             if ant is not None else "", status=c.status_faixa(yoy_inv, 0.05, 0.0),
             desc="Crescimento da base de investidores pessoa física no último ano da janela.",
             regra="≥ 5% Confortável · 0–5% Atenção · < 0 Alerta"),
        dict(nome="Custódia no ano", valor=pct(yoy_cus, 1, sinal=True),
             delta=f"R$ {br(ant['custodia'], 1)} → {br(fim['custodia'], 1)} bi" if ant is not None else "",
             status=c.status_faixa(yoy_cus, 0.05, 0.0),
             desc="Variação do valor guardado na B3 por pessoas físicas (preço dos ativos + novas aplicações).",
             regra="≥ 5% Confortável · 0–5% Atenção · < 0 Alerta"),
        dict(nome="Emissões de dívida no ano", valor=pct(v_emi, 1, sinal=True),
             delta=f"R$ {br(fim['emissoes'], 1)} bi em {int(fim['ano'])}" if pd.notna(fim["emissoes"]) else "",
             status=c.status_faixa(v_emi, 0.10, 0.0),
             desc="Ritmo de captação das empresas via mercado de capitais (canal de financiamento, ODS 8 e 9).",
             regra="≥ 10% Confortável · 0–10% Atenção · < 0 Alerta"),
        dict(nome="Investidores: crescimento médio", valor=pct(cagr_inv, 1, sinal=True) + " a.a.",
             delta=f"CAGR {int(ini['ano'])}–{int(fim['ano'])}", status="Informativo",
             desc="Crescimento médio composto da base de investidores na janela.", regra="informativo"),
        dict(nome="Custódia: crescimento médio", valor=pct(cagr_cus, 1, sinal=True) + " a.a.",
             delta=f"CAGR {int(ini['ano'])}–{int(fim['ano'])}", status="Informativo",
             desc="Crescimento médio composto da custódia na janela.", regra="informativo"),
        dict(nome="Custódia por investidor", valor=f"R$ {br(cust_inv.iloc[-1], 0)} mil",
             delta=f"era R$ {br(cust_inv.iloc[0], 0)} mil em {int(ini['ano'])}", status="Informativo",
             desc="Tamanho médio da carteira por CPF. Cai quando entram muitos investidores pequenos.",
             regra="informativo"),
    ]
    c.painel_alertas(alertas, leitura=c.leitura_alertas(alertas[:3], f"em {int(fim['ano'])}"),
                     rodape="Regras definidas pelo grupo para leitura rápida; não são metas oficiais da B3.", por_linha=3)
    c.legenda_oportunidade(("Alto", "Médio", "Forte"))
    st.caption("Nos gráficos desta aba, cada ponto é colorido pela variação contra o ano anterior: "
               "🟥 queda · 🟨 crescimento abaixo de 5% · 🟩 crescimento de 5% ou mais.")

    # ---------------------------------------------------------------- 1. Investidores
    c.cabecalho_secao("📈 Evolução dos investidores",
                      "A base de investidores dobrou, mas parou de crescer no ritmo de 2021",
                      "O número de investidores mostra a participação das pessoas físicas no mercado de renda "
                      "variável ao longo do tempo.")
    fig, d = _fig_serie(df, "investidores", "Investidores", "Investidores em renda variável", "linha",
                        "Milhões de investidores", lambda v: br(v, 1))
    c.mostrar_grafico(fig, key="cam_inv")
    yoy = d["yoy"]
    if len(d) > 1:
        i_max = yoy.idxmax()
        c.leitura(f"De {int(ini['ano'])} a {int(fim['ano'])}, a base foi de <b>{br(ini['investidores'], 1)}</b> para "
                  f"<b>{br(fim['investidores'], 1)} milhões</b> ({pct(v_inv, 0, sinal=True)}). O maior salto foi em "
                  f"{int(d.loc[i_max, 'ano'])} ({pct(yoy[i_max], 0, sinal=True)}); no último ano, "
                  f"{pct(yoy.iloc[-1], 1, sinal=True)}.")
    c.diagnostico([
        "Entrada forte de pessoas físicas em 2020–2021 (+56% em 2021), no período de juros baixos.",
        "De 2022 a 2025 a base praticamente estabilizou: 5,0 → 5,5 milhões (cerca de +3% ao ano), "
        "com 2023 sem crescimento.",
        "Oportunidade: retomar a captação de novos investidores (educação financeira, produtos de entrada).",
    ])
    c.fonte([("Investidores PF em renda variável", "B3 — indicadores de pessoas físicas",
              "Posição no encerramento de cada ano, em milhões de CPFs")],
            nota="Valores digitados a partir da publicação da B3; conferir com a fonte.")

    # ---------------------------------------------------------------- 2. Custódia
    c.cabecalho_secao("🏛️ Evolução do valor em custódia",
                      "A custódia cresceu, mas oscila com o preço dos ativos",
                      "O valor em custódia é o valor dos ativos mantidos pelos investidores. Reflete tanto novas "
                      "aplicações quanto a variação de preço dos ativos.")
    fig, d = _fig_serie(df, "custodia", "Custódia", "Valor em custódia", "barra", "R$ bilhões",
                        lambda v: f"R$ {br(v, 1)} bi")
    c.mostrar_grafico(fig, key="cam_cus")
    quedas = d[d["yoy"] < 0]["ano"].astype(int).tolist()
    c.leitura(f"A custódia foi de <b>R$ {br(ini['custodia'], 1)} bi</b> para <b>R$ {br(fim['custodia'], 1)} bi</b> "
              f"({pct(v_cus, 0, sinal=True)})" + (f", com quedas em {', '.join(map(str, quedas))}" if quedas else "")
              + ". É uma posição de fim de ano: os valores não se somam entre anos.")
    c.diagnostico([
        "Quedas em 2022 (−8%) e 2024 (−4%) acompanham anos de bolsa fraca: a custódia depende do preço dos ativos, "
        "não só de novos investidores.",
        f"Custódia por investidor caiu de R$ {br(cust_inv.iloc[0], 0)} mil para R$ {br(cust_inv.iloc[-1], 0)} mil: "
        "a base cresceu com investidores de carteira menor.",
        "2025 foi o maior valor da série (R$ 636,2 bi, +20%).",
    ])
    c.fonte([("Valor em custódia de pessoas físicas", "B3 — indicadores de pessoas físicas",
              "Posição no encerramento de cada ano, R$ bilhões")],
            nota="Valores digitados a partir da publicação da B3.")

    # ---------------------------------------------------------------- 3. Emissões
    c.cabecalho_secao("🏢 Emissões de dívida corporativa",
                      "O mercado de capitais virou canal relevante de financiamento das empresas",
                      "As empresas emitem títulos de dívida para captar recursos. O indicador mostra o volume anual "
                      "de emissões públicas divulgado pela B3.")
    if df["emissoes"].notna().any():
        fig, d = _fig_serie(df, "emissoes", "Emissões", "Emissões de dívida corporativa", "barra", "R$ bilhões",
                            lambda v: f"R$ {br(v, 1)} bi")
        c.mostrar_grafico(fig, key="cam_emi")
        if len(d) > 1:
            ritmo = (f"; o crescimento desacelerou de {pct(d['yoy'].iloc[1], 0, sinal=True)} para "
                     f"{pct(d['yoy'].iloc[-1], 1, sinal=True)}" if len(d) > 2
                     else f" ({pct(d['yoy'].iloc[-1], 1, sinal=True)})")
            c.leitura(f"As emissões foram de <b>R$ {br(d['emissoes'].iloc[0], 1)} bi</b> ({int(d['ano'].iloc[0])}) para "
                      f"<b>R$ {br(d['emissoes'].iloc[-1], 1)} bi</b> ({int(d['ano'].iloc[-1])}){ritmo}.")
    else:
        st.info("A série de emissões começa em 2023. Amplie a janela para vê-la.")
    c.diagnostico([
        "Recorde em 2025 (R$ 647,5 bi), mas o crescimento caiu de +76% (2024) para +6,5% (2025).",
        "A série só vai de 2023 a 2025: 2020–2022 ficaram fora para não misturar definições diferentes.",
    ])
    c.fonte([("Emissões públicas de dívida corporativa", "B3 — boletim de emissões", "Volume anual, R$ bilhões")],
            nota="Valores digitados a partir da publicação da B3.")

    # ---------------------------------------------------------------- 4. Composição
    c.cabecalho_secao("📑 Composição por instrumento financeiro",
                      "Debêntures dominam; CRI recuou em 2025",
                      "Principais instrumentos das emissões públicas de dívida corporativa em 2024 e 2025.")
    comp = COMPOSICAO.pivot(index="instrumento", columns="ano", values="valor").reindex(
        ["Debêntures", "CRI", "CRA", "Notas comerciais"])
    comp["var"] = comp[2025] / comp[2024] - 1
    niveis = [c.nivel_por_variacao(v) for v in comp["var"]]
    fig = go.Figure()
    fig.add_bar(x=comp.index, y=comp[2024], name="2024", marker_color=c.CINZA_CLARO,
                text=[f"R$ {br(v, 1)}" for v in comp[2024]], textposition="outside",
                hovertext=[f"<b>{i} · 2024</b><br>R$ {br(v, 1)} bi" + c.dica(TERMO_INSTR[i]) for i, v in comp[2024].items()],
                hoverinfo="text")
    fig.add_bar(x=comp.index, y=comp[2025], name="2025 (cor = oportunidade)", marker_color=[c.cor_oport(n) for n in niveis],
                text=[f"R$ {br(v, 1)}" for v in comp[2025]], textposition="outside",
                hovertext=[f"<b>{i} · 2025</b><br>R$ {br(v, 1)} bi · {pct(vr, 1, sinal=True)} vs 2024"
                           f"<br>Oportunidade: {n}" + c.dica(TERMO_INSTR[i])
                           for (i, v), vr, n in zip(comp[2025].items(), comp["var"], niveis)],
                hoverinfo="text")
    fig.update_layout(barmode="group")
    c.layout_base(fig, altura=460, y_titulo="R$ bilhões")
    fig.update_yaxes(range=[0, comp[[2024, 2025]].max().max() * 1.15])
    c.mostrar_grafico(fig, key="cam_comp")
    soma24, soma25 = comp[2024].sum(), comp[2025].sum()
    c.leitura(f"Debêntures são {pct(comp.loc['Debêntures', 2025] / soma25, 0)} dos quatro instrumentos em 2025. "
              f"CRI caiu {pct(-comp.loc['CRI', 'var'], 1)}; notas comerciais cresceram "
              f"{pct(comp.loc['Notas comerciais', 'var'], 1)}.")
    c.diagnostico([
        "Debêntures concentram a captação (R$ 496,3 bi em 2025, +6,5%).",
        "CRI recuou de R$ 57,5 bi para R$ 50,8 bi (−11,7%): oportunidade no financiamento imobiliário.",
        "Notas comerciais (+22,7%) e CRA (+12,7%) ganham espaço como alternativas.",
        f"**Destaque de coerência (sem corrigir dados):** em 2024, os quatro instrumentos somam "
        f"R$ {br(soma24, 1)} bi, contra R$ 608,1 bi de total no gráfico de emissões (diferença de "
        f"R$ {br(608.1 - soma24, 1)} bi). Em 2025 a soma (R$ {br(soma25, 1)} bi) bate com o total "
        "(R$ 647,5 bi). Vale conferir a série de 2024 na publicação da B3.",
    ])
    c.fonte([("Emissões por instrumento", "B3 — boletim de emissões", "2024 e 2025, R$ bilhões")],
            nota="Os valores por categoria podem não totalizar o total anual por "
                 "arredondamentos ou diferenças de apresentação.")

    # ---------------------------------------------------------------- IPOs, crédito imobiliário/agro e bancos
    camila_mercado.render(janela, ABA, df[["ano", "emissoes"]])

    # ---------------------------------------------------------------- 5. Tabela
    with st.expander("🔍 Tabela geral (dados da aba)"):
        tabela = df.rename(columns={"ano": "Ano", "investidores": "Investidores (milhões)",
                                    "custodia": "Custódia (R$ bilhões)",
                                    "emissoes": "Emissões corporativas (R$ bilhões)"})
        st.dataframe(tabela, hide_index=True, width="stretch")
        st.download_button("⬇️ Baixar CSV", tabela.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           "b3_desenvolvimento_mercado.csv", "text/csv", key="cam_csv")

    # ---------------------------------------------------------------- 6. Impacto e ODS
    c.cabecalho_secao("🌍 Impacto econômico e relação com os ODS")
    o1, o2 = st.columns(2)
    with o1:
        st.markdown("#### 📈 ODS 8")
        st.markdown("**Trabalho decente e crescimento econômico.** O mercado de capitais oferece às empresas "
                    "alternativas para captar recursos e financiar suas atividades; as emissões medem a força "
                    "desse canal.")
    with o2:
        st.markdown("#### 🏗️ ODS 9")
        st.markdown("**Indústria, inovação e infraestrutura.** Os recursos captados podem financiar projetos, "
                    "infraestrutura e inovação. Para comprovar resultados, é preciso dado sobre o destino dos "
                    "recursos.")
    c.diagnostico([
        "**ODS 8:** sem IPOs desde 2021, o financiamento das empresas passou a vir de dívida (debêntures, notas "
        "comerciais) e de títulos bancários; a retomada de IPOs ampliaria o capital de longo prazo para crescer e "
        "gerar emprego.",
        "**ODS 9:** LCI e CRI financiam moradia e construção; LCA e CRA financiam a produção agrícola. A B3 é a "
        "infraestrutura onde esses recursos são registrados.",
        "**Bancos:** os grandes bancos listados (Itaú, BTG, Bradesco, BB, Santander) são o canal pelo qual a poupança "
        "das famílias vira crédito; seus resultados acompanham juros e inadimplência do país.",
        "As emissões recordes reforçam o papel da B3 no financiamento das empresas (ODS 8).",
        "Falta dado de destinação dos recursos para medir o impacto em infraestrutura e inovação (ODS 9).",
    ], titulo="🔍 Diagnóstico ODS")

    # ---------------------------------------------------------------- Oportunidades
    a_cri = comp.loc["CRI", "var"]
    c.oportunidade(janela, ABA, "Alto" if yoy_inv is not None and yoy_inv < 0.05 else "Médio",
                   "Base de investidores estagnada",
                   f"A base cresceu {pct(yoy_inv, 1, sinal=True)} no último ano e cerca de 3% ao ano desde 2022, "
                   "depois do salto de 2020–2021.",
                   "Ampliar educação financeira e produtos de entrada para trazer novos CPFs à renda variável.",
                   f"{br(fim['investidores'], 1)} mi de investidores")
    c.oportunidade(janela, ABA, "Alto" if a_cri < 0 else "Médio", "Queda das emissões de CRI",
                   f"CRI recuou {pct(-a_cri, 1)} em 2025, enquanto debêntures e notas comerciais cresceram.",
                   "Estimular o financiamento imobiliário via mercado de capitais (produtos e liquidez de CRI).",
                   "R$ 50,8 bi em 2025")
    c.oportunidade(janela, ABA, "Médio", "Desaceleração das emissões",
                   "As emissões bateram recorde, mas cresceram só 6,5% em 2025 contra 76% em 2024.",
                   "Diversificar emissores (médias empresas, notas comerciais) para manter o ritmo de captação.",
                   "R$ 647,5 bi em 2025")
    c.oportunidade(janela, ABA, "Médio", "Medição de impacto nos ODS",
                   "Não há dado de destinação dos recursos captados para comprovar efeito em infraestrutura e inovação.",
                   "Divulgar a destinação das emissões (ex.: títulos verdes, infraestrutura) para medir o ODS 9.")
    c.oportunidade(janela, ABA, "Forte", "Custódia em recorde",
                   "A custódia de pessoas físicas chegou a R$ 636,2 bi em 2025 (+20%).",
                   "Manter: a base existente investe mais; foco em engajamento e diversificação de produtos.")
    c.bloco_oportunidades(janela, ABA)
