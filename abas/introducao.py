"""Aba 0 · Visão geral — contextualização para a apresentação (ficha técnica, ODS, ferramentas e fontes)."""
from pathlib import Path

import streamlit as st

from utils import comum as c
from utils import dre
from utils import solidez_data as sd
from utils.comum import br

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Cores oficiais dos ícones dos ODS (ONU)
ODS = [
    (4, "Educação de qualidade", "#C5192D", "B3 Social e educação financeira para novos investidores."),
    (8, "Trabalho decente e crescimento econômico", "#A21942",
     "Mercado de capitais como fonte de financiamento das empresas (foco da aba da Camila)."),
    (9, "Indústria, inovação e infraestrutura", "#FD6925",
     "Recursos captados na B3 financiam projetos, infraestrutura e inovação (foco da aba da Camila)."),
    (10, "Redução das desigualdades", "#DD1367", "Acesso de pessoas físicas ao investimento."),
    (11, "Cidades e comunidades sustentáveis", "#FD9D24", "CRI e LCI financiam moradia e construção."),
    (13, "Ação contra a mudança global do clima", "#3F7E44", "Índice ICO2 B3 e gestão de emissões."),
]

FICHA = [
    ("Razão social", "B3 S.A. – Brasil, Bolsa, Balcão"),
    ("Código de negociação", "B3SA3 · segmento Novo Mercado (mais alto nível de governança)"),
    ("Sede", "São Paulo (SP)"),
    ("Origem", "Bolsa de São Paulo (1890) → BM&FBOVESPA (2008) → B3, após a combinação com a Cetip (2017)"),
    ("CNAE", "6611-8/01 · Bolsa de valores"),
    ("O que faz", "Única bolsa do país: negociação, compensação (clearing), depósito e custódia, registro de "
                  "balcão, dados e tecnologia para o mercado financeiro"),
    ("Modelo de receita", "Tarifas por volume negociado e registrado (Mercados) e receitas recorrentes de dados, "
                          "tecnologia, listagem e depositária"),
]

FERRAMENTAS = [
    ("🐍", "Python 3.12", "Linguagem de toda a coleta, tratamento e análise"),
    ("🐼", "pandas / openpyxl", "Leitura das planilhas da B3 e cálculos (somas, razões, LTM)"),
    ("📊", "Plotly", "Gráficos interativos com zoom, autoescala e tela cheia"),
    ("🎈", "Streamlit", "Painel web com abas, filtros e glossário"),
    ("🐙", "Git e GitHub", "Versionamento e trabalho em paralelo do grupo"),
    ("🎨", "Canva", "Apresentações das sprints"),
    ("🤖", "Claude Code", "Apoio na integração das quatro análises e na padronização do painel"),
]

FONTES = [
    ("B3 · Relações com Investidores", "Central de Resultados: “Dados Trimestrais – Nova Segmentação” (2T26) e ITR 2T26",
     "https://ri.b3.com.br/pt-br/informacoes-financeiras/central-de-resultados/"),
    ("B3 · dados de mercado", "Pessoas físicas em renda variável, emissões corporativas, estoque de renda fixa bancária",
     "https://www.b3.com.br/pt_br/noticias/"),
    ("Moody's Local Brasil", "Relatório de crédito e comunicado de rating da B3 (faixas de alavancagem e cobertura)",
     "https://moodyslocal.com.br/"),
    ("Banco Central do Brasil", "Histórico da taxa Selic (Copom)", "https://www.bcb.gov.br/controleinflacao/historicotaxasjuros"),
    ("Imprensa e consultorias de mercado", "Séries de IPOs e valor de mercado dos bancos (citadas na aba da Camila)", ""),
]

ABAS = [
    ("📈", "Desenvolvimento de Mercado, Impacto Econômico & ODS", "Camila",
     "Como evoluíram investidores, custódia, emissões, IPOs e o crédito imobiliário e do agro?"),
    ("💰", "Receita, Diversificação & Apetite por Produtos", "Enzo",
     "De onde vem a receita da B3 e quanto ela depende do mercado de ações?"),
    ("⚙️", "Eficiência Operacional, Custos e Lucratividade", "João",
     "Quanto da receita vira lucro e quais custos têm espaço para melhorar?"),
    ("🏦", "Solidez Financeira, Endividamento e Geração de Valor", "Victor",
     "A B3 é sólida e o caixa que gera volta ao acionista de forma sustentável?"),
    ("🎯", "Conclusão", "Grupo", "Quais são as oportunidades prioritárias, somando as quatro análises?"),
]


