"""Aba da Camila · seções de mercado de capitais: IPOs, CRI/CRA, LCI/LCA e bancos listados.

Dados públicos digitados a partir das fontes citadas em cada bloco (B3, levantamentos de mercado e Banco Central).
Onde a fonte não publica o número, a célula fica vazia: nada é estimado.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import comum as c
from utils.comum import br, pct

# IPOs na B3 (ofertas iniciais) e Selic meta no fim do ano (% a.a.)
IPOS = pd.DataFrame({
    "ano": [2020, 2021, 2022, 2023, 2024, 2025],
    "ipos": [28, 46, 0, 0, 0, 0],
    "selic": [2.00, 9.25, 13.75, 11.75, 12.25, 15.00],
})
URL_IPO = "https://acionista.com.br/ipos-na-b3-historico-e-desempenho-das-acoes-do-boom-de-2020-e-2021/"
URL_IPO_2025 = "https://bpmoney.com.br/?p=395752"
URL_FOLLOW = "https://renovainvest.com.br/blog/follow-on-conheca-a-oferta-publica-subsequente-ao-ipo/"
URL_SELIC = "https://www.bcb.gov.br/controleinflacao/historicotaxasjuros"

# Estoque registrado na B3 (R$ bi). 2024 não foi publicado por produto na fonte consultada.
CAPTACAO = pd.DataFrame({
    "data": ["dez/2023", "dez/2025", "jun/2026"],
    "LCI": [360.5, 508.8, 544.0],
    "LCA": [458.9, 599.9, 563.0],
})
OUTROS_BANCARIOS = {"CDB": (2800.0, "dez/2025"), "Letras Financeiras (LF)": (976.8, "dez/2025")}
URL_CAPT_23 = "https://investidor10.com.br/noticias/lcis-fecharam-2023-com-r-4-5-trilhoes-aponta-b3-101362/"
URL_CAPT_25 = ("https://borainvestir.b3.com.br/tipos-de-investimentos/renda-fixa/cdb/"
               "cdb-lci-lca-e-lf-estoque-de-produtos-de-captacao-bancaria-na-b3-cresceu-17-em-2025/")
URL_CAPT_26 = "https://forbes.com.br/forbes-money/2026/07/renda-fixa-bancaria-b3/"

# Bancos listados: valor de mercado em 23/06/2026 (R$ bi)
BANCOS = pd.DataFrame({
    "banco": ["Itaú Unibanco", "BTG Pactual", "Bradesco", "Banco do Brasil", "Santander Brasil"],
    "ticker": ["ITUB4", "BPAC11", "BBDC4", "BBAS3", "SANB11"],
    "valor": [370.9, 209.7, 162.2, 120.4, 108.4],
    "perfil": ["Maior banco privado; varejo de massa, alta renda e atacado",
               "Banco de investimento; mercado de capitais e gestão de patrimônio",
               "Varejo de massa e seguros; grande presença fora dos grandes centros",
               "Controle público; maior financiador do agronegócio (LCA, crédito rural)",
               "Subsidiária do grupo espanhol; varejo e crédito ao consumo"],
})
OUTROS_BANCOS = ("Banrisul (BRSR6), ABC Brasil (ABCB4), Banco Pan (BPAN4), BRB (BSLI4), Banco da Amazônia (BAZA3), "
                 "Banestes (BEES3), Banco Mercantil (BMEB4); e, via BDR, Nubank (ROXO34) e Inter (INBR32).")
URL_BANCOS = ("https://investidor10.com.br/noticias/"
              "ranking-dos-maiores-bancos-em-valor-de-mercado-muda-em-2025-veja-quem-subiu-113770/")
URL_BANCOS_2025 = ("https://monitordomercado.com.br/noticias/"
                   "339774-bancos-lideram-ganhos-na-bolsa-em-2025-btg-pactual-cresce-r-150-bi/")


def render(janela, aba, emissoes):
    """emissoes: DataFrame ano/emissoes (R$ bi) da aba da Camila, para ligar IPO e dívida."""
    # ---------------------------------------------------------------- IPOs
    c.cabecalho_secao("🚀 IPOs: por que as empresas abriram, e pararam de abrir, capital",
                      "Com juros de 2%, a bolsa virou a porta de entrada do financiamento; com juros acima de 10%, "
                      "as empresas trocaram ações por dívida",
                      "IPO (oferta pública inicial) é quando uma empresa vende ações na bolsa pela primeira vez para "
                      "captar recursos de longo prazo, sem dívida.")
    d = IPOS[(IPOS["ano"] >= janela.ano_ini) & (IPOS["ano"] <= janela.ano_ref)]
    if d.empty:
        st.info("A série de IPOs vai de 2020 a 2025. Amplie a janela.")
    else:
        x = d["ano"].astype(str)
        niv = ["Alto" if v == 0 else "Forte" for v in d["ipos"]]
        fig = go.Figure()
        fig.add_bar(x=x, y=d["ipos"], name="IPOs no ano", marker_color=[c.cor_oport(n) for n in niv],
                    text=[str(v) for v in d["ipos"]], textposition="outside", cliponaxis=False,
                    hovertext=[f"<b>{a}</b><br>{v} IPOs<br>Oportunidade: {n}" + c.dica("IPO")
                               for a, v, n in zip(d["ano"], d["ipos"], niv)], hoverinfo="text")
        fig.add_scatter(x=x, y=d["selic"], name="Selic no fim do ano (% a.a., eixo direito)", yaxis="y2",
                        mode="lines+markers+text", text=[f"{br(v, 2)}%" for v in d["selic"]],
                        textposition="top center", line=dict(color=c.CINZA_ESCURO, width=2, dash="dot"),
                        hovertext=[f"<b>Selic {a}</b><br>{br(v, 2)}% a.a." + c.dica("Selic")
                                   for a, v in zip(d["ano"], d["selic"])], hoverinfo="text")
        c.layout_base(fig, "IPOs na B3 x taxa Selic", altura=440, y_titulo="Quantidade de IPOs")
        fig.update_layout(yaxis2=dict(title="Selic (% a.a.)", overlaying="y", side="right", showgrid=False,
                                      range=[0, 20], ticksuffix="%"))
        fig.update_layout(yaxis=dict(range=[0, max(d["ipos"].max(), 1) * 1.25]))
        fig.update_xaxes(type="category")
        c.mostrar_grafico(fig, key="cam_ipo")
        c.legenda_oportunidade(("Alto", "Forte"))
        c.leitura(f"Foram <b>{int(d['ipos'].sum())} IPOs</b> na janela, todos em 2020–2021, quando a Selic estava "
                  "no menor nível da história. Desde 2022, com a Selic acima de 10%, não houve nenhuma nova empresa "
                  "na bolsa.")
    c.diagnostico([
        "**O que levou ao boom (2020–2021):** Selic de 2% tornou a renda fixa pouco atraente e levou milhões de pessoas "
        "físicas à bolsa (a base de investidores foi de 2,7 para 4,2 milhões em 2021). Com demanda alta por ações, "
        "empresas de varejo, tecnologia, saúde e agro abriram capital para financiar expansão e reduzir dívida.",
        "**O que interrompeu (2022–2025):** a Selic subiu para 13,75% em 2022 e chegou a 15% em 2025. Com renda fixa "
        "pagando mais, o investidor saiu de ações, os preços caíram e abrir capital ficou caro. Os últimos IPOs foram em "
        "agosto de 2021 (Raízen, Vittia, Oncoclínicas).",
        "**Para onde foi o financiamento:** as empresas passaram a captar por dívida. As emissões de debêntures, CRI, CRA "
        "e notas comerciais bateram recorde (seção acima), e as já listadas fizeram ofertas subsequentes (follow-ons), "
        "como as cerca de 9 de 2025 (R$ 15,5 bi).",
        "**Destaque de coerência:** as fontes contam IPOs de formas diferentes (com ou sem ofertas secundárias); usamos "
        "a série que separa só as estreias. 2026 é apontado pela B3 como o ano provável da retomada.",
    ])
    c.fonte([("IPOs por ano (2020–2024)", f"[Acionista / Quantum Finance]({URL_IPO})", "Somente estreias na B3"),
             ("Ausência de IPOs em 2025", f"[BP Money, dez/2025]({URL_IPO_2025})", "Seca desde ago/2021"),
             ("Follow-ons 2025", f"[Renova Invest]({URL_FOLLOW})", "9 ofertas, R$ 15,5 bi"),
             ("Selic meta no fim do ano", f"[Banco Central, histórico do Copom]({URL_SELIC})", "% a.a.")],
            nota="Valores digitados a partir das fontes; o número de IPOs varia conforme a metodologia de cada fonte.")

    # ---------------------------------------------------------------- CRI/CRA x LCI/LCA
    c.cabecalho_secao("🏠🌾 Crédito imobiliário e do agro: CRI e CRA no mercado, LCI e LCA nos bancos",
                      "O financiamento imobiliário e do agronegócio passa pela B3 por dois caminhos",
                      "**CRI e CRA** são títulos de empresas (securitizadoras), lastreados em recebíveis imobiliários ou do "
                      "agro e vendidos no mercado de capitais. **LCI e LCA** são títulos emitidos por bancos com o mesmo "
                      "tipo de lastro e ficam registrados na B3. Os quatro são isentos de IR para pessoa física, por isso "
                      "atraem o investidor.")
    cap = CAPTACAO.copy()
    fig = go.Figure()
    for col, cor_base in (("LCI", c.AZUL), ("LCA", c.VERDE)):
        var = cap[col] / cap[col].shift(1) - 1
        niv = [c.nivel_por_variacao(v) if pd.notna(v) else "Baixo" for v in var]
        fig.add_bar(x=cap["data"], y=cap[col], name=f"{col} (borda = produto; cor = variação)",
                    marker=dict(color=[c.cor_oport(n) for n in niv], line=dict(color=cor_base, width=3)),
                    text=[f"R$ {br(v, 1)} bi" for v in cap[col]], textposition="outside", cliponaxis=False,
                    hovertext=[f"<b>{col} · {dt}</b><br>Estoque R$ {br(v, 1)} bi"
                               + (f"<br>Variação: {pct(vr, 1, sinal=True)}" if pd.notna(vr) else "")
                               + f"<br>Oportunidade: {n}" + c.dica(col)
                               for dt, v, vr, n in zip(cap["data"], cap[col], var, niv)], hoverinfo="text")
    fig.update_layout(barmode="group")
    c.layout_base(fig, "Estoque de LCI e LCA registrado na B3 (R$ bi)", altura=430, y_titulo="R$ bilhões")
    fig.update_yaxes(range=[0, cap[["LCI", "LCA"]].max().max() * 1.18])
    fig.update_xaxes(type="category")
    c.mostrar_grafico(fig, key="cam_lci")
    c.leitura(f"A LCI foi de R$ {br(cap['LCI'].iloc[0], 1)} bi (dez/23) para <b>R$ {br(cap['LCI'].iloc[-1], 1)} bi</b> "
              f"(jun/26). A LCA cresceu até dez/25 e recuou para <b>R$ {br(cap['LCA'].iloc[-1], 1)} bi</b> em jun/26 "
              f"({pct(cap['LCA'].iloc[-1] / cap['LCA'].iloc[-2] - 1, 1, sinal=True)}). Para comparar: CDB R$ 2,8 tri e "
              "LF R$ 976,8 bi (dez/25).")
    k = st.columns(4)
    k[0].metric("LCI (jun/2026)", f"R$ {br(cap['LCI'].iloc[-1], 0)} bi", help=c.explica("LCI"))
    k[1].metric("LCA (jun/2026)", f"R$ {br(cap['LCA'].iloc[-1], 0)} bi",
                f"{pct(cap['LCA'].iloc[-1] / cap['LCA'].iloc[-2] - 1, 1, sinal=True)} vs dez/2025", help=c.explica("LCA"))
    k[2].metric("CDB (dez/2025)", "R$ 2,8 tri", help=c.explica("CDB"))
    k[3].metric("Letras Financeiras (dez/2025)", f"R$ {br(976.8, 1)} bi", help=c.explica("Letra Financeira"))
    c.diagnostico([
        "**Imobiliário:** a LCI cresce forte (+29% em 2025), puxada pela isenção de IR e pela demanda por crédito "
        "habitacional. Já o CRI recuou 11,7% em 2025 (seção de composição): o investidor migrou do título de mercado "
        "para o título bancário, mais simples e com garantia do FGC.",
        "**Agro:** a LCA cresceu até 2025 e caiu 4% no 1º semestre de 2026. Segundo a B3, é acomodação após anos de "
        "expansão, mudanças regulatórias e a concorrência de CPR e CRA, que cresceu 12,7% em 2025.",
        "**Regulação:** em 2024 o CMN restringiu os lastros aceitos em CRI, CRA, LCI e LCA, e em 2025 reduziu o prazo "
        "mínimo das letras de 9 para 6 meses. Regras mudam o fluxo entre os produtos.",
        "**Leitura econômica (ODS 8 e 9):** esses títulos levam poupança das famílias para moradia e produção agrícola. A "
        "B3 registra os dois lados, então ganha com o volume, qualquer que seja o caminho escolhido.",
    ])
    c.fonte([("Estoque LCI e LCA dez/2023", f"[B3 via Investidor10]({URL_CAPT_23})", "R$ bi"),
             ("Estoque LCI, LCA, CDB e LF dez/2025", f"[B3 · Bora Investir]({URL_CAPT_25})", "R$ bi"),
             ("Estoque LCI e LCA jun/2026", f"[Forbes, com dados da B3]({URL_CAPT_26})", "R$ bi"),
             ("CRI e CRA (emissões)", "Seção de composição desta aba", "R$ bi")],
            nota="Dez/2024 não foi publicado por produto nas fontes consultadas; fica fora do gráfico em vez de estimado.")

    # ---------------------------------------------------------------- Bancos
    c.cabecalho_secao("🏦 Bancos de capital aberto na B3",
                      "Os bancos são, ao mesmo tempo, grandes empresas listadas e os maiores emissores de títulos "
                      "registrados na B3",
                      "Bancos listados captam com CDB, LCI, LCA e LF (registrados na B3), emprestam para famílias e "
                      "empresas e têm ações entre as mais negociadas da bolsa. O desempenho deles reflete juros, crédito e "
                      "inadimplência da economia.")
    b = BANCOS.sort_values("valor")
    fig = go.Figure(go.Bar(
        y=b["banco"] + " (" + b["ticker"] + ")", x=b["valor"], orientation="h", marker_color=c.AZUL,
        text=[f"R$ {br(v, 1)} bi" for v in b["valor"]], textposition="outside", cliponaxis=False,
        hovertext=[f"<b>{n} ({t})</b><br>Valor de mercado: R$ {br(v, 1)} bi<br>{p}" + c.dica("Valor de mercado")
                   for n, t, v, p in zip(b["banco"], b["ticker"], b["valor"], b["perfil"])], hoverinfo="text"))
    c.layout_base(fig, "Maiores bancos listados por valor de mercado (23/06/2026)", altura=360, legenda=False)
    fig.update_xaxes(title_text="R$ bilhões", range=[0, b["valor"].max() * 1.2])
    fig.update_yaxes(type="category")
    c.mostrar_grafico(fig, key="cam_bancos")
    soma = BANCOS["valor"].sum()
    c.leitura(f"Os cinco maiores bancos listados valem juntos cerca de <b>R$ {br(soma, 0)} bi</b>; o Itaú sozinho "
              f"responde por {pct(BANCOS['valor'].iloc[0] / soma, 0)} desse total.")
    st.markdown(c.md(f"**Outros bancos listados:** {OUTROS_BANCOS}"))
    c.diagnostico([
        "**Itaú Unibanco:** maior banco privado e o mais valioso da bolsa; atende do varejo de massa ao atacado, então "
        "seu resultado acompanha o crédito e o consumo de boa parte da população.",
        "**BTG Pactual:** foi o banco que mais ganhou valor em 2025 (+R$ 150 bi) e passou o Bradesco em 2026, puxado por "
        "mercado de capitais e gestão de recursos, atividades que também geram receita para a B3.",
        "**Banco do Brasil:** exceção em 2025 (−R$ 12,8 bi em valor de mercado), pressionado pela inadimplência do "
        "agronegócio, ligado diretamente à LCA e ao crédito rural.",
        "**Por que importa para a B3:** bancos emitem a maior parte do estoque de renda fixa bancária registrado na B3 "
        "(CDB, LCI, LCA e LF somavam R$ 4,9 tri em dez/2025) e suas ações estão entre as mais negociadas, o que "
        "alimenta as receitas de renda fixa e de renda variável da B3 (aba do Enzo).",
    ])
    c.fonte([("Valor de mercado dos bancos (23/06/2026)", f"[Investidor10]({URL_BANCOS})", "R$ bi"),
             ("Variação de valor em 2025", f"[Monitor do Mercado / Elos Ayta]({URL_BANCOS_2025})", "R$ bi"),
             ("Estoque de renda fixa bancária", f"[B3 · Bora Investir]({URL_CAPT_25})", "dez/2025")],
            nota="Valor de mercado muda todo dia; os números são uma foto da data indicada.")

    # ---------------------------------------------------------------- Oportunidades
    c.oportunidade(janela, aba, "Alto", "Seca de IPOs desde 2021",
                   "Nenhuma nova empresa abriu capital de 2022 a 2025, com a Selic acima de 10%.",
                   "Preparar a retomada: produtos para empresas médias, listagem simplificada e atração de investidores "
                   "quando os juros caírem.", "46 IPOs em 2021 → 0 em 2025")
    c.oportunidade(janela, aba, "Médio", "LCA em queda e CRI em recuo",
                   "A LCA caiu 4% no 1º semestre de 2026 e o CRI recuou 11,7% em 2025, enquanto a LCI cresce.",
                   "Acompanhar o efeito das regras do CMN e reforçar CRA/CPR como alternativas de financiamento do agro.",
                   f"LCA R$ {br(CAPTACAO['LCA'].iloc[-1], 0)} bi")
    c.oportunidade(janela, aba, "Forte", "Renda fixa bancária em alta",
                   "O estoque de CDB, LCI, LCA e LF registrado na B3 chegou a R$ 4,9 tri em dez/2025 (+17%).",
                   "Manter: é receita recorrente de registro para a B3, menos sensível ao ciclo de ações.")
