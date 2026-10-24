"""Aba 4 · Victor — Solidez Financeira, Endividamento e Geração de Valor.

Gerado a partir do módulo original do Victor (pages/4_Solidez_Financeira.py), com os padrões comuns do painel:
filtros de ano vindos da janela global, indicadores-chave e painel de alertas do utils/comum.py,
oportunidades registradas para a Conclusão.
"""
import pandas as pd
import streamlit as st

from utils import comum as cm
from utils import solidez_charts as sc
from utils import solidez_data as sd
from utils.solidez_data import br, dinheiro, mult, pct

ABA = "Solidez Financeira"
STATUS_COR = cm.STATUS_COR


def plot(fig, key=None):
    cm.mostrar_grafico(fig, key=key)


def visao(key):
    return st.segmented_control("Visão", ["Macro", "Micro"], default="Macro", key=key,
                                label_visibility="collapsed") or "Macro"


def botoes(rotulo, opcoes, padrao, key):
    """Escolha em bloquinhos (padrão do painel): anos direto; trimestres em ano + trimestre."""
    opcoes = list(opcoes)
    if opcoes and all(len(o) == 4 and o[1] == "T" for o in opcoes):
        return cm.bloco_trimestre(rotulo, opcoes, padrao, key)
    return cm.blocos(rotulo, opcoes, padrao, key)


def intervalo(rotulo, opcoes, de, ate, key):
    """Par De/Até de trimestres, cada um em bloquinhos de ano + trimestre."""
    g_de, g_ate = st.columns(2)
    with g_de:
        q0 = cm.bloco_trimestre("De", opcoes, de, f"{key}_de")
    with g_ate:
        q1 = cm.bloco_trimestre("Até", opcoes, ate, f"{key}_ate")
    return q0, q1


def cabecalho(n, nome, tese, abertura):
    cm.cabecalho_secao(f"Bloco {n} · {nome}", tese, abertura)


def tabela_fonte(linhas):
    cm.fonte(linhas)


def diagnostico(itens):
    cm.diagnostico(itens)


