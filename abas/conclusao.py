"""Aba 5 · Conclusão — consolidação dos diagnósticos de oportunidades das quatro abas."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import comum as c
from utils import dre
from utils import solidez_data as sd
from utils.comum import br, pct

ABAS = ["Camila · Desenvolvimento de Mercado", "Enzo · Receita & Diversificação",
        "João · Eficiência & Lucratividade", "Victor · Solidez Financeira"]
NIVEIS_OP = ["Alto", "Médio", "Baixo", "Forte"]


def _numeros(janela):
    """Números-chave de cada aba para a leitura integrada (mesma janela)."""
    valores, _, _ = dre.carregar_dre()
    fechados = janela.anos_fechados or [janela.ano_ref]  # janela só com 2026: usa o último ano fechado
    ini, fim = fechados[0], fechados[-1]
    a = dre.anual(valores, sorted({ini, fim}))
    tri, _ = sd.load()
    u = tri[tri["ano"] <= janela.ano_fim].iloc[-1]
    from abas.camila import DADOS
    cam = DADOS[(DADOS["ano"] >= ini) & (DADOS["ano"] <= fim)]
    return dict(
        ini=ini, fim=fim,
        inv_ini=cam["investidores"].iloc[0], inv_fim=cam["investidores"].iloc[-1],
        rv_peso_ini=a.loc[ini, "renda_variavel"] / a.loc[ini, "receita_total"],
        rv_peso_fim=a.loc[fim, "renda_variavel"] / a.loc[fim, "receita_total"],
        rb_var=c.var(a.loc[fim, "receita_total"], a.loc[ini, "receita_total"]),
        mg_ini=a.loc[ini, "ebitda_recorrente"] / a.loc[ini, "receita_liquida"],
        mg_fim=a.loc[fim, "ebitda_recorrente"] / a.loc[fim, "receita_liquida"],
        alav=u["divida_bruta_ebitda_ltm"], cobertura=u["cobertura_ebit_desp_fin_ltm"], payout=u["payout_ltm"],
        folga=-u["divida_liquida"], per=u["trimestre"],
    )


def render(janela):
    st.markdown("## 🎯 Conclusão: consolidação dos diagnósticos de oportunidades")
    st.caption("Junta, numa só visão, as oportunidades que cada aba identificou na mesma janela de período "
               f"({janela.rotulo()}). As cores seguem o padrão do painel.")
    c.glossario("todas", titulo="📖 Glossário completo do painel")

    ops = pd.DataFrame(janela.oportunidades)
    if ops.empty:
        st.warning("Nenhuma oportunidade foi registrada na janela escolhida. Amplie a janela de anos.")
        return

    # ---------------------------------------------------------------- Indicadores-chave
    cont = ops["nivel"].value_counts()
    c.kpis([
        dict(rotulo="Oportunidades mapeadas", valor=str(int((ops["nivel"] != "Forte").sum())),
             ajuda="Itens com potencial de melhoria (Alto, Médio ou Baixo) somando as quatro abas."),
        dict(rotulo="🟥 Prioridade alta", valor=str(int(cont.get("Alto", 0))), ajuda=c.OPORT_DESC["Alto"]),
        dict(rotulo="🟨 Prioridade média", valor=str(int(cont.get("Médio", 0))), ajuda=c.OPORT_DESC["Médio"]),
        dict(rotulo="🟩 Pontos fortes", valor=str(int(cont.get("Forte", 0))), ajuda=c.OPORT_DESC["Forte"]),
    ])

    # ---------------------------------------------------------------- Leitura integrada
    n = _numeros(janela)
    c.cabecalho_secao("A história em uma frase",
                      "A B3 diversificou a receita e segue sólida, mas está devolvendo mais caixa do que gera e "
                      "perdendo margem; a prioridade é eficiência e disciplina de capital")
    c.leitura(
        f"<b>Mercado (Camila):</b> a base de investidores foi de {br(n['inv_ini'], 1)} para {br(n['inv_fim'], 1)} milhões "
        f"({n['ini']}–{n['fim']}), mas cresce devagar desde 2022.<br>"
        f"<b>Receita (Enzo):</b> a receita bruta variou {pct(n['rb_var'], 1, sinal=True)} e a Renda Variável caiu de "
        f"{pct(n['rv_peso_ini'], 1)} para {pct(n['rv_peso_fim'], 1)} da receita: o modelo ficou menos dependente do "
        "volume de ações.<br>"
        f"<b>Eficiência (João):</b> a margem EBITDA recorrente foi de {pct(n['mg_ini'], 1)} para {pct(n['mg_fim'], 1)}: "
        "os custos (pessoal e TI) cresceram mais que a receita.<br>"
        f"<b>Solidez (Victor):</b> no {n['per']}, alavancagem de {br(n['alav'], 2)}x (abaixo do gatilho de 2,5x) e folga "
        f"de R$ {br(n['folga'] / 1e6, 1)} bi, mas payout de {pct(n['payout'], 0)} e cobertura de juros de "
        f"{br(n['cobertura'], 1)}x, abaixo da faixa da Moody's.")
    c.diagnostico([
        "**Mesma causa em duas abas:** a base de investidores estagnada (Camila) e a receita de Renda Variável em queda "
        "(Enzo) refletem o mercado de ações mais fraco; a diversificação compensou na receita, não no volume.",
        "**Efeito encadeado:** a margem menor (João) reduz o EBITDA que paga os juros, e por isso a cobertura de juros "
        "ficou abaixo da faixa da Moody's (Victor).",
        "**Ponto de equilíbrio:** a B3 tem caixa maior que a dívida, mas a devolução acima do FCL depois dos juros está "
        "consumindo essa folga.",
    ], titulo="🔍 Diagnóstico integrado")

    # ---------------------------------------------------------------- Mapa de oportunidades
    c.cabecalho_secao("Mapa de oportunidades por aba", abertura="Quantidade de itens por aba e por nível de prioridade.")
    tab = ops.pivot_table(index="aba", columns="nivel", values="tema", aggfunc="count", fill_value=0)
    tab = tab.reindex(index=[a for a in ABAS if a in tab.index][::-1],
                      columns=[x for x in NIVEIS_OP if x in tab.columns], fill_value=0)
    fig = go.Figure()
    for nivel in tab.columns:
        temas = [", ".join(ops[(ops["aba"] == a) & (ops["nivel"] == nivel)]["tema"]) for a in tab.index]
        fig.add_bar(y=tab.index, x=tab[nivel], name=f"{nivel}: {c.OPORT_DESC[nivel]}", orientation="h",
                    marker_color=c.cor_oport(nivel), text=[str(v) if v else "" for v in tab[nivel]],
                    textposition="inside", customdata=temas,
                    hovertemplate="<b>%{y}</b><br>" + nivel + ": %{x}<br>%{customdata}<extra></extra>")
    fig.update_layout(barmode="stack")
    c.layout_base(fig, altura=360, legenda=True)
    fig.update_xaxes(title_text="Quantidade de itens", dtick=1)
    fig.update_yaxes(type="category")
    c.mostrar_grafico(fig, key="conc_mapa")
    alto_por_aba = ops[ops["nivel"] == "Alto"]["aba"].value_counts()
    if not alto_por_aba.empty:
        c.leitura(f"A aba com mais itens de prioridade alta é <b>{alto_por_aba.index[0]}</b> "
                  f"({alto_por_aba.iloc[0]} item(ns)).")

    # ---------------------------------------------------------------- Lista consolidada
    c.cabecalho_secao("Oportunidades consolidadas", abertura="Filtre por aba ou por nível. Cada item traz o diagnóstico, "
                                                             "a ação proposta e a evidência numérica.")
    f1, f2 = st.columns(2)
    abas_sel = f1.multiselect("Abas", ABAS, default=ABAS, key="conc_abas")
    niv_sel = f2.multiselect("Níveis", NIVEIS_OP, default=NIVEIS_OP, key="conc_niveis",
                             format_func=lambda x: f"{c.OPORT_EMOJI[x]} {x}")
    filtrado = ops[ops["aba"].isin(abas_sel) & ops["nivel"].isin(niv_sel)]
    for nivel in NIVEIS_OP:
        grupo = filtrado[filtrado["nivel"] == nivel]
        if grupo.empty:
            continue
        st.markdown(f"#### {c.OPORT_EMOJI[nivel]} {nivel} — {c.OPORT_DESC[nivel]} ({len(grupo)})")
        for _, o in grupo.iterrows():
            ev = f" <span style='opacity:.7'>({o['evidencia']})</span>" if o["evidencia"] else ""
            corpo = (f"<b>{o['tema']}</b> · <span style='opacity:.75'>{o['aba']}</span>{ev}<br>{o['diagnostico']}"
                     f"<br><b>Ação:</b> {o['acao']}")
            st.markdown(f"<div class='oport' style='border-left:5px solid {c.cor_oport(nivel)}'>"
                        f"{c.sem_escape(corpo)}</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------- Prescrição integrada
    c.cabecalho_secao("Prescrição integrada 2026–2027", abertura="As ações de prioridade alta, em ordem de execução.")
    st.markdown(c.md(
        "1. **Eficiência primeiro (João):** renegociar TI e serviços de terceiros e conter pessoal abaixo do crescimento "
        "da receita. Recupera margem e melhora a cobertura de juros (Victor).\n"
        "2. **Disciplina de capital (Victor):** devolver ao acionista no máximo o FCL depois dos juros, no acumulado de "
        "vários anos, e recomprar só com sobra de caixa. Preserva a folga.\n"
        "3. **Proteger a receita do ciclo de ações (Enzo):** seguir crescendo em Renda Fixa e Crédito e Dados/Tecnologia, "
        "com atenção à margem dessas linhas, e estimular volume em Renda Variável.\n"
        "4. **Ampliar o mercado (Camila):** retomar a entrada de investidores pessoa física e destravar instrumentos em "
        "queda (CRI), reforçando o papel da B3 no financiamento das empresas (ODS 8 e 9).\n"
        "5. **Transparência (Victor e Camila):** divulgar FCO sem aplicações, caixa próprio, dívida por instrumento e "
        "séries de emissões consistentes."
    ))
    c.fonte([("Oportunidades", "Abas da Camila, do Enzo, do João e do Victor", "Registradas por cada aba na mesma janela"),
             ("Números da leitura integrada", "DRE IS (New Seg), base de solidez do Victor e dados da Camila",
              "Recalculados para a janela escolhida")],
            nota="Os níveis de prioridade seguem as regras de cada aba (variação no tempo, critério de custo do João e "
                 "faixas da Moody's no Victor).")

    with st.expander("⬇️ Exportar oportunidades"):
        st.dataframe(ops.rename(columns={"aba": "Aba", "nivel": "Nível", "tema": "Tema", "diagnostico": "Diagnóstico",
                                         "acao": "Ação", "evidencia": "Evidência"}), hide_index=True, width="stretch")
        st.download_button("⬇️ Baixar CSV", ops.to_csv(index=False, sep=";").encode("utf-8-sig"),
                           "b3_oportunidades_consolidadas.csv", "text/csv", key="conc_csv")