def _logo():
    """Logo da B3, se o arquivo estiver em data/ (logo_b3.svg ou logo_b3.png)."""
    for nome in ("logo_b3.svg", "logo_b3.png"):
        caminho = DATA_DIR / nome
        if caminho.exists():
            return caminho
    return None


def render(janela):
    logo = _logo()
    if logo:
        g_logo, g_tit = st.columns([1, 6], vertical_alignment="center")
        g_logo.image(str(logo), width=120)
        with g_tit:
            st.markdown("## Visão geral: B3 S.A. — Brasil, Bolsa, Balcão")
    else:
        st.markdown("## 🏛️ Visão geral: B3 S.A. — Brasil, Bolsa, Balcão")
    st.caption("Contextualização da Sprint 2: quem é a empresa, que ODS ela toca e com que ferramentas e fontes o "
               "grupo trabalhou.")

    # ---------------------------------------------------------------- Ficha técnica
    st.markdown("### 📋 Ficha técnica")
    g1, g2 = st.columns([3, 2])
    with g1:
        st.markdown(c.md("\n".join(f"- **{k}:** {v}" for k, v in FICHA)))
    with g2:
        valores, _, _ = dre.carregar_dre()
        a = dre.anual(valores, [2025]).loc[2025]
        tri, _ = sd.load()
        u = tri.iloc[-1]
        c.kpis([
            dict(rotulo="Receita bruta 2025", valor=c.bi(a["receita_total"], 1, md=False), termo="Receita bruta"),
            dict(rotulo="Lucro líquido 2025", valor=c.bi(a["lucro"], 1, md=False), termo="Lucro líquido"),
            dict(rotulo="EBITDA recorrente 2025", valor=c.bi(a["ebitda_recorrente"], 1, md=False),
                 termo="EBITDA recorrente"),
            dict(rotulo=f"Caixa total ({u['trimestre']})", valor=c.bi(u["caixa_total"], 1, md=False), termo="Caixa total"),
        ], colunas=2)
        st.caption("Fonte: planilha oficial da B3 (RI), 2T26.")

    # ---------------------------------------------------------------- ODS
    st.markdown("### 🌍 ODS impactados")
    st.caption("Objetivos de Desenvolvimento Sustentável da ONU ligados à atuação da B3. A aba da Camila explora os "
               "ODS 8 e 9 com dados.")
    cols = st.columns(len(ODS))
    for col, (n, nome, cor, porque) in zip(cols, ODS):
        col.markdown(
            f"<div title=\"{porque}\" style='background:{cor};color:white;border-radius:10px;padding:10px;"
            f"height:150px;cursor:help;display:flex;flex-direction:column;justify-content:space-between'>"
            f"<div style='font-size:2.1rem;font-weight:800;line-height:1'>{n}</div>"
            f"<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;line-height:1.15'>{nome}</div></div>"
            f"<div style='font-size:0.78rem;margin-top:6px;line-height:1.25'>{porque}</div>",
            unsafe_allow_html=True)

    # ---------------------------------------------------------------- Estrutura do painel
    st.markdown("### 🧭 Como o painel está organizado")
    for emoji, tema, quem, pergunta in ABAS:
        st.markdown(c.md(f"{emoji} **{tema}** · {quem} — _{pergunta}_"))

    # ---------------------------------------------------------------- Ferramentas e fontes
    f1, f2 = st.columns(2)
    with f1:
        st.markdown("### 🛠️ Ferramentas")
        for emoji, nome, uso in FERRAMENTAS:
            st.markdown(f"{emoji} **{nome}** — {uso}")
    with f2:
        st.markdown("### 📚 Fontes de dados")
        for nome, conteudo, url in FONTES:
            link = f" · [acessar]({url})" if url else ""
            st.markdown(c.md(f"**{nome}** — {conteudo}{link}"))
        st.caption("Regra do grupo: nenhum valor da B3 é alterado; incoerências são destacadas, não corrigidas.")
