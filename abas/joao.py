"""Aba 3 · João — Eficiência Operacional, Custos e Lucratividade.

Mantém a ponte de resultado clicável, os gráficos complementares, a DRE gerencial e o critério de
potencial de oportunidade do João. Mudança combinada com o grupo: os valores ilustrativos e a abertura
de custos de exemplo foram trocados pelas linhas oficiais da DRE da B3 (IS New Seg, 2T26).
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import comum as c
from utils import dre
from utils.comum import br, pct

ABA = "Eficiência & Lucratividade"
COR_TOTAL, COR_QUEDA, COR_GANHO = "#1f77b4", "#d62728", "#2ca02c"
NOMES_DRILL = {"ded": "Deduções e impostos", "desp": "Despesas operacionais", "bx": "D&A, financeiro e IR"}


def mi(v_mil, casas=1):
    """Formato do João: R$ mi, ou R$ bi acima de mil milhões. Entrada em R$ mil."""
    v = v_mil / 1e3
    if abs(v) >= 1000:
        return f"R$ {br(v / 1000, 2)} bi"
    return f"R$ {br(v, casas)} mi"


def modelo(r):
    """Modelo de resultado a partir das linhas oficiais (r: Series de um ano ou soma de anos, R$ mil)."""
    m = dict(
        receita_bruta=r["receita_total"], deducoes=-r["deducoes"], receita_liquida=r["receita_liquida"],
        despesas=-(r["despesas"] - r["da"]), ebitda=r["ebitda"], ebitda_rec=r["ebitda_recorrente"],
        da=-r["da"], resultado_operacional=r["resultado_operacional"],
        outros_op=r["impairment"] + r["equivalencia"] + r["descontinuidade_eq"] + r["alienacao_coligadas"],
        financeiro=r["resultado_financeiro"], ir=-r["ir"], ir_corrente=-r["ir_corrente"],
        ir_diferido=-r["ir_diferido"], lucro=r["lucro"], lucro_rec=r["lucro_recorrente"], lair=r["lair"],
    )
    m["ajustes"] = m["ebitda_rec"] - m["ebitda"]
    m["bx_total"] = m["ebitda"] - m["lucro"]
    m["margem_ebitda"] = m["ebitda_rec"] / m["receita_liquida"]
    m["margem_oper"] = m["resultado_operacional"] / m["receita_liquida"]
    m["margem_liq"] = m["lucro"] / m["receita_liquida"]
    m["aliquota_efetiva"] = m["ir"] / m["lair"]
    m["det"] = {
        "ded": [(nome, -r[k], niv, mot) for k, nome, niv, mot in dre.DEDUCOES],
        "desp": [(nome, -r[k], niv, mot) for k, nome, niv, mot in dre.DESPESAS if abs(r[k]) > 0],
        # efeitos sobre a ponte (sinal: + soma ao lucro, − reduz)
        "bx": [
            ("Depreciação e amortização", -m["da"], "Nulo", "Efeito contábil: não sai dinheiro do caixa."),
            ("Impairment, equivalência e outros", m["outros_op"], "Baixo", "Eventos contábeis pontuais."),
            ("Resultado financeiro", m["financeiro"], "Forte" if m["financeiro"] >= 0 else "Médio",
             "Rendimento das aplicações menos juros das dívidas."),
            ("IR e CS corrente", -m["ir_corrente"], "Médio", "Imposto pago; o JCP reduz a base de cálculo."),
            ("IR e CS diferido", -m["ir_diferido"], "Nulo", "Imposto contábil, sem saída de caixa no ano."),
        ],
    }
    return m


def render(janela):
    st.markdown("## ⚙️ Eficiência Operacional, Custos e Lucratividade")
    st.caption("Auditoria de rentabilidade: da receita ao lucro, onde estão os custos e quais "
               "têm potencial de melhoria. Clique nas barras marcadas com ▸ para explorar os detalhes.")
    c.glossario("joao")
    c.aviso_parcial(janela)

    valores, _, _ = dre.carregar_dre()
    anos = janela.anos_fechados
    if not anos:
        st.warning("A janela escolhida não tem ano fechado (2020–2025).")
        return
    a = dre.anual(valores, range(2020, 2026))
    modelos = {ano: modelo(a.loc[ano]) for ano in a.index}

    # Seletor original do João: um ou mais anos (dentro da janela global); vários anos são somados.
    sel = sorted(st.multiselect(
        "📅 Anos de análise (selecione um ou mais)", anos, default=[anos[-1]], key=f"joao_anos_{anos[0]}_{anos[-1]}",
        help="Com vários anos, os valores são somados e as margens recalculadas. A variação compara com o período "
             "imediatamente anterior de mesma duração (só para anos seguidos)."))
    if not sel:
        sel = [anos[-1]]
        st.info(f"Nenhum ano selecionado; exibindo {anos[-1]}.")
    seguidos = sel[-1] - sel[0] + 1 == len(sel)

    def rotulo_periodo(lista):
        if len(lista) == 1:
            return str(lista[0])
        return f"{lista[0]}–{lista[-1]}" if lista[-1] - lista[0] + 1 == len(lista) else ", ".join(map(str, lista))

    rot = rotulo_periodo(sel)
    m = modelo(a.loc[sel].sum())
    prev = list(range(sel[0] - len(sel), sel[0]))
    mp = modelo(a.loc[prev].sum()) if seguidos and all(p in a.index for p in prev) else None
    rot_ant = rotulo_periodo(prev) if mp else None

    def d(k):
        return c.var(m[k], mp[k]) if mp else None

    def dpp(k):
        return m[k] - mp[k] if mp else None

    # ---------------------------------------------------------------- Indicadores-chave
    st.markdown(f"#### Indicadores-chave · {rot}")
    c.kpis([
        dict(rotulo="Receita bruta", valor=mi(m["receita_bruta"]), delta=c.delta_txt(d("receita_bruta"), rot_ant)),
        dict(rotulo="Receita líquida", valor=mi(m["receita_liquida"]), delta=c.delta_txt(d("receita_liquida"), rot_ant)),
        dict(rotulo="EBITDA recorrente", valor=mi(m["ebitda_rec"]), delta=c.delta_txt(d("ebitda_rec"), rot_ant)),
        dict(rotulo="Margem EBITDA recorrente", valor=pct(m["margem_ebitda"], 1),
             delta=c.delta_txt(dpp("margem_ebitda"), rot_ant, "p.p.")),
        dict(rotulo="Despesas operacionais", valor=mi(m["despesas"]), delta=c.delta_txt(d("despesas"), rot_ant),
             delta_color="inverse"),
        dict(rotulo="Lucro líquido recorrente", valor=mi(m["lucro_rec"]), delta=c.delta_txt(d("lucro_rec"), rot_ant)),
        dict(rotulo="Margem líquida", valor=pct(m["margem_liq"], 1), delta=c.delta_txt(dpp("margem_liq"), rot_ant, "p.p.")),
        dict(rotulo="EBITDA (reportado)", valor=mi(m["ebitda"]), delta=c.delta_txt(d("ebitda"), rot_ant), termo="EBITDA"),
    ], colunas=4)

    # ---------------------------------------------------------------- Painel de alertas
    dd, dr = d("despesas"), d("receita_liquida")
    gao = d("ebitda_rec") / dr if (mp and dr) else None
    peso_aj = abs(m["ajustes"]) / m["ebitda_rec"]
    alto = [(n, v) for n, v, p, _ in m["det"]["desp"] if p == "Alto"]
    soma_alto = sum(v for _, v in alto)
    alertas = [
        dict(nome="Despesas x receita", valor=f"{pct(dd, 1, sinal=True)} x {pct(dr, 1, sinal=True)}" if mp else "—",
             delta=f"despesas x receita líquida, vs {rot_ant}" if mp else "sem período anterior",
             status=("Alerta" if dd > dr else "Confortável") if mp else "Informativo",
             desc="Se as despesas crescem mais que a receita, a empresa perde eficiência.",
             regra="despesas ≤ receita Confortável · despesas > receita Alerta"),
        dict(nome="Alavancagem operacional", valor=f"{br(gao, 2)}x" if gao is not None else "—",
             delta="EBITDA cresce mais que a receita" if gao and gao > 1 else "sem ganho de escala" if gao else "",
             status=c.status_faixa(gao, 1.0, 0.0), desc=c.explica("Alavancagem operacional"),
             regra="≥ 1x Confortável · 0–1x Atenção · < 0 Alerta"),
        dict(nome="Margem EBITDA recorrente", valor=pct(m["margem_ebitda"], 1),
             delta=c.pp(dpp("margem_ebitda")) + f" vs {rot_ant}" if mp else "",
             status=c.status_faixa(dpp("margem_ebitda"), 0.0, -0.03), desc=c.explica("Margem EBITDA recorrente"),
             regra="variação ≥ 0 Confortável · até −3 p.p. Atenção · < −3 p.p. Alerta"),
        dict(nome="Ajustes não recorrentes", valor=pct(peso_aj, 1), delta=f"{mi(m['ajustes'])} (recorrente − reportado)",
             status=c.status_faixa(peso_aj, 0.03, 0.10, maior_melhor=False), desc=c.explica("Ajustes não recorrentes"),
             regra="≤ 3% do EBITDA Confortável · 3–10% Atenção · > 10% Alerta"),
        dict(nome="Itens de alto potencial", valor=mi(soma_alto),
             delta=f"{pct(soma_alto / m['despesas'], 0)} das despesas ({', '.join(n for n, _ in alto)})",
             status="Informativo", desc="Despesas com contratos renegociáveis (cor vermelha nos gráficos).",
             regra="informativo"),
        dict(nome="Alíquota efetiva de IR", valor=pct(m["aliquota_efetiva"], 1),
             delta=f"IR diferido: {mi(m['ir_diferido'])}", status="Informativo",
             desc="IR e CS ÷ lucro antes dos impostos. A alíquota nominal é 34%; o JCP reduz, ajustes de diferido aumentam.",
             regra="informativo"),
    ]
    c.painel_alertas(alertas, leitura=c.leitura_alertas(alertas[:4], rot), por_linha=3,
                     rodape="Regras definidas pelo grupo para leitura rápida; não são metas oficiais da B3.")

    # ---------------------------------------------------------------- Ponte de resultado
    c.cabecalho_secao(f"🌉 Ponte de resultado — {rot}",
                      "Da receita bruta ao lucro: clique em uma barra marcada com ▸ para abrir os componentes")
    st.caption("Passe o mouse sobre cada barra para ver, em palavras simples, o que ela significa.")
    ss = st.session_state
    ss.setdefault("joao_drill", None)
    ss.setdefault("joao_ver", 0)

    passos = []

    def total(r_, v):
        passos.append(dict(rotulo=r_, valor=v, tipo="total", cor=COR_TOTAL,
                           hover=f"<b>{r_}</b><br>{mi(v)}" + c.dica(r_.replace(" (reportado)", ""))))

    def queda(chave, efeito):
        """efeito com sinal sobre a ponte (negativo reduz)."""
        if ss["joao_drill"] == chave:
            ref = sum(abs(x[1]) for x in m["det"][chave])
            for nome, v, pot, motivo in m["det"][chave]:
                ef = v if chave == "bx" else -v
                passos.append(dict(rotulo=nome, valor=ef, tipo="passo", cor=c.cor_oport(pot),
                                   hover=f"<b>{nome}</b><br>{mi(abs(v))} ({br(abs(v) / ref * 100)}% de "
                                         f"{NOMES_DRILL[chave]})<br>Potencial de oportunidade: {pot}<br>{motivo}"
                                         + c.dica(nome)))
        else:
            passos.append(dict(rotulo=NOMES_DRILL[chave] + " ▸", valor=efeito, tipo="passo", cor=COR_QUEDA,
                               chave=chave, hover=f"<b>{NOMES_DRILL[chave]}</b><br>{mi(abs(efeito))}<br>"
                                                  "Clique para detalhar" + c.dica(
                                   {"ded": "Deduções da receita", "desp": "Despesas operacionais"}.get(chave, ""))))

    total("Receita bruta", m["receita_bruta"])
    queda("ded", -m["deducoes"])
    total("Receita líquida", m["receita_liquida"])
    queda("desp", -m["despesas"])
    total("EBITDA (reportado)", m["ebitda"])
    queda("bx", -m["bx_total"])
    total("Lucro líquido", m["lucro"])

    fig = c.cascata(passos, f"Ponte consolidada do resultado — {rot}"
                    + (f" · detalhando {NOMES_DRILL[ss['joao_drill']]}" if ss["joao_drill"] else ""),
                    altura=520, y_titulo="R$ bilhões", rotulos_caixa=True)
    fig.update_layout(clickmode="event+select")
    fig.update_traces(selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
                      selector=dict(type="bar"))
    if ss["joao_drill"]:
        if st.button("⬅️ Voltar à visão consolidada", type="primary", key="joao_voltar"):
            ss["joao_drill"] = None
            ss["joao_ver"] += 1
            st.rerun()
        c.legenda_oportunidade()
    evento = c.mostrar_grafico(fig, key=f"joao_ponte_{ss['joao_ver']}", on_select="rerun", selection_mode="points")
    pontos = (evento or {}).get("selection", {}).get("points", []) if evento else []
    if pontos and not ss["joao_drill"]:
        clicado = pontos[0].get("x")
        chave = next((p.get("chave") for p in passos if p["rotulo"] == clicado), None)
        if chave:
            ss["joao_drill"] = chave
            ss["joao_ver"] += 1
            st.rerun()
    maior = max(m["det"]["desp"], key=lambda x: x[1])
    c.leitura(f"Em {rot}, de cada R$ 100 de receita bruta, R$ {br(m['deducoes'] / m['receita_bruta'] * 100)} vão para "
              f"impostos sobre o faturamento, R$ {br(m['despesas'] / m['receita_bruta'] * 100)} para despesas e sobram "
              f"<b>R$ {br(m['lucro'] / m['receita_bruta'] * 100)}</b> de lucro. O maior custo é {maior[0].lower()} "
              f"({mi(maior[1])}).")
    c.diagnostico([
        f"**Maior item de custo:** {maior[0]} ({mi(maior[1])}, {pct(maior[1] / m['despesas'], 1)} das despesas sem D&A).",
        f"**Alavancas de alto potencial:** {', '.join(n for n, _ in alto)}, somando {mi(soma_alto)}. Uma redução de 10% "
        f"liberaria cerca de {mi(soma_alto * 0.10)} de EBITDA.",
        (f"🔴 **Alerta:** despesas cresceram {pct(dd, 1)} contra {pct(dr, 1)} da receita líquida (perda de eficiência)."
         if mp and dd > dr else
         f"🟢 Despesas cresceram {pct(dd, 1)} contra {pct(dr, 1)} da receita líquida (ganho de escala)." if mp else
         "Sem período anterior para comparar despesas e receita."),
        f"{'🟡' if peso_aj > 0.03 else '🟢'} Ajustes não recorrentes equivalem a {pct(peso_aj, 1)} do EBITDA recorrente.",
        f"Alíquota efetiva de IR de {pct(m['aliquota_efetiva'], 1)}; o IR diferido ({mi(m['ir_diferido'])}) não sai do "
        "caixa no período.",
    ])
    c.fonte([("Receita bruta, deduções, receita líquida", "Planilha B3 · IS (New Seg)", "Linhas 4, 22–24 e 25"),
             ("Despesas por natureza", "Planilha B3 · IS (New Seg)", "Linhas 26–38 (D&A na linha 29)"),
             ("EBITDA e EBITDA recorrente", "Planilha B3 · IS (New Seg)", "Linhas 66 e 79 (ajustes 67–78)"),
             ("Impairment, equivalência, financeiro", "Planilha B3 · IS (New Seg)", "Linhas 41–45"),
             ("IR (corrente e diferido), lucro", "Planilha B3 · IS (New Seg)", "Linhas 51–53 e 56; recorrente 121")],
            nota="O potencial de oportunidade (Alto/Médio/Baixo/Nulo) é o critério da aba aplicado às linhas reais. "
                 "Validação ao carregar: as linhas 27–38 somam as despesas e a ponte fecha com o lucro em todos os anos.")

    # ---------------------------------------------------------------- Análises complementares
    c.cabecalho_secao("📈 Análises complementares")
    c.legenda_oportunidade()
    sub = st.tabs(["EBITDA", "Estrutura de custos", "Margens", "Pareto de custos", "Mapa hierárquico", "Variação"])
    anos_graf = sel if len(sel) > 1 else anos  # como no original: anos escolhidos, ou a janela toda
    anos_txt = [str(x) for x in anos_graf]
    base_custos = [(n, v, p) for n, v, p, _ in m["det"]["desp"]] + [("Depreciação e amortização", m["da"], "Nulo")]

    with sub[0]:
        fig = go.Figure()
        fig.add_bar(name="EBITDA reportado", x=anos_txt, y=[modelos[x]["ebitda"] / 1e3 for x in anos_graf],
                    marker_color="#6c8ebf", text=[br(modelos[x]["ebitda"] / 1e3, 0) for x in anos_graf], textposition="outside",
                    hovertext=[f"<b>EBITDA reportado · {x}</b><br>{mi(modelos[x]['ebitda'])}" + c.dica("EBITDA") for x in anos_graf],
                    hoverinfo="text")
        fig.add_bar(name="EBITDA recorrente", x=anos_txt, y=[modelos[x]["ebitda_rec"] / 1e3 for x in anos_graf],
                    marker_color=COR_TOTAL, text=[br(modelos[x]["ebitda_rec"] / 1e3, 0) for x in anos_graf],
                    textposition="outside",
                    hovertext=[f"<b>EBITDA recorrente · {x}</b><br>{mi(modelos[x]['ebitda_rec'])}<br>Ajustes: "
                               f"{mi(modelos[x]['ajustes'])}" + c.dica("EBITDA recorrente") for x in anos_graf],
                    hoverinfo="text")
        fig.update_layout(barmode="group")
        c.layout_base(fig, "EBITDA reportado vs. recorrente (R$ milhões)", altura=460, y_titulo="R$ milhões")
        fig.update_xaxes(type="category")
        c.mostrar_grafico(fig, key="joao_ebitda")
        st.caption("A diferença entre as barras são os ajustes não recorrentes (reversões de provisões, M&A, rescisões).")

    with sub[1]:
        g1, g2 = st.columns([3, 2])
        with g1:
            fig = go.Figure(go.Pie(
                labels=[n for n, _, _ in base_custos], values=[v / 1e3 for _, v, _ in base_custos], hole=0.5,
                marker=dict(colors=[c.cor_oport(p) for _, _, p in base_custos], line=dict(color="white", width=1)),
                texttemplate="%{label}<br>R$ %{value:,.0f} mi<br>%{percent}", textposition="outside",
                customdata=[f"Potencial: {p}" + c.dica(n) for n, _, p in base_custos],
                hovertemplate="%{label}<br>R$ %{value:,.1f} mi (%{percent})<br>%{customdata}<extra></extra>", sort=False))
            c.layout_base(fig, f"Estrutura de custos — {rot}", altura=500, legenda=False)
            ev = c.mostrar_grafico(fig, key="joao_rosca", on_select="rerun", selection_mode="points")
        with g2:
            st.markdown("##### 🔍 Detalhe da fatia")
            pts = (ev or {}).get("selection", {}).get("points", []) if ev else []
            if pts:
                idx = pts[0].get("point_index", pts[0].get("point_number"))
                if idx is None:
                    idx = next((i for i, (n, _, _) in enumerate(base_custos) if n == pts[0].get("label")), 0)
                nome, val, pot = base_custos[int(idx)]
                st.metric(nome, mi(val), f"{pct(val / m['receita_liquida'], 1)} da receita líquida · potencial: {pot}",
                          delta_color="off", help=c.explica(nome) or None)
                motivo = next((mt for n, _, _, mt in m["det"]["desp"] if n == nome), c.explica(nome))
                st.markdown(f"{c.OPORT_EMOJI[pot]} **{pot}:** {motivo}")
            else:
                st.info("Clique em uma fatia da rosca para ver o peso sobre a receita e o potencial de oportunidade.")

    with sub[2]:
        fig = go.Figure()
        for nome, k, cor in [("Margem EBITDA recorrente", "margem_ebitda", COR_TOTAL),
                             ("Margem operacional", "margem_oper", "#f2b134"), ("Margem líquida", "margem_liq", COR_GANHO)]:
            fig.add_scatter(name=nome, x=anos_txt, y=[modelos[x][k] * 100 for x in anos_graf], mode="lines+markers+text",
                            line=dict(color=cor, width=3), text=[f"{br(modelos[x][k] * 100)}%" for x in anos_graf],
                            textposition="top center",
                            hovertext=[f"<b>{nome} · {x}</b><br>{pct(modelos[x][k], 1)}" + c.dica(
                                nome.replace("Margem operacional", "Margem EBITDA")) for x in anos_graf], hoverinfo="text")
        c.layout_base(fig, "Evolução das margens sobre a receita líquida (%)", altura=460)
        fig.update_yaxes(ticksuffix="%")
        fig.update_xaxes(type="category")
        c.mostrar_grafico(fig, key="joao_margens")
        mi_, mf = modelos[anos_graf[0]], modelos[anos_graf[-1]]
        c.leitura(f"Margem EBITDA recorrente: {pct(mi_['margem_ebitda'], 1)} ({anos_graf[0]}) → "
                  f"<b>{pct(mf['margem_ebitda'], 1)}</b> ({anos_graf[-1]}); margem líquida: {pct(mi_['margem_liq'], 1)} → "
                  f"<b>{pct(mf['margem_liq'], 1)}</b>.")

    with sub[3]:
        ordenado = sorted(base_custos, key=lambda x: -x[1])
        total_c = sum(v for _, v, _ in ordenado)
        acum, soma = [], 0
        for _, v, _ in ordenado:
            soma += v
            acum.append(soma / total_c * 100)
        fig = go.Figure()
        fig.add_bar(x=[n for n, _, _ in ordenado], y=[v / 1e3 for _, v, _ in ordenado], name="Valor (R$ mi)",
                    marker_color=[c.cor_oport(p) for _, _, p in ordenado], text=[br(v / 1e3, 0) for _, v, _ in ordenado],
                    textposition="outside",
                    hovertext=[f"<b>{n}</b><br>R$ {br(v / 1e3, 0)} mi · potencial {p}" + c.dica(n)
                               for n, v, p in ordenado],
                    hoverinfo="text")
        fig.add_scatter(x=[n for n, _, _ in ordenado], y=acum, name="% acumulado", yaxis="y2", mode="lines+markers",
                        line=dict(color="#333", width=2), hovertemplate="%{y:.1f}% acumulado<extra></extra>")
        c.layout_base(fig, f"Pareto de custos — {rot}: poucos itens concentram a maior parte do gasto", altura=520,
                      y_titulo="R$ milhões")
        fig.update_layout(yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 105], ticksuffix="%",
                                      dtick=20, showgrid=False))
        c.mostrar_grafico(fig, key="joao_pareto")
        n80 = next(i for i, x in enumerate(acum) if x >= 80) + 1
        c.leitura(f"{n80} de {len(ordenado)} itens concentram 80% do custo: "
                  f"{', '.join(n for n, _, _ in ordenado[:n80])}." + c.dica("Pareto").replace("<br>", " "))

    with sub[4]:
        fin_out = m["financeiro"] + m["outros_op"]
        raiz = "Receita bruta" + (" + resultado financeiro" if fin_out > 0 else "")
        rotulos, pais, vals = [raiz], [""], [m["receita_bruta"] + max(fin_out, 0)]
        grupos = [("Deduções e impostos", [(n, v) for n, v, _, _ in m["det"]["ded"]]),
                  ("Despesas operacionais", [(n, v) for n, v, _, _ in m["det"]["desp"]]),
                  ("D&A e IR", [("Depreciação e amortização ", m["da"]), ("IR e CS corrente", m["ir_corrente"]),
                                ("IR e CS diferido", m["ir_diferido"])] + ([("Resultado financeiro e outros", -fin_out)]
                                                                          if fin_out < 0 else [])),
                  ("Lucro líquido", [("Lucro líquido ", m["lucro"])])]
        for gnome, filhos in grupos:
            filhos = [(n, v) for n, v in filhos if v > 0]
            rotulos.append(gnome); pais.append(raiz); vals.append(sum(v for _, v in filhos))
            for n_, v in filhos:
                rotulos.append(n_); pais.append(gnome); vals.append(v)
        vals[0] = sum(v for r_, p_, v in zip(rotulos, pais, vals) if p_ == raiz)
        fig = go.Figure(go.Treemap(labels=rotulos, parents=pais, values=[v / 1e3 for v in vals], branchvalues="total",
                                   texttemplate="%{label}<br>R$ %{value:,.0f} mi", textfont=dict(size=14),
                                   hovertemplate="%{label}<br>R$ %{value:,.1f} mi · %{percentRoot:.1%} do total<extra></extra>"))
        c.layout_base(fig, f"Para onde vai cada real — {rot} (clique para aprofundar)", altura=580, legenda=False)
        c.mostrar_grafico(fig, key="joao_treemap")
        if fin_out > 0:
            st.caption(f"O resultado financeiro e outros foi positivo ({mi(fin_out)}) e entra somado à receita na raiz.")

    with sub[5]:
        if mp:
            itens = [("Receita líquida", "receita_liquida", True), ("Despesas operacionais", "despesas", False),
                     ("EBITDA recorrente", "ebitda_rec", True), ("Lucro líquido", "lucro", True)]
            vals = [c.var(m[k], mp[k]) for _, k, _ in itens]
            cores = [COR_GANHO if (v >= 0) == bom else COR_QUEDA for v, (_, _, bom) in zip(vals, itens)]
            fig = go.Figure(go.Bar(x=[n for n, _, _ in itens], y=[v * 100 for v in vals], marker_color=cores,
                                   text=[pct(v, 1, sinal=True) for v in vals], textposition="outside",
                                   hovertext=[f"<b>{n}</b><br>{pct(v, 1, sinal=True)} vs {rot_ant}" + c.dica(n)
                                              for (n, _, _), v in zip(itens, vals)], hoverinfo="text"))
            c.layout_base(fig, f"Variação {rot_ant} → {rot} (%) · verde = favorável, vermelho = desfavorável", altura=460,
                          legenda=False)
            fig.update_yaxes(ticksuffix="%")
            c.mostrar_grafico(fig, key="joao_var")
        else:
            st.info("Não há período anterior de mesma duração na base (começa em 2020).")
    c.diagnostico([
        "Pessoal e TI são os maiores custos e os que mais cresceram desde 2020: é aí que está a eficiência a buscar.",
        "A amortização do intangível da Cetip praticamente acabou (D&A de R$ 1,04 bi em 2020 para R$ 0,39 bi em 2025), "
        "o que ajuda o lucro, mas não o EBITDA.",
        "A margem EBITDA recorrente caiu de 76% (2020) para 69% (2025): a receita cresceu menos que os custos.",
    ])
    c.fonte([("EBITDA, margens, custos", "Planilha B3 · IS (New Seg)", "Linhas 25–39, 56, 66 e 79")])

    # ---------------------------------------------------------------- Oportunidades
    m_ini, m_fim = modelos[anos[0]], modelos[anos[-1]]
    ti_ini = next(v for n, v, *_ in m_ini["det"]["desp"] if n == "Tecnologia da informação")
    ti_fim = next(v for n, v, *_ in m_fim["det"]["desp"] if n == "Tecnologia da informação")
    c.oportunidade(janela, ABA, "Alto", "Renegociar contratos de TI e terceiros",
                   f"TI e serviços de terceiros somam {mi(soma_alto)} em {rot}; TI foi de {mi(ti_ini)} ({anos[0]}) para "
                   f"{mi(ti_fim)} ({anos[-1]}).",
                   f"Renegociar licenças, nuvem e consultorias: 10% de redução liberaria cerca de {mi(soma_alto * 0.10)} "
                   "de EBITDA.", f"{pct(soma_alto / m['despesas'], 0)} das despesas")
    if mp:
        c.oportunidade(janela, ABA, "Alto" if dd > dr else "Forte",
                       "Despesas crescendo mais que a receita" if dd > dr else "Ganho de escala",
                       f"Despesas {pct(dd, 1, sinal=True)} contra receita líquida {pct(dr, 1, sinal=True)} ({rot_ant} → {rot}).",
                       "Fixar teto de crescimento das despesas abaixo da receita (orçamento base zero nas linhas de alto "
                       "potencial)." if dd > dr else "Manter a disciplina de custos.")
    c.oportunidade(janela, ABA, "Alto" if m_fim["margem_ebitda"] < m_ini["margem_ebitda"] - 0.03 else "Médio",
                   "Margem EBITDA recorrente em queda",
                   f"A margem foi de {pct(m_ini['margem_ebitda'], 1)} ({anos[0]}) para {pct(m_fim['margem_ebitda'], 1)} "
                   f"({anos[-1]}).", "Recuperar margem com eficiência em pessoal e TI e foco nas receitas de maior margem.")
    c.oportunidade(janela, ABA, "Médio", "Pessoal: maior custo",
                   f"Pessoal e encargos somam {mi(maior[1])} ({pct(maior[1] / m['despesas'], 0)} das despesas sem D&A).",
                   "Atrelar mais a remuneração variável ao resultado e revisar a estrutura.")
    c.oportunidade(janela, ABA, "Médio", "Carga tributária",
                   f"Alíquota efetiva de {pct(m['aliquota_efetiva'], 1)} em {rot}, influenciada pelo IR diferido.",
                   "Usar o JCP no limite legal e acompanhar a atualização do imposto diferido.")
    c.oportunidade(janela, ABA, "Forte", "Fim da amortização da Cetip",
                   f"D&A caiu de {mi(modelos[2020]['da'])} (2020) para {mi(modelos[2025]['da'])} (2025).",
                   "Efeito contábil favorável ao lucro; não exige ação.")
    c.bloco_oportunidades(janela, ABA)
