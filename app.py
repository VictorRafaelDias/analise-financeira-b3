"""Painel integrado da B3 (PI III): quatro análises em abas + conclusão consolidada.

Rodar:  python -m streamlit run app.py
"""
import importlib
import os

import streamlit as st

import abas.camila_mercado
import utils.comum
import utils.dre
import utils.solidez_charts
import utils.solidez_data
from abas import camila, conclusao, enzo, introducao, joao, victor

# O Streamlit relê o app.py a cada atualização, mas guarda os módulos importados na memória (no Streamlit Cloud,
# isso deixava o app.py novo chamando funções que a versão antiga de utils/comum.py não tinha). Aqui cada módulo
# do painel é recarregado quando o arquivo dele muda; utils antes de abas, porque as abas dependem deles.
_MODULOS = [utils.comum, utils.dre, utils.solidez_data, utils.solidez_charts, abas.camila_mercado,
            camila, enzo, joao, victor, introducao, conclusao]


@st.cache_resource
def _versoes_modulos():
    return {}


_versoes = _versoes_modulos()
for _m in _MODULOS:
    _mtime = os.path.getmtime(_m.__file__)
    if _versoes.get(_m.__name__) != _mtime:
        importlib.reload(_m)  # primeira execução do processo ou arquivo alterado
        _versoes[_m.__name__] = _mtime

from utils import comum as c  # noqa: E402  (depois do recarregamento)
from utils import dre  # noqa: E402

st.set_page_config(page_title="B3 · Painel Integrado", page_icon="📊", layout="wide")
c.aplicar_css()

# ======================================================================================
# Versão do painel: escolhida na abertura (ou pelo link ?versao=) e trocada na barra lateral
# ======================================================================================
VERSOES = {"completo": "Completo", "simplificado": "Simplificado"}
ss = st.session_state
if "versao" not in ss and st.query_params.get("versao") in VERSOES:
    ss["versao"] = st.query_params["versao"]


def _escolher(versao):
    ss["versao"] = versao
    st.query_params["versao"] = versao


if "versao" not in ss:
    logo = c.logo_b3()
    if logo:
        st.image(logo, width=130)
    st.title("B3 S.A. — Painel Integrado de Análise")
    st.markdown("#### Qual versão você quer abrir?")
    v1, v2 = st.columns(2)
    with v1, st.container(border=True):
        st.markdown("### 📘 Completo")
        st.markdown("Todas as seções das quatro análises, com gráficos de detalhe, IPOs, emissões, bancos, ritmo "
                    "trimestral, conversão de caixa e retorno ao acionista.")
        st.caption("Ordem: Visão geral → Desenvolvimento de Mercado → Receita → Eficiência → Solidez → Conclusão")
        st.button("Abrir o completo", key="abrir_completo", width="stretch", on_click=_escolher, args=("completo",))
    with v2, st.container(border=True):
        st.markdown("### 📗 Simplificado")
        st.markdown("Só as seções principais de cada análise, para uma apresentação mais curta e direta.")
        st.caption("Ordem: Visão geral → Solidez → Receita → Eficiência → Desenvolvimento de Mercado → Conclusão")
        st.button("Abrir o simplificado", key="abrir_simplificado", type="primary", width="stretch",
                  on_click=_escolher, args=("simplificado",))
    st.stop()
st.query_params["versao"] = ss["versao"]
SIMPLES = ss["versao"] == "simplificado"

# ======================================================================================
# Janela de período (igual para todas as abas)
# ======================================================================================
with st.sidebar:
    ss.setdefault("versao_ver", 0)

    def _troca_versao():
        escolha = ss.get(f"versao_ctrl_{ss['versao_ver']}")
        if escolha:
            _escolher(escolha)
        ss["versao_ver"] += 1

    st.segmented_control("🧭 Versão do painel", list(VERSOES), default=ss["versao"], format_func=VERSOES.get,
                         key=f"versao_ctrl_{ss['versao_ver']}", on_change=_troca_versao,
                         help="Simplificado: só as seções principais de cada aba e a ordem da apresentação "
                              "(Solidez primeiro). Completo: todas as seções.")
    c.seletor_tema()
    st.divider()
    st.header("📅 Janela de análise")
    anos_opcoes = list(range(2020, 2027))
    rotulo_ano = lambda a: f"{a}*" if a > c.ULTIMO_ANO_FECHADO else str(a)
    ajuda = ("Mesma janela em todas as abas. Análises anuais usam anos fechados (até 2025); 2026* é parcial e entra "
             "até o 2T26 nos gráficos trimestrais e LTM.")
    # Dois jeitos de escolher a mesma janela, sempre sincronizados: intervalo em linha e blocos De/Até.
    # Fonte única: ss["janela"]. Ao mexer em um controle, a versão muda e os dois são recriados com o valor novo.
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
    janela = c.Janela(ano_ini, ano_fim, simples=SIMPLES)
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
st.caption(f"PI III · {'Versão simplificada' if SIMPLES else 'Versão completa'} · janela {janela.rotulo()} · "
           "fontes oficiais da B3 (RI, 2T26) e dados de mercado da B3")
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
        "- **Cores de oportunidade:** 🟥 alto potencial de melhoria · 🟨 médio · ⬜ baixo · "
        "🟦 efeito contábil · 🟩 ponto forte.\n"
        "- **Janela de período:** definida na barra lateral e aplicada a todas as abas.\n"
        "- **Nenhum valor da B3 foi alterado:** só somas, diferenças e razões sobre as linhas oficiais. Incoerências "
        "aparecem destacadas, não corrigidas."
    ))

ABAS = {
    "introducao": ("🏛️ Visão geral", introducao),
    "camila": ("📈 Desenvolvimento de Mercado", camila),
    "enzo": ("💰 Receita & Diversificação", enzo),
    "joao": ("⚙️ Eficiência & Lucratividade", joao),
    "victor": ("🏦 Solidez Financeira", victor),
    "conclusao": ("🎯 Conclusão", conclusao),
}
# A Conclusão fica sempre por último: ela lê as oportunidades registradas pelas outras abas.
ORDEM = (["introducao", "victor", "enzo", "joao", "camila", "conclusao"] if SIMPLES
         else ["introducao", "camila", "enzo", "joao", "victor", "conclusao"])
for aba, chave in zip(st.tabs([ABAS[k][0] for k in ORDEM]), ORDEM):
    with aba:
        ABAS[chave][1].render(janela)