def render(janela):
    tri, anual = sd.load()
    erros = sd.validar(tri, anual)

    st.markdown("## 🏦 Solidez Financeira, Endividamento e Geração de Valor")
    st.caption("A B3 é financeiramente sólida, e o dinheiro que ela gera volta ao acionista de forma "
               "sustentável? Dados oficiais da B3 até o 2T26 (base em R\\$ mil).")
    if erros:
        st.error("Falha nos testes de validação da base:\n\n" + "\n".join(f"- {e}" for e in erros))
    cm.glossario("victor")

    anos = janela.anos
    with st.container(border=True):
        f = st.columns([1.3, 1, 1.1, 1.1])
        gran = f[0].radio("Granularidade", ["Anual", "Trimestral", "LTM"], horizontal=True, key="vic_gran",
                          help="Anual usa a aba Anual (2026 é YTD); LTM usa as colunas *_ltm (soma de 12 meses).")
        unidade = f[1].radio("Unidade", ["R$ mi", "R$ bi"], index=1, horizontal=True, key="vic_un")
        regime = f[2].radio("Regime dos proventos", ["Declarado", "Pago"], horizontal=True, key="vic_reg",
                            help="Declarado: aba de proventos (competência). Pago: DFC (caixa).")
        destacar = f[3].toggle("Destacar incoerências", value=True, key="vic_dest",
                               help="Mostra a linha oficial de aplicações ao lado do FCO e o aviso de garantias de terceiros.")
        # Filtro "Anos" do painel original do Victor, dentro da janela global da barra lateral
        if janela.ano_fim > janela.ano_ini:
            anos = st.slider("Anos", janela.ano_ini, janela.ano_fim, (janela.ano_ini, janela.ano_fim),
                             key=f"vic_anos_{janela.ano_ini}_{janela.ano_fim}",
                             help="Anos desta aba; o limite é a janela da barra lateral.")
        st.caption(f"Filtros desta aba. Os anos ficam dentro da janela da barra lateral ({janela.rotulo()}); "
                   "a faixa de alavancagem é fixa: 2,0x e 2,5x (referência Moody's).")

    div, suf, dec_padrao = sd.escala(unidade)
    gran_saldo = "Anual" if gran == "Anual" else "Trimestral"  # saldos do BP não têm LTM

    # Período de referência: último trimestre dentro do filtro de anos, e 1 ano antes
    i_ref, i_ant = sd.ref_idx(tri, anos[1])
    r = tri.loc[i_ref]
    ra = tri.loc[i_ant] if i_ant is not None else None
    per_ref = r["trimestre"]
    per_ant = ra["trimestre"] if ra is not None else None


    def dif(col):
        return None if ra is None else r[col] - ra[col]


    # Indicadores-chave (padrão comum)
    st.markdown("#### Indicadores-chave e painel de alertas")
    st.caption(f"Números do {per_ref}" + (f"; variação contra o {per_ant}." if per_ant else "."))
    d_folga = None if ra is None else -(r["divida_liquida"] - ra["divida_liquida"])
    d_payout = None if ra is None or pd.isna(ra["payout_ltm"]) else r["payout_ltm"] - ra["payout_ltm"]
    cm.kpis([
        dict(rotulo="Caixa total", valor=dinheiro(r["caixa_total"], unidade, md=False),
             delta=None if ra is None else dinheiro(dif("caixa_total"), unidade, sinal=True, md=False)),
        dict(rotulo="Dívida bruta", valor=dinheiro(r["divida_bruta"], unidade, md=False),
             delta=None if ra is None else dinheiro(dif("divida_bruta"), unidade, sinal=True, md=False),
             delta_color="inverse"),
        dict(rotulo="Folga (caixa − dívida)", valor=dinheiro(-r["divida_liquida"], unidade, md=False),
             delta=None if ra is None else dinheiro(d_folga, unidade, sinal=True, md=False)),
        dict(rotulo="Alavancagem", valor=mult(r["divida_bruta_ebitda_ltm"]), termo="Alavancagem",
             delta=None if ra is None or pd.isna(ra["divida_bruta_ebitda_ltm"])
             else mult(dif("divida_bruta_ebitda_ltm"), sinal=True), delta_color="inverse"),
        dict(rotulo="Payout LTM", valor=pct(r["payout_ltm"]), termo="Payout",
             delta=None if d_payout is None else f"{'+' if d_payout >= 0 else '-'}{br(abs(d_payout) * 100, 0)} p.p.",
             delta_color="off"),
    ])

    # ======================================================================================
    # 3. Radar de alertas
    # ======================================================================================


    def status_alav(v):
        if pd.isna(v):
            return "Informativo"
        return "Confortável" if v <= sd.ALAV_CONFORTAVEL else ("Atenção" if v <= sd.ALAV_GATILHO else "Alerta")


    def status_min(v, minimo):
        if pd.isna(v):
            return "Informativo"
        return "Confortável" if v >= minimo else "Atenção"


    acum = anual[(anual["ano"] >= 2021) & (anual["ano"] <= 2025)]
    devolvido_fcl = acum["retorno_acionista_caixa"].sum() / acum["fcl_pos_juros"].sum()


    def delta_txt(col, fmt):
        if ra is None or pd.isna(ra[col]) or pd.isna(r[col]):
            return ""
        return f"{fmt(r[col] - ra[col])} vs {per_ant}"


    radar = [
        dict(nome="Alavancagem", formula="Dívida bruta ÷ EBITDA recorrente LTM", curto="a alavancagem", valor=mult(r["divida_bruta_ebitda_ltm"]),
             delta=delta_txt("divida_bruta_ebitda_ltm", lambda v: mult(v, sinal=True)),
             status=status_alav(r["divida_bruta_ebitda_ltm"]),
             desc="Quantos anos de EBITDA pagariam toda a dívida.",
             fonte="Moody's: histórico 1,0–2,0x; rebaixamento se > 2,5x de forma sustentada"),
        dict(nome="Cobertura de juros", formula="EBIT ÷ despesas financeiras LTM", chave="cobertura",
             curto="a cobertura de juros", valor=mult(r["cobertura_ebit_desp_fin_ltm"], 1),
             delta=delta_txt("cobertura_ebit_desp_fin_ltm", lambda v: mult(v, 1, sinal=True)),
             status=status_min(r["cobertura_ebit_desp_fin_ltm"], sd.COBERTURA_MIN),
             desc="Quantas vezes o resultado operacional cobre as despesas financeiras.",
             fonte="Moody's projeta 4,0–4,5x para 2025–26 (5,1x na métrica ajustada dela)"),
        dict(nome="Capacidade de pagamento", formula="FCO LTM ÷ dívida bruta", curto="a capacidade de pagamento", valor=pct(r["fco_sobre_divida_ltm"]),
             delta=delta_txt("fco_sobre_divida_ltm", lambda v: f"{'+' if v >= 0 else '-'}{br(abs(v) * 100, 0)} p.p."),
             status=status_min(r["fco_sobre_divida_ltm"], sd.FCO_DIVIDA_MIN),
             desc="Quanto da dívida o caixa da operação de 12 meses pagaria.",
             fonte="Moody's projeta 25–35% para 2025–26"),
        dict(nome="Folga de caixa", formula="Caixa total − dívida bruta",
             valor=dinheiro(-r["divida_liquida"], unidade, md=False),
             delta="" if ra is None else f"{dinheiro(d_folga, unidade, sinal=True, md=False)} vs {per_ant}",
             status="Informativo", desc="Quanto sobra de caixa depois de pagar toda a dívida.",
             fonte="Moody's: liquidez \"extremamente forte\""),
        dict(nome="Pressão de curto prazo", formula="Dívida que vence em 12 meses ÷ caixa total",
             valor=pct(r["divida_bruta_cp"] / r["caixa_total"]),
             delta="" if ra is None else
             f"{'+' if (r['divida_bruta_cp'] / r['caixa_total'] - ra['divida_bruta_cp'] / ra['caixa_total']) >= 0 else '-'}"
             f"{br(abs(r['divida_bruta_cp'] / r['caixa_total'] - ra['divida_bruta_cp'] / ra['caixa_total']) * 100, 0)} p.p. vs {per_ant}",
             status="Informativo", desc="Parte do caixa comprometida com dívida que vence em 12 meses.", fonte="—"),
        dict(nome="Payout", formula="(Dividendos + JCP + recompras) ÷ lucro, LTM", valor=pct(r["payout_ltm"]),
             delta="" if d_payout is None else f"{'+' if d_payout >= 0 else '-'}{br(abs(d_payout) * 100, 0)} p.p. vs {per_ant}",
             status="Informativo", desc="Quanto do lucro de 12 meses voltou ao acionista. Acima de 100%, devolveu mais do que lucrou.",
             fonte="Moody's: distribuição \"elevada\", mas compatível"),
        dict(nome="Devolução x caixa livre", formula="Devolvido ÷ FCL depois dos juros, 2021–2025",
             valor=pct(devolvido_fcl),
             delta="acumulado de 5 anos, valores pagos", status="Informativo",
             desc="Quanto foi devolvido ao acionista para cada R$ 1 de FCL depois dos juros.", fonte="—"),
    ]

    n_conf = sum(1 for x in radar[:3] if x["status"] == "Confortável")
    atencao = [x for x in radar[:3] if x["status"] in ("Atenção", "Alerta")]
    leitura_radar = (f"**Leitura:** no {per_ref}, {n_conf} de 3 indicadores com referência de mercado "
                     f"{'está confortável' if n_conf == 1 else 'estão confortáveis'}")
    if atencao:
        leitura_radar += " e " + "; ".join(f"**{x['curto']} ({x['valor']})** pede atenção" for x in atencao)
        if any(x.get("chave") == "cobertura" for x in atencao):
            leitura_radar += ", abaixo da faixa de 4,0–4,5x que a Moody's projeta para a B3"
    for x in radar:
        x["regra"] = x.pop("fonte")
    cm.painel_alertas(radar, leitura=leitura_radar + ".",
                      rodape="As métricas da Moody's usam ajustes próprios da agência; aqui usamos só as linhas oficiais "
                             "da B3. Passe o mouse sobre um card para ver o que ele mede.")
    cm.legenda_oportunidade()
    st.caption("Nos gráficos desta aba, os componentes são pintados pela cor de oportunidade; o **hachurado amarelo** marca "
               "uma incoerência da divulgação, mostrada com a linha oficial e sem correção.")

    # ======================================================================================
    # 4. Bloco 1 · Estrutura de capital
    # ======================================================================================
    cabecalho(
        1, "Estrutura de capital", "A B3 tem mais caixa do que dívida, mas a folga encolheu",
        "A B3 tem mais caixa do que dívida em todos os anos, mas a folga (caixa − dívida) caiu de R\\$ 10,8 bi (2020) "
        "para R\\$ 2,5 bi (2024) e voltou a R\\$ 4,4 bi (2T26).",
    )
    v1 = visao("v1")
    if v1 == "Macro":
        df1 = sd.serie(tri, anual, gran_saldo, anos, stocks=["caixa_total", "divida_bruta", "divida_liquida"])
        plot(sc.macro_bloco1(df1, unidade))
        folga = -df1["divida_liquida"]
        i_min = folga.idxmin()
        st.markdown(
            f"Caixa maior que a dívida em **{(folga > 0).sum()} de {len(df1)}** períodos. A folga foi de "
            f"**{dinheiro(folga.iloc[0], unidade)}** ({df1['periodo'].iloc[0]}) para "
            f"**{dinheiro(folga.iloc[-1], unidade)}** ({df1['periodo'].iloc[-1]}), com mínimo de "
            f"{dinheiro(folga[i_min], unidade)} em {df1['periodo'][i_min]}."
            + (" Em 2026 (YTD), os saldos são os do 2T26." if gran == "Anual" and anos[1] == 2026 else "")
        )
    else:
        base = anual if gran == "Anual" else tri
        base = base[(base["ano"] >= anos[0]) & (base["ano"] <= anos[1])]
        opcoes = list(base["periodo"])
        per = botoes("Período", opcoes, opcoes[-1], key=f"p1_{gran_saldo}")
        rr = base[base["periodo"] == per].iloc[0]
        st.markdown("**Do caixa ao caixa líquido**")
        plot(sc.micro_bloco1_cascata(rr, unidade))
        st.markdown(
            f"Em {per}, o caixa total de **{dinheiro(rr['caixa_total'], unidade)}** cobre a dívida de "
            f"**{dinheiro(rr['divida_bruta'], unidade)}** e sobram **{dinheiro(-rr['divida_liquida'], unidade)}**. "
            f"Quase todo o caixa está em aplicações ({pct((rr['aplic_fin_cp'] + rr['aplic_fin_lp']) / rr['caixa_total'])}); "
            f"a dívida de curto prazo é {dinheiro(rr['divida_bruta_cp'], unidade)}."
        )
        if destacar:
            st.warning(
                f"⚠️ O caixa inclui {dinheiro(rr['garantias_recebidas'], 'R$ bi', 2)} de garantias de terceiros "
                "(`garantias_recebidas`, BP linha 37), que também estão no passivo."
            )
        st.markdown(f"**Dívida em {per}: quando vence**")
        plot(sc.micro_bloco1_prazo(rr, unidade))
        st.markdown(
            f"Em {per}, **{dinheiro(rr['divida_bruta_cp'], unidade)}** "
            f"({pct(rr['divida_bruta_cp'] / rr['divida_bruta'])} da dívida) vencem em até 12 meses e "
            f"**{dinheiro(rr['divida_bruta_lp'], unidade)}** vencem depois."
        )
        ultimo = tri.iloc[-1]
        no_ultimo = per == ultimo["periodo"] or (gran == "Anual" and rr["ano"] == ultimo["ano"])
        ins = sd.DIVIDA_INSTRUMENTOS
        part = ins.groupby("tipo")["saldo_mi"].sum() / ins["saldo_mi"].sum()
        texto_ins = (
            f"{pct(part['Debêntures'])} da dívida são debêntures (quase todas no CDI), {pct(part['Bond'])} é o bond "
            f"em dólar e {pct(part['Empréstimos'])} são empréstimos bancários em dólar. Total: "
            f"R\\$ {br(ultimo['divida_bruta'] / 1e3, 1)} mi, igual à `divida_bruta` do {ultimo['trimestre']}."
        )
        if no_ultimo:
            st.markdown(f"**Composição da dívida no {ultimo['trimestre']}, por instrumento (ITR 2T26, nota 9)**")
            plot(sc.micro_bloco1_instrumentos())
            st.markdown(texto_ins)
        else:
            st.caption(f"A divisão por instrumento (debêntures, bond, empréstimos) só é publicada nas notas do ITR/DFP, "
                       f"fora da planilha; a base tem o detalhe apenas do {ultimo['trimestre']}. Para {per}, o gráfico "
                       f"acima usa a divisão por prazo do balanço oficial.")
            with st.expander(f"Ver a composição por instrumento do {ultimo['trimestre']}"):
                plot(sc.micro_bloco1_instrumentos())
                st.markdown(texto_ins)
        with st.expander("Tabela de instrumentos"):
            t = ins[["instrumento", "taxa", "vencimento", "saldo_mi"]].rename(
                columns={"instrumento": "Instrumento", "taxa": "Taxa", "vencimento": "Vencimento do principal",
                         "saldo_mi": "Saldo 30/06/2026 (R$ mi)"})
            st.dataframe(t, hide_index=True, width="stretch",
                         column_config={"Saldo 30/06/2026 (R$ mi)": st.column_config.NumberColumn(format="%.1f")})

    diagnostico([
        "A dívida dobrou em 2021 (de R\\$ 7,1 para R\\$ 14,2 bi) e é rolada todo ano: as captações de R\\$ 2,8 a 6,7 bi por ano "
        "repagam os vencimentos (DFC linhas 72, 73 e 75; colunas `emissao_debentures`, `amortizacao_divida`).",
        "A B3 trocou capital próprio por dívida de propósito: dívida ÷ (dívida + PL) foi de 22% (2020) para 44% (2T26).",
        "70% da dívida são debêntures (quase todas no CDI), 21% é o bond em dólar e 9% são empréstimos bancários em dólar.",
        "**Ponto de atenção:** R\\$ 2,6 bi vencem em 12 meses (17% da dívida), contra R\\$ 0,3 bi um ano antes. O salto vem dos "
        "empréstimos B3 Inova que vencem em 2026 e da 1ª parcela da 8ª emissão (mai/2027).",
        "**Destaque de transparência:** o caixa inclui R\\$ 2,65 bi de garantias de participantes. A Moody's exclui esse valor "
        "(caixa de R\\$ 14,9 bi no 1T26). A B3 poderia divulgar o caixa próprio separado na planilha.",
    ])
    tabela_fonte([
        ("Disponibilidades", "Balance Sheet · 8", "`caixa_disponibilidades`"),
        ("Aplicações CP e LP", "Balance Sheet · 9 e 18", "`aplic_fin_cp`, `aplic_fin_lp`"),
        ("Garantias de terceiros", "Balance Sheet · 37", "`garantias_recebidas`"),
        ("Dívida CP e LP", "Balance Sheet · 43–45 e 51–53", "`divida_bruta_cp`, `divida_bruta_lp`"),
        ("Patrimônio líquido", "Balance Sheet · 60", "`patrimonio_liquido`"),
        ("Captações e amortizações", "Cash Flow Statement · 72, 73, 75", "`emissao_debentures`, `amortizacao_divida`"),
        ("Dívida por instrumento", "ITR 2T26, nota 9", "(tabela fixa)"),
    ])

    # ======================================================================================
    # 5. Bloco 2 · Alavancagem
    # ======================================================================================
    cabecalho(
        2, "Alavancagem", "Dívida em ~2x o EBITDA, abaixo do gatilho de 2,5x da Moody's",
        "A dívida equivale a 1,98x o EBITDA recorrente no 2T26, dentro do histórico de até 2,0x e abaixo do gatilho de "
        "rebaixamento de 2,5x da Moody's. A melhora desde o pico de 2,24x (1T24) veio do crescimento do EBITDA, "
        "não de pagar dívida.",
    )
    tri_ltm = tri[tri["ebitda_recorrente_ltm"].notna()]


    def alav_hist(anos_):
        if gran == "Anual":
            return sd.fim_de_ano(tri_ltm, anos_)
        d = tri_ltm[(tri_ltm["ano"] >= anos_[0]) & (tri_ltm["ano"] <= anos_[1])].copy()
        return d.reset_index(drop=True)


    v2 = visao("v2")
    if v2 == "Macro":
        df2 = alav_hist(anos)
        if df2.empty:
            st.info("A alavancagem LTM começa no 4T20. Amplie o filtro de anos.")
        else:
            plot(sc.macro_bloco2(df2))
            if gran == "Anual":
                st.caption("Visão anual: múltiplo do fim de cada ano (4T, igual ao anual) e o último trimestre em LTM, "
                           "para não comparar 2026 YTD com anos fechados.")
            b = df2["divida_bruta_ebitda_ltm"]
            ip = b.idxmax()
            st.markdown(
                f"A alavancagem foi de **{mult(b.iloc[0])}** ({df2['periodo'].iloc[0]}) a **{mult(b.iloc[-1])}** "
                f"({df2['periodo'].iloc[-1]}), com pico de {mult(b[ip])} em {df2['periodo'][ip]}. A dívida líquida ÷ EBITDA "
                f"ficou negativa em todo o período ({mult(df2['divida_liquida_ebitda_ltm'].min())} a "
                f"{mult(df2['divida_liquida_ebitda_ltm'].max())}): a B3 tem caixa líquido."
            )
            ult = b.iloc[-1]
            msg = f"{df2['periodo'].iloc[-1]}: dívida bruta ÷ EBITDA LTM de {mult(ult)}"
            s = status_alav(ult)
            if s == "Confortável":
                st.success(f"🟢 Confortável · {msg}, dentro do histórico de até 2,0x.")
            elif s == "Atenção":
                st.warning(f"🟡 Atenção · {msg}, entre 2,0x e o gatilho de 2,5x da Moody's.")
            else:
                st.error(f"🔴 Alerta · {msg}, acima do gatilho de 2,5x da Moody's.")
    else:
        st.markdown("**Ponte da alavancagem entre dois trimestres**")
        qs = list(tri_ltm["trimestre"])
        q0, q1 = intervalo("De / Até", qs, "1T24" if "1T24" in qs else qs[0], qs[-1], key="p2_intervalo")
        r0, r1 = tri_ltm[tri_ltm["trimestre"] == q0].iloc[0], tri_ltm[tri_ltm["trimestre"] == q1].iloc[0]
        plot(sc.micro_bloco2_ponte(r0, r1, q0, q1))
        ef_e = r0["divida_bruta"] / r1["ebitda_recorrente_ltm"] - r0["divida_bruta_ebitda_ltm"]
        ef_d = r1["divida_bruta_ebitda_ltm"] - r0["divida_bruta"] / r1["ebitda_recorrente_ltm"]
        st.markdown(
            f"De {q0} para {q1}, a alavancagem foi de **{mult(r0['divida_bruta_ebitda_ltm'])}** para "
            f"**{mult(r1['divida_bruta_ebitda_ltm'])}**. O EBITDA LTM variou "
            f"{pct(r1['ebitda_recorrente_ltm'] / r0['ebitda_recorrente_ltm'] - 1, sinal=True)} (efeito {mult(ef_e, sinal=True)}) "
            f"e a dívida {pct(r1['divida_bruta'] / r0['divida_bruta'] - 1, sinal=True)} (efeito {mult(ef_d, sinal=True)}). "
            "Verde reduz a alavancagem (bom); vermelho aumenta."
        )

        st.markdown("**Da receita ao EBITDA recorrente**")
        base = anual[(anual["ano"] >= anos[0]) & (anual["ano"] <= anos[1])]
        opcoes = list(base["periodo"])
        padrao = opcoes.index("2025") if "2025" in opcoes else len(opcoes) - 1
        per = botoes("Ano", opcoes, opcoes[padrao], key="p2_ano")
        ra2 = base[base["periodo"] == per].iloc[0]
        plot(sc.micro_bloco2_ebitda(ra2, unidade))
        desp = {n: -ra2[c] for c, n in sd.CASCATA_DESPESAS}
        maior = max(desp, key=desp.get)
        st.markdown(
            f"Em {per}, a receita líquida de **{dinheiro(ra2['receita_liquida'], unidade, 2 if suf == 'bi' else 0)}** virou "
            f"**{dinheiro(ra2['ebitda_recorrente'], unidade, 2 if suf == 'bi' else 0)}** de EBITDA recorrente "
            f"(margem de {pct(ra2['ebitda_recorrente'] / ra2['receita_liquida'])}). O maior custo é {maior.lower()} "
            f"({dinheiro(desp[maior], unidade, 2 if suf == 'bi' else 0)}), ponte com o módulo de eficiência."
        )

    diagnostico([
        "O EBITDA LTM foi de R\\$ 6,3 bi (1T24) para R\\$ 7,5 bi (2T26), +20%. A dívida cresceu só 6%.",
        "Dívida líquida ÷ EBITDA negativa em todo o período, de −1,8x a −0,3x: a B3 tem caixa líquido.",
        "Cobertura de juros (EBIT ÷ despesas financeiras) de 3,7x nos 12 meses até o 2T26, abaixo dos 4,0–4,5x projetados "
        "pela Moody's (5,1x na métrica ajustada da agência).",
        "Custo implícito da dívida ~12,2% a.a. x rendimento do caixa ~12,5% (2025): usar caixa para pagar dívida quase não "
        "economiza juros.",
        "Maior custo do EBITDA: pessoal (R\\$ 1,56 bi em 2025), seguido de TI (R\\$ 0,69 bi). Ponte com o módulo de eficiência.",
    ])
    tabela_fonte([
        ("Dívida bruta", "Balance Sheet · 43–45 + 51–53", "`divida_bruta`"),
        ("EBITDA e EBITDA recorrente", "IS (New Seg) · 66 e 79", "`ebitda`, `ebitda_recorrente`"),
        ("Receita total, deduções", "IS (New Seg) · 4 e 22", "`receita_total`, `deducoes_receita`"),
        ("Pessoal, TI, D&A, atrelada", "IS (New Seg) · 27, 28, 29, 30",
         "`desp_pessoal`, `desp_ti`, `desp_depreciacao_amortizacao`, `desp_atrelada_faturamento`"),
        ("Outras despesas", "IS (New Seg) · 31 a 38", "`desp_outras`"),
        ("EBIT", "IS (New Seg) · 39", "`ebit_resultado_operacional`"),
        ("Receitas e despesas financeiras", "IS (New Seg) · 46 e 47", "`receitas_financeiras`, `despesas_financeiras`"),
    ])

    # ======================================================================================
    # 6. Bloco 3 · Conversão de caixa
    # ======================================================================================
    cabecalho(
        3, "Conversão de caixa", "O FCO oficial oscila muito mais que o lucro, e a explicação está numa linha da DFC",
        "O FCO oficial oscila entre 0,66x e 2,34x o lucro, enquanto o lucro fica estável em R\\$ 4,1–4,7 bi. A oscilação "
        "vem de uma linha que a B3 lança dentro do operacional: a variação das aplicações financeiras.",
    )
    v3 = visao("v3")
    if v3 == "Macro":
        df3 = sd.serie(tri, anual, gran, anos,
                       flows=["lucro_liquido_acionistas", "fco", "fcl", "var_aplicacoes_financeiras"])
        plot(sc.macro_bloco3(df3, unidade, destacar))
        conv = df3["fco"] / df3["lucro_liquido_acionistas"]
        st.markdown(
            f"Conversão FCO ÷ lucro entre **{mult(conv.min())}** e **{mult(conv.max())}**, com lucro entre "
            f"{dinheiro(df3['lucro_liquido_acionistas'].min(), unidade)} e {dinheiro(df3['lucro_liquido_acionistas'].max(), unidade)}"
            f" por período{' (LTM)' if gran == 'LTM' else ''}. Os números acima das barras são a conversão FCO ÷ lucro."
            + (" 2026 (YTD) aparece mais claro: só 2 trimestres." if gran == "Anual" and anos[1] == 2026 else "")
        )
    else:
        base = anual[(anual["ano"] >= anos[0]) & (anual["ano"] <= anos[1])]
        opcoes = list(base["periodo"])
        padrao = opcoes.index("2025") if "2025" in opcoes else len(opcoes) - 1
        per = botoes("Ano", opcoes, opcoes[padrao], key="p3_ano")
        r3 = base[base["periodo"] == per].iloc[0]
        st.markdown("**Do lucro ao FCL depois dos juros (só linhas oficiais)**")
        plot(sc.micro_bloco3(r3, unidade))
        d3 = 2 if suf == "bi" else 0
        antes = r3["fco"] - r3["var_aplicacoes_financeiras"]
        st.markdown(
            f"Em {per}, antes das aplicações a operação gerou **{dinheiro(antes, unidade, d3)}** contra lucro de "
            f"{dinheiro(r3['lucro_liquido_dfc'], unidade, d3)}. A linha de aplicações financeiras "
            f"(<span style='color:#9A7400'>**amarela hachurada**</span>, incoerência destacada) somou {dinheiro(r3['var_aplicacoes_financeiras'], unidade, d3, sinal=True)} "
            f"e o FCO publicado ficou em **{dinheiro(r3['fco'], unidade, d3)}**. Depois do CAPEX e dos juros, sobram "
            f"**{dinheiro(r3['fcl_pos_juros'], unidade, d3)}**.",
            unsafe_allow_html=True,
        )
        st.caption("A soma dos passos fecha exatamente com `fco` em todos os anos (testado ao carregar).")

    diagnostico([
        "Antes das aplicações, a operação gera mais caixa do que lucro: em 2025, R\\$ 7,2 bi contra R\\$ 4,6 bi. Depois que a B3 "
        "lança R\\$ 2,7 bi de aplicações no operacional, o FCO publicado cai para R\\$ 4,4 bi.",
        "Em 2022 e 2024 aconteceu o contrário: a B3 resgatou aplicações (+R\\$ 4,5 bi e +R\\$ 2,6 bi) e o FCO saltou para "
        "R\\$ 9,9 e R\\$ 9,3 bi.",
        "Em 2025, o IR diferido de R\\$ 1,13 bi (R\\$ 1,04 bi de atualização não recorrente do saldo) reduziu o lucro sem sair caixa.",
        "CAPEX baixo: entre 2,4% e 2,9% da receita líquida desde 2022.",
        "Os juros ficam no fluxo de financiamento, fora do FCO. Por isso o número que importa para o Bloco 4 é o FCL depois "
        "dos juros (R\\$ 2,35 bi em 2025).",
        "**Destaque de transparência:** a norma contábil permite essa classificação, mas ela deixa o FCO difícil de comparar "
        "com o lucro. Melhoria: a B3 poderia divulgar também o FCO sem a movimentação de aplicações.",
    ])
    tabela_fonte([
        ("Lucro líquido", "IS (New Seg) · 59 / DFC · 7", "`lucro_liquido_acionistas`, `lucro_liquido_dfc`"),
        ("FCO", "Cash Flow Statement · 52", "`fco`"),
        ("D&A, IR diferido, juros", "Cash Flow Statement · 9, 12–13, 16",
         "`depreciacao_amortizacao`, `ir_diferido_total_dfc`, `despesas_juros_dfc`"),
        ("Outros ajustes", "Cash Flow Statement · 10–11, 14–15, 17–29", "`outros_ajustes_dfc`"),
        ("Aplicações financeiras", "Cash Flow Statement · 32", "`var_aplicacoes_financeiras`"),
        ("Garantias e custódia", "Cash Flow Statement · 40 e 41", "`var_garantias_recebidas`, `var_proventos_custodia`"),
        ("Capital de giro", "Cash Flow Statement · 31, 33–39, 42–50", "`capital_de_giro_dfc`"),
        ("IR pago", "Cash Flow Statement · 51", "`ir_cs_pago`"),
        ("CAPEX", "Cash Flow Statement · 55 + 59", "`capex_total`"),
    ])

    # ======================================================================================
    # 7. Bloco 4 · Retorno ao acionista
    # ======================================================================================
    cabecalho(
        4, "Retorno ao acionista", "A B3 devolve mais do que lucra, e a diferença saiu da folga de caixa",
        "A B3 devolve ao acionista de 116% a 150% do lucro todo ano. Somando 2021 a 2025, ela pagou R\\$ 28,3 bi, R\\$ 5,4 bi "
        "a mais que o FCL depois dos juros (R\\$ 22,9 bi). A diferença saiu da folga de caixa.",
    )
    v4 = visao("v4")
    if v4 == "Macro":
        partes = (["dividendos_declarados", "jcp_declarados", "recompras_dist"] if regime == "Declarado"
                  else ["proventos_pagos_caixa", "recompra_caixa"])
        df4 = sd.serie(tri, anual, gran, anos, flows=[*partes, "lucro_liquido_acionistas"])
        plot(sc.macro_bloco4(df4, unidade, regime))
        tot = df4[partes].sum(axis=1)
        pay = tot / df4["lucro_liquido_acionistas"]
        completos = ~df4["parcial"]
        st.markdown(
            f"Regime **{regime.lower()}**: a B3 devolveu entre **{pct(pay[completos].min())}** e "
            f"**{pct(pay[completos].max())}** do lucro por período{' (LTM)' if gran == 'LTM' else ''}"
            f"{' (anos fechados)' if gran == 'Anual' else ''}. O traço cinza marca o lucro (100%); o número acima é "
            f"{'o payout' if regime == 'Declarado' else 'o pago ÷ lucro'}."
            + (" No trimestral, proventos e recompras se concentram em alguns trimestres; prefira Anual ou LTM."
               if gran == "Trimestral" else "")
        )
    else:
        st.markdown("**Ponte da folga entre dois trimestres**")
        qs = list(tri["trimestre"])
        q0, q1 = intervalo("De / Até", qs, "4T20", qs[-1], key="p4_intervalo")
        i0, i1 = qs.index(q0), qs.index(q1)
        if i1 <= i0:
            st.info("Escolha um trimestre final posterior ao inicial.")
        else:
            fig4, pas = sc.micro_bloco4_ponte(tri, i0, i1, unidade)
            plot(fig4)
            devolvido = -(pas["Proventos pagos"] + pas["Recompras pagas"])
            st.markdown(
                f"De {q0} a {q1}, o FCL somou **{dinheiro(pas['FCL'], unidade)}** e a B3 devolveu "
                f"**{dinheiro(devolvido, unidade)}** (proventos + recompras pagos), além de "
                f"{dinheiro(-pas['Juros'], unidade)} de juros. A folga foi de {dinheiro(-tri.loc[i0, 'divida_liquida'], unidade)} "
                f"para **{dinheiro(-tri.loc[i1, 'divida_liquida'], unidade)}**."
            )
            st.caption("“Aplicações no FCO” (amarelo) entra porque o caixa total inclui as aplicações e o FCO as desconta: é a "
                       "soma oficial da linha 32 no período, não um ajuste. “Câmbio e outros” é o resíduo que fecha a conta.")

        st.markdown("**Acumulado desde 2021: FCL depois dos juros x devolvido ao acionista (pago)**")
        plot(sc.micro_bloco4_acumulado(anual, unidade))
        a5 = anual[(anual["ano"] >= 2021) & (anual["ano"] <= 2025)]
        st.markdown(
            f"De 2021 a 2025, a B3 gerou **{dinheiro(a5['fcl_pos_juros'].sum(), unidade)}** de FCL depois dos juros e devolveu "
            f"**{dinheiro(a5['retorno_acionista_caixa'].sum(), unidade)}**, "
            f"{dinheiro(a5['retorno_acionista_caixa'].sum() - a5['fcl_pos_juros'].sum(), unidade)} a mais. O acumulado é usado "
            "porque, ano a ano, as aplicações no FCO distorcem a comparação."
        )

    diagnostico([
        "Dividendos caíram de R\\$ 4,1 bi (2020) para zero (2025). Recompras viraram o principal instrumento (R\\$ 2,5 a 3,7 bi por "
        "ano desde 2022). JCP de R\\$ 3,0 bi em 2025, com um extraordinário no 4T25.",
        "Ações em circulação: de 6,0 bi (1T22) para 5,0 bi (2T26), −17% (`acoes_circulacao`).",
        "ROE de 17% para 26%, mais pela queda do PL (R\\$ 24,5 → 17,5 bi) do que pelo lucro.",
        "A Moody's chega a uma leitura parecida: nos 12 meses até o 1T26, o fluxo de caixa livre depois das recompras foi de "
        "apenas R\\$ 137 mi.",
        "Declarado e pago diferem por prazo: em 2021 a B3 declarou R\\$ 6,0 bi e pagou R\\$ 7,4 bi.",
    ])
    tabela_fonte([
        ("Dividendos, JCP, recompras (declarados)", "Distributions & Share Count · 6, 7, 8",
         "`dividendos_declarados`, `jcp_declarados`, `recompras_dist`"),
        ("Payout oficial", "Distributions & Share Count · 10", "`payout_total`"),
        ("Ações em circulação", "Distributions & Share Count · 13", "`acoes_circulacao`"),
        ("Proventos e recompras pagos", "Cash Flow Statement · 78 e 71", "`proventos_pagos_caixa`, `recompra_caixa`"),
        ("Aquisições e outros investimentos", "Cash Flow Statement · 68 − CAPEX", "`aquisicoes_outros_invest`"),
    ])

    # ======================================================================================
    # 8. Diagnóstico de oportunidades
    # ======================================================================================
    cm.cabecalho_secao("Diagnóstico de oportunidades",
                       abertura="**Leitura:** a principal oportunidade a partir de 2026 não é zerar a dívida. É devolver ao "
                                "acionista só o que sobra depois dos juros e deixar o crescimento do EBITDA reduzir a "
                                "alavancagem e melhorar a cobertura de juros.")
    c_forte, c_atencao = st.columns(2)
    with c_forte:
        st.markdown("#### 🟢 Pontos fortes")
        st.markdown(
            "- Caixa maior que a dívida em todos os períodos; alavancagem (1,98x) abaixo do gatilho de 2,5x.\n"
            "- Antes das aplicações, a operação gera mais caixa do que lucro (2025: R\\$ 7,2 bi x R\\$ 4,6 bi), com CAPEX abaixo "
            "de 3% da receita.\n"
            "- Proteção natural contra os juros: caixa e dívida de tamanhos parecidos; cada 1 p.p. de Selic mexe "
            "~R\\$ 150 mi/ano dos dois lados."
        )
    with c_atencao:
        st.markdown("#### 🟡 Pontos de atenção")
        st.markdown(
            "- A folga caiu de R\\$ 10,8 bi (4T20) para R\\$ 4,4 bi (2T26).\n"
            "- De 2021 a 2025, a B3 devolveu R\\$ 5,4 bi a mais que o FCL depois dos juros.\n"
            "- Cobertura de juros (3,7x) abaixo da faixa de 4,0–4,5x da Moody's.\n"
            "- R\\$ 2,6 bi de dívida vencem nos próximos 12 meses."
        )
    a5 = anual[(anual["ano"] >= 2021) & (anual["ano"] <= 2025)]
    devolvido5 = a5["retorno_acionista_caixa"].sum()
    excesso = devolvido5 - a5["fcl_pos_juros"].sum()
    ult = tri.iloc[-1]
    folga0 = -anual.iloc[0]["divida_liquida"]
    rec = anual.set_index("ano")["recompra_caixa"]
    cm.oportunidade(janela, ABA, "Alto", "Devolver só o que o caixa gera",
                    f"De 2021 a 2025, a B3 devolveu R$ {br(devolvido5 / 1e6, 1)} bi aos acionistas: "
                    f"R$ {br(excesso / 1e6, 1)} bi a mais do que sobrou de caixa depois dos juros. Por isso a folga caiu "
                    f"de R$ {br(folga0 / 1e6, 1)} bi para R$ {br(-ult['divida_liquida'] / 1e6, 1)} bi.",
                    f"Limitar dividendos + JCP + recompras ao FCL depois dos juros: cerca de "
                    f"R$ {br(a5['fcl_pos_juros'].mean() / 1e6, 1)} bi por ano (média 2021–2025), e não os "
                    f"R$ {br(devolvido5 / 5 / 1e6, 1)} bi por ano devolvidos.",
                    f"payout LTM {pct(ult['payout_ltm'])}",
                    numero=(pct(ult["payout_ltm"]), f"payout em 12 meses: devolveu R$ {br(ult['payout_ltm'], 2)} "
                                                    f"para cada R$ 1 de lucro"))
    cm.oportunidade(janela, ABA, "Médio", "Cobertura de juros abaixo do esperado",
                    f"Nos 12 meses até o {ult['trimestre']}, o resultado operacional (EBIT) pagou as despesas "
                    f"financeiras {mult(ult['cobertura_ebit_desp_fin_ltm'], 1)}; a Moody's espera 4,0–4,5x.",
                    "Fazer o EBITDA crescer mais que a dívida: +10% de EBITDA leva a alavancagem a ~1,80x; cortar 10% "
                    "de pessoal e TI libera ~R$ 0,22 bi.",
                    numero=(mult(ult["cobertura_ebit_desp_fin_ltm"], 1), "cobertura de juros (Moody's: 4,0–4,5x)"))
    cm.oportunidade(janela, ABA, "Médio", "Dívida que vence em 12 meses",
                    f"R$ {br(ult['divida_bruta_cp'] / 1e6, 1)} bi vencem nos próximos 12 meses; um ano antes eram "
                    f"R$ 0,3 bi.",
                    "Pagar parte com o caixa em vez de rolar tudo: quitar o curto prazo leva a alavancagem de "
                    f"{mult(ult['divida_bruta_ebitda_ltm'])} para ~1,63x. O ganho é de risco; a economia de juros é "
                    "pequena, porque o caixa rende quase o que a dívida custa.",
                    numero=(f"R$ {br(ult['divida_bruta_cp'] / 1e6, 1)} bi", f"vencem até 12 meses após o {ult['trimestre']}"))
    cm.oportunidade(janela, ABA, "Médio", "Recompras maiores que a sobra de caixa",
                    f"Em 2022 e 2024, a B3 pagou R$ {br(rec[2022] / 1e6, 1)} bi e R$ {br(rec[2024] / 1e6, 1)} bi em "
                    "recompras, o maior pagamento ao acionista nesses anos.",
                    "Recomprar ações só com o que sobrar depois de juros, dividendos e JCP.",
                    numero=(f"R$ {br(rec[2024] / 1e6, 1)} bi", "em recompras pagas em 2024"))
    cm.oportunidade(janela, ABA, "Médio", "Transparência da divulgação",
                    f"O FCO inclui a variação das aplicações financeiras (DFC linha 32) e o caixa inclui "
                    f"R$ {br(ult['garantias_recebidas'] / 1e6, 2)} bi de garantias de terceiros.",
                    "Publicar na planilha: FCO sem aplicações, caixa próprio (sem garantias), juros separados do "
                    "principal e a dívida por instrumento.",
                    numero=(f"R$ {br(ult['garantias_recebidas'] / 1e6, 2)} bi",
                            f"de garantias de terceiros dentro do caixa ({ult['trimestre']})"))
    cm.oportunidade(janela, ABA, "Forte", "Caixa maior que a dívida",
                    f"Folga de R$ {br(-ult['divida_liquida'] / 1e6, 1)} bi e alavancagem de "
                    f"{mult(ult['divida_bruta_ebitda_ltm'])} no {ult['trimestre']}, abaixo do gatilho de 2,5x da Moody's.",
                    "Manter a alavancagem abaixo de 2,5x e a devolução dentro do caixa gerado.",
                    numero=(f"R$ {br(-ult['divida_liquida'] / 1e6, 1)} bi", f"de folga de caixa no {ult['trimestre']}"))
    cm.bloco_oportunidades(janela, ABA, titulo="💡 Oportunidades (prescrição 2026–2027)")
    st.markdown("#### 🔎 Pontos de melhoria na divulgação da B3")
    st.caption("Incoerências destacadas, sem corrigir dados.")
    st.markdown(
        "1. FCO com aplicações financeiras (linha 32): divulgar também o FCO sem essa linha.\n"
        "2. Caixa com R\\$ 2,65 bi de garantias de terceiros: separar o caixa próprio na planilha.\n"
        "3. Principal e juros misturados na mesma linha da DFC (75): separar.\n"
        "4. Dívida por instrumento só no PDF do ITR/DFP: incluir o quadro na planilha."
    )
    st.info(
        "**Contraponto:** menos dívida não é automaticamente melhor. Juros são dedutíveis, o JCP reduz o IR e a dívida ajudou "
        "o ROE a ir de 17% para 26%. O ótimo é manter a alavancagem abaixo do gatilho e a devolução dentro do caixa."
    )

    # ======================================================================================
    # 9. Metodologia + dados
    # ======================================================================================
    st.divider()
    with st.expander("Metodologia"):
        st.markdown(
            """
    Nenhum valor da B3 foi ajustado. Todos os indicadores são cálculos padrão sobre as linhas oficiais.

    | Indicador | Cálculo | Linhas |
    |---|---|---|
    | Caixa total | disponibilidades + aplicações CP + aplicações LP | BP 8, 9, 18 |
    | Dívida bruta | dívida CP + dívida LP | BP 43–45, 51–53 |
    | Dívida líquida (folga com sinal trocado) | dívida bruta − caixa total | BP |
    | Alavancagem | dívida bruta ÷ EBITDA recorrente LTM | BP + IS 79 |
    | Cobertura de juros | EBIT ÷ despesas financeiras, LTM | IS 39 e 47 |
    | FCL | FCO − CAPEX | DFC 52, 55, 59 |
    | FCL depois dos juros | FCL − despesas de juros | DFC 16 |
    | Payout | (dividendos + JCP + recompras) ÷ lucro | Proventos 6–8 + IS 59 |

    **Notas**
    - "Despesas de juros" (DFC 16) é o juro reconhecido no ano; o juro pago está misturado com o principal na linha 75.
    - Custo da dívida (~12,2%) e rendimento do caixa (~12,5%) são taxas implícitas: juros ou receitas financeiras ÷ saldo médio do ano.
    - Na ponte da folga, "Aplicações no FCO" é a soma oficial da linha 32 no período; entra para fechar a conta.
    - Faixas do radar: Moody's Local, que usa ajustes próprios; por isso os valores da agência diferem dos nossos.
    - Payout e proventos seguem a competência da B3 (declarado); a comparação com o FCL usa valores pagos (DFC).
    - Diferença conhecida com o módulo de DRE do colega: lá o "EBITDA recorrente" de 2025 aparece como R\\$ 6,63 bi (é o
      "Resultado operacional", IS linha 39) e o lucro como R\\$ 3,58 bi. Aqui usamos IS linhas 79 (R\\$ 6,93 bi) e 59
      (R\\$ 4,59 bi). Decisão do grupo: cada módulo mantém os seus números.
    - Granularidade LTM: colunas `*_ltm` da base; onde a base não traz a coluna LTM (ex.: aplicações, proventos por tipo),
      usa-se a soma dos últimos 4 trimestres das linhas oficiais.

    **Fontes:** [B3 RI · Central de Resultados](https://ri.b3.com.br/pt-br/informacoes-financeiras/central-de-resultados/)
    ("Dados Trimestrais - Nova Segmentação", 2T26: abas Balance Sheet, Cash Flow Statement, Distributions & Share Count,
    IS (New Seg)) · ITR 2T26, nota 9 · [Moody's Local Brasil, relatório de crédito (16/06/2025)](https://moodyslocal.com.br/wp-content/uploads/2025/06/1.2_MLBR_RelatoriodeCredito_B3_16062025_V4.pdf)
    e [comunicado de rating (20/05/2026)](https://moodyslocal.com.br/wp-content/uploads/2026/05/ML-BR-PR-B3-S.A.-%E2%80%93-Brasil-Bolsa-Balcao.pdf).
    """
        )

    with st.expander("Ver dados"):
        st.caption("Valores em R$ mil, como na base oficial. CSV com separador ';' e vírgula decimal.")
        t1, t2 = st.tabs(["Trimestral", "Anual"])
        with t1:
            st.dataframe(tri.drop(columns=["periodo", "parcial"]), hide_index=True, width="stretch")
            st.download_button("⬇️ Baixar CSV trimestral", sd.para_csv(tri.drop(columns=["periodo", "parcial"])),
                               "b3_solidez_trimestral.csv", "text/csv")
        with t2:
            st.dataframe(anual.drop(columns=["parcial"]), hide_index=True, width="stretch")
            st.download_button("⬇️ Baixar CSV anual", sd.para_csv(anual.drop(columns=["parcial"])),
                               "b3_solidez_anual.csv", "text/csv")
