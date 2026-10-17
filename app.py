"""Painel integrado da B3 (PI III): quatro análises em abas + conclusão consolidada.

Rodar:  python -m streamlit run app.py
"""
import streamlit as st

from abas import camila, conclusao, enzo, introducao, joao, victor
from utils import comum as c
from utils import dre

st.set_page_config(page_title="B3 · Painel Integrado", page_icon="📊", layout="wide")
c.aplicar_css()

# ======================================================================================
# Janela de período (igual para todas as abas)
# ======================================================================================
with st.sidebar:
    c.seletor_tema()
    st.divider()
    st.header("📅 Janela de análise")
    anos_opcoes = list(range(2020, 2027))
    rotulo_ano = lambda a: f"{a}*" if a > c.ULTIMO_ANO_FECHADO else str(a)
    ajuda = ("Mesma janela em todas as abas. Análises anuais usam anos fechados (até 2025); 2026* é parcial e entra "
             "até o 2T26 nos gráficos trimestrais e LTM.")
    # Dois jeitos de escolher a mesma janela, sempre sincronizados: intervalo em linha e blocos De/Até.
    # Fonte única: ss["janela"]. Ao mexer em um controle, a versão muda e os dois são recriados com o valor novo.
    ss = st.session_state
    ss.setdefault("janela", (2020, 2026))
    ss.setdefault("janela_versao", 0)
    v = ss["janela_versao"]

    def _da_linha():
        ss["janela"] = tuple(ss[f"janela_linha_{v}"])
        ss["janela_versao"] += 1

    def _dos_blocos():
        de = ss[f"janela_de_{v}"] if ss[f"janela_de_{v}"] is not None else ss["janela"][0]
        ate = ss[f"janela_ate_{v}"] if ss[f"janela_ate_{v}"] is not None else ss["janela"][1]
        ss["janela"] = (min(de, ate), max(de, ate))
        ss["janela_versao"] += 1

    st.select_slider("Período (vale para todas as abas)", options=anos_opcoes, value=ss["janela"],
                     format_func=rotulo_ano, key=f"janela_linha_{v}", on_change=_da_linha, help=ajuda)
    st.segmented_control("De", anos_opcoes, default=ss["janela"][0], format_func=rotulo_ano, key=f"janela_de_{v}",
                         on_change=_dos_blocos)
    st.segmented_control("Até", anos_opcoes, default=ss["janela"][1], format_func=rotulo_ano, key=f"janela_ate_{v}",
                         on_change=_dos_blocos)
    ano_ini, ano_fim = ss["janela"]
    janela = c.Janela(ano_ini, ano_fim)
    st.caption(f"Anos fechados na janela: {janela.anos_fechados[0] if janela.anos_fechados else '—'}–{janela.ano_ref}"
               + (" · 2026 parcial (1T26–2T26)" if janela.inclui_parcial else ""))
    st.divider()
    def _amostra(cor, texto):
        return (f"<div style='display:flex;align-items:center;gap:8px;margin:3px 0;font-size:0.9rem'>"
                f"<span style='width:14px;height:14px;border-radius:3px;background:{cor};flex-shrink:0'></span>"
                f"<span>{texto}</span></div>")

    st.markdown("**Cores de oportunidade**")
    st.markdown("".join(_amostra(c.OPORT[n], f"<b>{n}</b>: {c.OPORT_DESC[n]}") for n in c.ORDEM_NIVEL),
                unsafe_allow_html=True)
    st.markdown("**Status dos alertas** (borda dos cards)")
    st.markdown("".join(_amostra(cor, s) for s, cor in c.STATUS_COR.items()), unsafe_allow_html=True)
    st.divider()
    st.caption("Em cada gráfico: ⛶ tela cheia (canto superior direito) e barra de escala do Plotly (zoom, "
               "autoescala, resetar eixos, baixar PNG). Passe o mouse para ver a explicação de cada termo.")

# ======================================================================================
# Cabeçalho
# ======================================================================================
logo = c.logo_b3()
if logo:
    st.logo(logo, size="large")
    g_logo, g_tit = st.columns([1, 9], vertical_alignment="center")
    g_logo.image(logo, width=110)
    g_tit.title("B3 S.A. — Painel Integrado de Análise")
else:
    st.title("📊 B3 S.A. — Painel Integrado de Análise")
st.caption(f"PI III · Desenvolvimento de mercado, receita, eficiência e solidez financeira da B3 · janela "
           f"{janela.rotulo()} · fontes oficiais da B3 (RI, 2T26) e dados de mercado da B3")
valores, rotulos, _ = dre.carregar_dre()
erros = dre.validar_dre(valores, rotulos)
if erros:
    st.error("Falha na validação da DRE oficial:\n\n" + "\n".join(f"- {e}" for e in erros))

with st.expander("ℹ️ Como ler este painel"):
    st.markdown(c.md(
        "- **Seis abas:** uma visão geral da B3, uma por tema do grupo e uma de **Conclusão**, que consolida as "
        "oportunidades de todas.\n"
        "- **Mesma estrutura em todas:** glossário → indicadores-chave → painel de alertas → seções com gráfico, "
        "leitura, diagnóstico e fonte → oportunidades da aba.\n"
        "- **Cores de oportunidade** (padrão do João): 🟥 alto potencial de melhoria · 🟨 médio · ⬜ baixo · "
        "🟦 efeito contábil · 🟩 ponto forte.\n"
        "- **Janela de período** (padrão do Enzo): definida na barra lateral e aplicada a todas as abas.\n"
        "- **Nenhum valor da B3 foi alterado:** só somas, diferenças e razões sobre as linhas oficiais. Incoerências "
        "aparecem destacadas, não corrigidas."
    ))

abas = st.tabs([
    "🏛️ Visão geral",
    "📈 Desenvolvimento de Mercado · Camila",
    "💰 Receita & Diversificação · Enzo",
    "⚙️ Eficiência & Lucratividade · João",
    "🏦 Solidez Financeira · Victor",
    "🎯 Conclusão",
])
with abas[0]:
    introducao.render(janela)
with abas[1]:
    camila.render(janela)
with abas[2]:
    enzo.render(janela)
with abas[3]:
    joao.render(janela)
with abas[4]:
    victor.render(janela)
with abas[5]:
    conclusao.render(janela)
