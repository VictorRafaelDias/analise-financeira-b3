"""Padrões compartilhados por todas as abas do painel integrado.

Cada padrão pedido pelo grupo tem uma função aqui, para que as quatro abas fiquem iguais:

- explicação ao passar o mouse ........ GLOSSARIO, explica(), dica()      (padrão do João)
- cor por potencial de oportunidade .... OPORT, cor_oport(), legenda_oportunidade() (João)
- tela cheia em cada gráfico ........... mostrar_grafico()                (Enzo)
- opções de escala (zoom/autoescala) ... mostrar_grafico()                (Enzo)
- glossário ............................ glossario()                      (João)
- painel de alerta ..................... painel_alertas()                 (João e Victor)
- janela de período igual .............. Janela + barra lateral do app.py (Enzo)
- indicadores-chave .................... kpis()                           (Camila)
- bloco de diagnóstico e fonte ......... diagnostico(), fonte()           (Victor)
"""
import html
import re
import textwrap
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import streamlit as st

# ======================================================================================
# Janela de período (igual para todas as abas)
# ======================================================================================
ULTIMO_ANO_FECHADO = 2025
ULTIMO_TRIMESTRE = "2T26"


@dataclass
class Janela:
    """Janela global escolhida na barra lateral."""
    ano_ini: int
    ano_fim: int
    oportunidades: list = field(default_factory=list)  # preenchida pelas abas, lida na Conclusão

    @property
    def anos(self):
        return (self.ano_ini, self.ano_fim)

    @property
    def ano_ref(self):
        """Último ano fechado dentro da janela (análises anuais)."""
        return min(self.ano_fim, ULTIMO_ANO_FECHADO)

    @property
    def anos_fechados(self):
        return list(range(self.ano_ini, self.ano_ref + 1))

    @property
    def inclui_parcial(self):
        return self.ano_fim > ULTIMO_ANO_FECHADO

    def rotulo(self):
        fim = f"{self.ano_fim} (1S)" if self.inclui_parcial else str(self.ano_fim)
        return f"{self.ano_ini}–{fim}" if self.ano_ini != self.ano_fim else fim


def aviso_parcial(janela, extra=""):
    if janela.inclui_parcial:
        st.caption(f"ℹ️ 2026 ainda é parcial (até o {ULTIMO_TRIMESTRE}): as análises anuais desta aba vão até "
                   f"{ULTIMO_ANO_FECHADO}{extra}.")


# ======================================================================================
# Paleta e cores de oportunidade
# ======================================================================================
AZUL = "#1F5FAD"
AZUL_CLARO = "#8DB6E6"
CINZA = "#9AA3AE"
CINZA_CLARO = "#C5CBD3"
CINZA_ESCURO = "#4B5563"
VERDE = "#2E9E5B"
VERMELHO = "#D64545"
ROXO = "#7B5EA7"
LARANJA = "#F58518"

# Potencial de oportunidade de melhoria (padrão do João, aplicado a todas as abas)
OPORT = {
    "Alto": "#E4572E",    # maior potencial de melhoria / prioridade
    "Médio": "#F2B134",   # melhoria possível
    "Baixo": "#9AA5B1",   # estrutural, pouco espaço
    "Nulo": "#6C8EBF",    # efeito contábil, sem saída de caixa
    "Forte": "#2CA02C",   # ponto forte / benefício
}
OPORT_DESC = {
    "Alto": "alto potencial de melhoria",
    "Médio": "potencial médio",
    "Baixo": "baixo potencial (estrutural)",
    "Nulo": "efeito contábil, sem caixa",
    "Forte": "ponto forte / benefício",
}
OPORT_EMOJI = {"Alto": "🟥", "Médio": "🟨", "Baixo": "⬜", "Nulo": "🟦", "Forte": "🟩"}
ORDEM_NIVEL = ["Alto", "Médio", "Baixo", "Nulo", "Forte"]


def cor_oport(nivel):
    return OPORT.get(nivel, CINZA)


def nivel_por_variacao(v, forte=0.05):
    """Regra única para séries no tempo: queda = Alto, crescimento abaixo de `forte` = Médio, acima = Forte."""
    if v is None or pd.isna(v):
        return "Baixo"
    if v < 0:
        return "Alto"
    return "Médio" if v < forte else "Forte"


def legenda_oportunidade(niveis=("Alto", "Médio", "Baixo", "Nulo", "Forte")):
    partes = [
        f"<span style='display:inline-flex;align-items:center;gap:5px;margin-right:14px'>"
        f"<span style='width:12px;height:12px;border-radius:3px;background:{OPORT[n]};display:inline-block'></span>"
        f"<span style='font-size:0.8rem'>{n}: {OPORT_DESC[n]}</span></span>"
        for n in niveis
    ]
    st.markdown("<div style='margin:2px 0 8px 0'><span style='font-size:0.8rem;font-weight:600;margin-right:8px'>"
                "Cores de oportunidade:</span>" + "".join(partes) + "</div>", unsafe_allow_html=True)


# ======================================================================================
# Glossário único (explicação ao passar o mouse + expansor de glossário)
# ======================================================================================
# termo -> (explicação, abas onde aparece)
GLOSSARIO = {
    # --- Geral
    "B3": ("Empresa que oferece a infraestrutura de negociação, registro e depósito de ativos do mercado "
           "brasileiro (bolsa e balcão).", {"geral", "camila"}),
    "Balanço Patrimonial (BP)": ("Foto do que a empresa tem e deve em uma data.", {"victor"}),
    "Fluxo de Caixa (DFC)": ("Extrato de por onde o dinheiro entrou e saiu no período.", {"victor"}),
    "DRE": ("Demonstração do resultado: o 'filme' de receitas, custos e lucro do período.",
            {"enzo", "joao", "victor"}),
    "LTM": ("Soma dos últimos 12 meses (4 trimestres).", {"victor"}),
    "CAGR": ("Crescimento médio composto por ano entre o primeiro e o último ano da janela.", {"enzo", "camila"}),
    "p.p.": ("Pontos percentuais: diferença entre duas porcentagens (ex.: de 70% para 68% = −2 p.p.).",
             {"enzo", "joao", "victor"}),
    # --- Camila
    "Investidores em renda variável": ("Pessoas físicas (CPFs) com posição em ativos de retorno variável, como "
                                       "ações e fundos imobiliários, no fim do ano.", {"camila"}),
    "Valor em custódia": ("Valor dos ativos de pessoas físicas guardados na B3 numa data. É uma posição (saldo), "
                          "não dinheiro em conta, e não se soma entre anos.", {"camila"}),
    "Custódia por investidor": ("Valor em custódia ÷ número de investidores: o tamanho médio da carteira.",
                                {"camila"}),
    "Emissões de dívida corporativa": ("Recursos captados por empresas ao emitir títulos de dívida no mercado de "
                                       "capitais no ano (fluxo).", {"camila"}),
    "Debêntures": ("Títulos de dívida emitidos por empresas para captar recursos de investidores.",
                   {"camila", "victor"}),
    "CRI": ("Certificado de Recebíveis Imobiliários: renda fixa lastreada em créditos imobiliários.", {"camila"}),
    "CRA": ("Certificado de Recebíveis do Agronegócio: renda fixa lastreada em créditos do agronegócio.",
            {"camila"}),
    "Notas comerciais": ("Títulos de dívida de curto ou médio prazo emitidos por empresas.", {"camila"}),
    "IPO": ("Oferta pública inicial: quando uma empresa vende ações na bolsa pela primeira vez para captar recursos.",
            {"camila", "geral"}),
    "Follow-on": ("Nova oferta de ações de uma empresa que já está listada.", {"camila"}),
    "Selic": ("Taxa básica de juros da economia, definida pelo Copom do Banco Central.", {"camila", "victor"}),
    "LCI": ("Letra de Crédito Imobiliário: título emitido por banco, lastreado em crédito imobiliário; isento de IR para "
            "pessoa física e coberto pelo FGC.", {"camila"}),
    "LCA": ("Letra de Crédito do Agronegócio: título emitido por banco, lastreado em crédito ao agro; isento de IR para "
            "pessoa física e coberto pelo FGC.", {"camila"}),
    "CDB": ("Certificado de Depósito Bancário: principal título de captação dos bancos, registrado na B3.", {"camila"}),
    "Letra Financeira": ("Título de longo prazo emitido por bancos, para investidores maiores, registrado na B3.",
                         {"camila"}),
    "FGC": ("Fundo Garantidor de Créditos: garante até R$ 250 mil por CPF por instituição em CDB, LCI e LCA.",
            {"camila"}),
    "Valor de mercado": ("Preço da ação x quantidade de ações: quanto a bolsa diz que a empresa vale naquele dia.",
                         {"camila"}),
    "ODS": ("Objetivos de Desenvolvimento Sustentável da ONU (ex.: ODS 8 trabalho e crescimento; ODS 9 indústria, "
            "inovação e infraestrutura).", {"camila"}),
    "ASG": ("Critérios ambientais, sociais e de governança (ESG, em inglês).", {"camila"}),
    # --- Enzo
    "Receita bruta": ("Tudo o que a B3 faturou com seus serviços (negociação, depósito, dados etc.), antes de "
                      "descontar impostos. Na planilha da B3 é a 'Receita total'.", {"enzo", "joao"}),
    "Receita líquida": ("Receita bruta menos os impostos sobre o faturamento (PIS/Cofins e ISS). É a base das "
                        "margens.", {"enzo", "joao", "victor"}),
    "Deduções da receita": ("Impostos sobre o faturamento (PIS/Cofins e ISS) que reduzem a receita bruta.",
                            {"enzo", "joao"}),
    "Mercados": ("Segmento de negociação e pós-negociação: derivativos, renda variável, renda fixa e crédito e "
                 "empréstimo de ativos.", {"enzo"}),
    "Renda Variável": ("Receita com negociação e pós-negociação de ações e fundos listados. Depende do volume "
                       "negociado na bolsa (ADTV).", {"enzo"}),
    "Derivativos": ("Receita com contratos futuros, opções e swaps (juros, câmbio, índices).", {"enzo"}),
    "Renda Fixa e Crédito": ("Receita com registro e negociação de títulos de renda fixa (debêntures, CRI, CRA, "
                             "CDB etc.) e operações de crédito.", {"enzo"}),
    "Soluções para Mercado de Capitais": ("Dados de mercado, depositária e listagem de emissores.", {"enzo"}),
    "Soluções Analíticas de Dados": ("Veículos e imobiliário, plataformas e dados analíticos (ex.: Neoway).",
                                     {"enzo"}),
    "Tecnologia": ("Receita com tecnologia e plataformas vendidas ao mercado (ex.: balcão, acesso).", {"enzo"}),
    "Serviços de Apoio ao Mercado": ("Serviços acessórios prestados aos participantes do mercado.", {"enzo"}),
    "Outras receitas": ("Reversão de provisões e recuperação de despesas lançadas como receita: efeito contábil, "
                        "não recorrente.", {"enzo"}),
    "Outros": ("Demais receitas de tecnologia e plataformas que não entram nos outros grupos.", {"enzo"}),
    "Receita fora de Renda Variável": ("Parte da receita que não depende do volume de ações negociado. Quanto maior, "
                                       "mais diversificado e menos volátil é o modelo.", {"enzo"}),
    "ADTV": ("Volume financeiro médio diário negociado. Não consta na DRE; a receita de Renda Variável é usada "
             "como referência.", {"enzo"}),
    "Margem EBITDA": ("EBITDA ÷ receita líquida: de cada R$ 100 de receita líquida, quanto vira resultado da "
                      "operação antes de D&A.", {"enzo", "joao"}),
    "Margem líquida": ("Lucro líquido ÷ receita líquida: de cada R$ 100, quanto vira lucro no final.",
                       {"enzo", "joao"}),
    # --- João
    "Despesas operacionais": ("Custos para manter a empresa funcionando (pessoal, TI, terceiros etc.), sem a "
                              "depreciação e amortização.", {"joao"}),
    "EBITDA": ("Lucro antes de juros, impostos, depreciação e amortização: o resultado da operação.",
               {"joao", "victor", "enzo"}),
    "EBITDA recorrente": ("EBITDA sem eventos pontuais (reversões de provisões, M&A, rescisões). Aproxima a "
                          "geração de caixa 'de verdade' da operação.", {"joao", "victor"}),
    "Margem EBITDA recorrente": ("EBITDA recorrente ÷ receita líquida.", {"joao"}),
    "Ajustes não recorrentes": ("Ganhos ou gastos pontuais que não se repetem todo ano. Separam o EBITDA "
                                "contábil do recorrente.", {"joao"}),
    "Alavancagem operacional": ("Variação do EBITDA ÷ variação da receita. Acima de 1x, o lucro operacional "
                                "cresce mais rápido que a receita (ganho de escala).", {"joao"}),
    "Lucro líquido": ("Resultado final do período, depois de todas as despesas, juros e impostos; o que pertence "
                      "aos acionistas.", {"enzo", "joao", "victor"}),
    "Lucro líquido recorrente": ("Lucro sem eventos pontuais, como a B3 divulga (DRE, linha 121).", {"joao"}),
    "Pessoal e encargos": ("Salários, benefícios e encargos da equipe, incluindo remuneração variável.", {"joao"}),
    "Tecnologia da informação": ("Licenças de software, nuvem, processamento e links de dados. Contratos costumam "
                                 "ser renegociáveis.", {"joao"}),
    "Depreciação e amortização": ("Desgaste contábil de equipamentos, softwares e intangíveis comprados "
                                  "(ex.: Cetip). Não sai dinheiro do caixa.", {"joao", "victor"}),
    "Atrelada ao faturamento": ("Despesas que acompanham a receita (ex.: repasses e incentivos por volume).",
                                {"joao"}),
    "Serviços de terceiros": ("Consultorias, jurídico e outros serviços contratados de fora.", {"joao"}),
    "Resultado financeiro": ("Rendimento das aplicações menos os juros das dívidas.", {"joao", "victor"}),
    "Imposto de renda e contribuição social": ("IRPJ e CSLL sobre o lucro, corrente (pago) e diferido (contábil).",
                                               {"joao", "victor"}),
    "Pareto": ("Ordena os custos do maior para o menor: poucos itens costumam concentrar a maior parte do gasto.",
               {"joao"}),
    # --- Victor
    "Caixa total": ("Disponibilidades + aplicações financeiras de curto e longo prazo.", {"victor"}),
    "Garantias de terceiros": ("Dinheiro de participantes depositado como garantia; está no caixa e no passivo.",
                               {"victor"}),
    "Dívida bruta": ("Debêntures, empréstimos e bond, curto + longo prazo.", {"victor"}),
    "Dívida líquida": ("Dívida bruta − caixa total. Negativa = caixa líquido (folga).", {"victor"}),
    "Folga (caixa − dívida)": ("Quanto sobra de caixa depois de pagar toda a dívida.", {"victor"}),
    "Alavancagem": ("Dívida bruta ÷ EBITDA recorrente LTM: quantos anos de EBITDA pagariam a dívida.", {"victor"}),
    "Cobertura de juros": ("EBIT ÷ despesas financeiras: quantas vezes o resultado operacional paga os juros.",
                           {"victor"}),
    "EBIT": ("Resultado operacional (lucro antes de juros e impostos).", {"victor"}),
    "FCO": ("Fluxo de caixa operacional, como a B3 publica na DFC.", {"victor"}),
    "CAPEX": ("Investimento em equipamentos, sistemas e software.", {"victor"}),
    "FCL": ("Fluxo de caixa livre: FCO − CAPEX.", {"victor"}),
    "FCL depois dos juros": ("FCL − despesas de juros: o que sobra para o acionista.", {"victor"}),
    "JCP": ("Juros sobre capital próprio: outra forma de pagar o acionista em dinheiro. A B3 desconta esse valor "
            "do lucro tributável e paga menos imposto; quem recebe paga IR na fonte.", {"victor", "joao"}),
    "Dividendos": ("Parte do lucro paga em dinheiro aos acionistas. Para quem recebe, é isento de imposto de renda.",
                   {"victor"}),
    "Proventos": ("Dinheiro pago ao acionista: dividendos + JCP.", {"victor"}),
    "Recompra": ("A B3 usa o próprio caixa para comprar ações dela mesma na bolsa e depois cancelá-las. Com menos "
                 "ações, cada uma fica com um pedaço maior do lucro: é outra forma de devolver dinheiro ao acionista.",
                 {"victor"}),
    "Payout": ("(Dividendos + JCP + recompras) ÷ lucro: quanto do lucro voltou ao acionista. Acima de 100%, a B3 "
               "devolveu mais do que lucrou.", {"victor"}),
    "Lucro do período (traço)": ("O traço marca o lucro do período (100%). Se a pilha passa do traço, a B3 devolveu "
                                 "mais do que lucrou.", {"victor"}),
    "Devolvido ao acionista": ("Proventos + recompras pagos em dinheiro no período.", {"victor"}),
    "Disponibilidades": ("Dinheiro em conta e aplicações de resgate imediato.", {"victor"}),
    "Aplicações financeiras": ("Dinheiro aplicado em títulos (CDB, títulos públicos, fundos). CP = vence em até 12 "
                               "meses; LP = depois disso.", {"victor"}),
    "Dívida de curto prazo": ("Parte da dívida que vence nos próximos 12 meses.", {"victor"}),
    "Dívida de longo prazo": ("Parte da dívida que vence depois de 12 meses.", {"victor"}),
    "Bond": ("Título de dívida vendido a investidores no exterior, em dólar.", {"victor"}),
    "Empréstimos bancários": ("Dinheiro emprestado direto por bancos, com juros e prazo combinados em contrato.",
                              {"victor"}),
    "IR diferido": ("Imposto lançado agora, mas pago (ou abatido) no futuro: entra no lucro sem sair do caixa.",
                    {"victor"}),
    "Capital de giro": ("Variação de contas a receber e a pagar do dia a dia; mexe no caixa sem passar pelo lucro.",
                        {"victor"}),
    "IR e CS pagos": ("Imposto de renda e contribuição social pagos em dinheiro no período.", {"victor"}),
    "Outros ajustes": ("Itens que mudam o lucro sem mexer no caixa (provisões, remuneração em ações etc.).",
                       {"victor"}),
    "Despesas de juros": ("Juros da dívida (debêntures, bond e empréstimos).", {"victor"}),
    "Proventos em custódia": ("Dividendos de outras empresas que a B3 guarda por alguns dias antes de repassar aos "
                              "investidores: passam pelo caixa, mas não são dela.", {"victor"}),
    "Aquisições e outros investimentos": ("Compra de empresas e participações e outros investimentos fora do CAPEX.",
                                          {"victor"}),
    "Câmbio e outros": ("Diferença que fecha a conta: efeito do dólar sobre a dívida em moeda estrangeira e itens "
                        "menores.", {"victor"}),
    "Efeito EBITDA": ("Quanto a alavancagem mudou só porque o EBITDA mudou (com a dívida parada).", {"victor"}),
    "Efeito dívida": ("Quanto a alavancagem mudou só porque a dívida mudou.", {"victor"}),
    "Arrendamentos": ("Aluguéis de longo prazo (imóveis, equipamentos) que a contabilidade trata como dívida.",
                      {"victor"}),
    "Capacidade de pagamento": ("FCO de 12 meses ÷ dívida bruta: quanto da dívida o caixa da operação pagaria em "
                                "um ano.", {"victor"}),
    "ROE": ("Lucro ÷ patrimônio líquido: retorno sobre o capital do acionista.", {"victor"}),
}


def md(texto):
    """Escapa o cifrão para st.markdown (dois "$" no mesmo texto viram fórmula LaTeX)."""
    return str(texto).replace("\\$", "$").replace("$", "\\$")


def sem_escape(texto):
    """Para blocos HTML: o markdown não interpreta fórmulas dentro deles, então o cifrão fica puro."""
    return str(texto).replace("\\$", "$")


def explica(termo):
    """Explicação em texto puro (para help= e title=)."""
    return GLOSSARIO.get(termo, ("", set()))[0]


def dica(termo, largura=52):
    """Explicação para o balão do Plotly (hover)."""
    t = explica(termo)
    return "" if not t else "<br><i>" + "<br>".join(textwrap.wrap(t, largura)) + "</i>"


def glossario(aba, titulo="📖 Glossário"):
    termos = sorted((k, v[0]) for k, v in GLOSSARIO.items() if aba == "todas" or aba in v[1])
    with st.expander(titulo):
        st.markdown("\n".join(f"- **{k}:** {v}" for k, v in termos))
        st.markdown("**Cores de oportunidade:** " + " · ".join(
            f"{OPORT_EMOJI[n]} **{n}**: {OPORT_DESC[n]}" for n in ORDEM_NIVEL))
        st.caption("Passe o mouse sobre os indicadores (ícone ?) e sobre os gráficos para ver estas explicações.")


# ======================================================================================
# Formatação pt-BR
# ======================================================================================
def br(v, dec=1):
    if v is None or (isinstance(v, (float, np.floating)) and np.isnan(v)):
        return "—"
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, dec=1, sinal=False):
    """v em fração (0,12 -> 12,0%)."""
    if v is None or pd.isna(v):
        return "—"
    s = br(v * 100, dec) + "%"
    return ("+" + s) if (sinal and v >= 0) else s


def pp(v, dec=1):
    """v em fração -> pontos percentuais com sinal."""
    if v is None or pd.isna(v):
        return "—"
    return f"{'+' if v >= 0 else '-'}{br(abs(v) * 100, dec)} p.p."


def bi(v_mil, dec=2, md=True):
    """R$ mil -> 'R$ 11,12 bi'. md=True escapa o cifrão para st.markdown."""
    if v_mil is None or pd.isna(v_mil):
        return "—"
    moeda = "R\\$" if md else "R$"
    sinal = "-" if v_mil < 0 else ""
    return f"{sinal}{moeda} {br(abs(v_mil) / 1e6, dec)} bi"


def mi(v_mil, dec=0, md=True):
    if v_mil is None or pd.isna(v_mil):
        return "—"
    moeda = "R\\$" if md else "R$"
    sinal = "-" if v_mil < 0 else ""
    return f"{sinal}{moeda} {br(abs(v_mil) / 1e3, dec)} mi"


def var(atual, anterior):
    if anterior is None or atual is None or pd.isna(anterior) or pd.isna(atual) or anterior == 0:
        return None
    return atual / anterior - 1


def cagr(ini, fim, n):
    if n <= 0 or ini is None or ini <= 0 or fim is None or fim <= 0:
        return None
    return (fim / ini) ** (1 / n) - 1


def delta_txt(v, ref, unidade="%"):
    """Delta para st.metric: string com sinal ASCII ('-' define a cor)."""
    if v is None or pd.isna(v):
        return None
    if unidade == "p.p.":
        return f"{pp(v)} vs {ref}"
    return f"{'+' if v >= 0 else '-'}{br(abs(v) * 100, 1)}% vs {ref}"


# ======================================================================================
# Gráficos: tela cheia + barra de escala (zoom, autoescala, resetar eixos)
# ======================================================================================
CONFIG_GRAFICO = {
    "displaylogo": False,
    "displayModeBar": True,  # barra sempre visível: zoom, pan, autoescala, resetar eixos, baixar PNG
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "scrollZoom": False,
    "locale": "pt-BR",
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


def layout_base(fig, titulo=None, altura=430, y_titulo=None, legenda=True):
    """Título no topo e legenda logo abaixo dele, com margem que cresce com a legenda (nada se sobrepõe)."""
    itens = [t for t in fig.data if t.type not in ("waterfall", "sankey", "treemap", "pie")
             and getattr(t, "showlegend", None) is not False]
    linhas = 0 if not legenda or not itens else (1 if len(itens) <= 2 else 2 if len(itens) <= 4 else 3)
    # a barra de ferramentas do Plotly ocupa ~30 px no topo: título e legenda começam abaixo dela
    topo = (72 if titulo else 34) + 26 * linhas + 10
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", x=0, xanchor="left", y=1, yref="container", yanchor="top",
                   pad=dict(t=34), font=dict(size=15)) if titulo else None,
        separators=",.",
        height=altura + topo - 40,
        margin=dict(l=10, r=10, t=topo, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=12),
                    bgcolor="rgba(0,0,0,0)"),
        showlegend=legenda,
        font=dict(size=13),
        hoverlabel=dict(align="left"),
    )
    if y_titulo:
        fig.update_yaxes(title_text=y_titulo)
    return fig


def cascata(passos, titulo=None, altura=480, y_titulo="R$ bilhões", dec=2, escala=1e6, rotulos_caixa=False):
    """Cascata com cor por barra (barras flutuantes), para colorir cada componente pela oportunidade.

    passos: lista de dict(rotulo, valor [R$ mil], tipo='total'|'passo', cor=None, hover='').
    'total' desenha o valor como barra cheia (subtotal); 'passo' sobe ou desce a partir do nível atual.
    """
    import plotly.graph_objects as go

    nivel, bases, alturas, textos, cores, hovers, topos = 0.0, [], [], [], [], [], []
    for p in passos:
        v = p["valor"] / escala
        if p["tipo"] == "total":
            base, alt, nivel = 0.0, v, v
            txt = br(v, dec)
            cor = p.get("cor") or AZUL
        else:
            base = nivel + v if v < 0 else nivel
            alt = abs(v)
            nivel += v
            txt = ("+" if v >= 0 else "−") + br(abs(v), dec)
            cor = p.get("cor") or (VERDE if v >= 0 else VERMELHO)
        bases.append(base)
        alturas.append(alt)
        textos.append(txt)
        cores.append(cor)
        topos.append(base + alt)
        hovers.append(p.get("hover") or f"<b>{p['rotulo']}</b><br>{txt}")
    x = [p["rotulo"] for p in passos]
    fig = go.Figure()
    fig.add_bar(x=x, y=bases, marker_color="rgba(0,0,0,0)", hoverinfo="skip", showlegend=False)
    fig.add_bar(x=x, y=alturas, marker_color=cores, hovertext=hovers, hoverinfo="text", showlegend=False,
                marker_line=dict(color="rgba(0,0,0,0.25)", width=0.5))
    for i, (t, topo) in enumerate(zip(textos, topos)):
        fig.add_annotation(x=i, y=topo, text=f"<b>{t}</b>", showarrow=False, yshift=12, font=dict(size=12),
                           bgcolor="rgba(255,255,255,0.9)" if rotulos_caixa else None)
    fig.update_layout(barmode="stack", bargap=0.3)
    layout_base(fig, titulo, altura=altura, y_titulo=y_titulo, legenda=False)
    fig.update_yaxes(range=[min(0, min(bases)) * 1.1, max(topos) * 1.12])
    fig.update_xaxes(type="category")
    return fig


def rotular_linhas(fig):
    """Padrão do grupo: todo gráfico de linha mostra o valor em cada ponto.

    Linhas sem rótulo (ou com rótulo só em alguns pontos) ganham o valor em todos os pontos, com as casas
    decimais pelo tamanho do número e o sufixo do eixo (%, x). Áreas empilhadas ficam de fora.
    """
    for t in fig.data:
        if t.type != "scatter" or "lines" not in (t.mode or "lines") or t.stackgroup or t.y is None:
            continue
        y = pd.to_numeric(pd.Series(list(t.y)), errors="coerce")
        if y.isna().all():
            continue
        texto = list(t.text) if t.text is not None and not isinstance(t.text, str) else None
        completo = t.texttemplate or (texto is not None and len(texto) == len(y) and all(str(x).strip() for x in texto))
        modo = set((t.mode or "lines").split("+"))
        if not completo:
            eixo = fig.layout.yaxis2 if t.yaxis == "y2" else fig.layout.yaxis
            sufixo = eixo.ticksuffix or ""
            maior = y.abs().max()
            dec = 0 if maior >= 100 else 1 if maior >= 10 else 2
            t.text = None
            t.texttemplate = f"%{{y:,.{dec}f}}{sufixo}"
            t.textposition = t.textposition or "top center"
            t.textfont = dict(size=11 if len(y) <= 12 else 9, color=(t.textfont.color if t.textfont else None))
        t.mode = "+".join(sorted(modo | {"lines", "markers", "text"}, key=["lines", "markers", "text"].index))
    return fig


def mostrar_grafico(fig, key=None, **kw):
    """Padrão de exibição: largura total, botão de tela cheia do Streamlit e barra de escala do Plotly."""
    fig.update_layout(separators=",.")
    rotular_linhas(fig)
    ajustar_tema(fig)
    return st.plotly_chart(fig, width="stretch", config=CONFIG_GRAFICO, key=key, **kw)


# ======================================================================================
# Indicadores-chave (padrão da Camila)
# ======================================================================================
def kpis(itens, colunas=None):
    """itens: lista de dict(rotulo, valor, delta=None, termo=None, delta_color='normal')."""
    colunas = colunas or len(itens)
    for i in range(0, len(itens), colunas):
        cols = st.columns(colunas)
        for c, it in zip(cols, itens[i:i + colunas]):
            c.metric(it["rotulo"], it["valor"], it.get("delta"), delta_color=it.get("delta_color", "normal"),
                     help=it.get("ajuda") or explica(it.get("termo", it["rotulo"])) or None)


# ======================================================================================
# Painel de alertas (padrão do João e do Victor)
# ======================================================================================
STATUS_COR = {"Confortável": "#2E9E5B", "Atenção": "#C98A00", "Alerta": "#D64545", "Informativo": "#1F5FAD"}
STATUS_EMOJI = {"Confortável": "🟢", "Atenção": "🟡", "Alerta": "🔴", "Informativo": "🔵"}


def status_faixa(v, conf, alerta=None, maior_melhor=True):
    """Confortável / Atenção / Alerta a partir de limites."""
    if v is None or pd.isna(v):
        return "Informativo"
    if maior_melhor:
        if v >= conf:
            return "Confortável"
        return "Alerta" if (alerta is not None and v < alerta) else "Atenção"
    if v <= conf:
        return "Confortável"
    return "Alerta" if (alerta is not None and v > alerta) else "Atenção"


def _card_alerta(x):
    cor = STATUS_COR[x["status"]]
    titulo = html.escape(x.get("desc", ""), quote=True)
    x = {k: sem_escape(v) if isinstance(v, str) else v for k, v in x.items()}
    return (
        f"<div class='radar-card' style='border-left:6px solid {cor}' title=\"{titulo}\">"
        f"<div class='rc-top'><span class='rc-nome'>{x['nome']}</span>"
        f"<span class='rc-badge' style='background:{cor}26;color:{cor}'>{x['status']}</span></div>"
        + (f"<div class='rc-formula'>{x['formula']}</div>" if x.get("formula") else "") +
        f"<div class='rc-valor'>{x['valor']}</div>"
        f"<div class='rc-delta'>{x.get('delta') or '&nbsp;'}</div>"
        f"<div class='rc-desc'>{x.get('desc', '')}</div>"
        f"<div class='rc-fonte'>Regra: {x.get('regra', '—')}</div></div>"
    )


def painel_alertas(itens, leitura=None, rodape=None, por_linha=4, titulo="🚨 Painel de alertas"):
    st.markdown(f"### {titulo}")
    if leitura:
        st.markdown(md(leitura))
    for i in range(0, len(itens), por_linha):
        cols = st.columns(por_linha)
        for c, x in zip(cols, itens[i:i + por_linha]):
            c.markdown(_card_alerta(x), unsafe_allow_html=True)
    if rodape:
        st.caption(rodape)


def leitura_alertas(itens, contexto):
    """Frase-resumo do painel a partir dos status."""
    cont = {s: [x for x in itens if x["status"] == s] for s in STATUS_COR}
    partes = []
    if cont["Confortável"]:
        partes.append(f"{len(cont['Confortável'])} confortável(is)")
    if cont["Atenção"]:
        partes.append(f"{len(cont['Atenção'])} em atenção (" + ", ".join(x["nome"].lower() for x in cont["Atenção"]) + ")")
    if cont["Alerta"]:
        partes.append(f"{len(cont['Alerta'])} em alerta (" + ", ".join(x["nome"].lower() for x in cont["Alerta"]) + ")")
    return f"**Leitura:** {contexto}: " + "; ".join(partes) + "." if partes else None


# ======================================================================================
# Diagnóstico e fonte (padrão do Victor)
# ======================================================================================
def diagnostico(itens, titulo="🔍 Diagnóstico", aberto=True):
    with st.expander(titulo, expanded=aberto):
        st.markdown("\n".join(f"- {t}" for t in itens))


def fonte(linhas, titulo="📄 Fonte", nota=None):
    """linhas: lista de (item, origem, detalhe)."""
    tabela = "| Item | Origem | Detalhe |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in linhas)
    with st.expander(titulo):
        st.markdown(md(tabela))
        if nota:
            st.caption(md(nota))


def leitura(texto):
    """Frase de leitura logo abaixo de um gráfico."""
    st.markdown(f"<div class='leitura'>{sem_escape(texto)}</div>", unsafe_allow_html=True)


# ======================================================================================
# Oportunidades (coletadas pelas abas e consolidadas na Conclusão)
# ======================================================================================
def oportunidade(janela, aba, nivel, tema, diagnostico_, acao, evidencia="", numero=None):
    """numero: (valor, legenda) mostrado em destaque no card, ex.: ("124%", "payout LTM")."""
    janela.oportunidades.append(dict(aba=aba, nivel=nivel, tema=tema, diagnostico=diagnostico_, acao=acao,
                                     evidencia=evidencia, numero=numero))


# Valores com unidade (R$ 2,6 bi · 124% · 1,98x · 4,0–4,5x · +11 p.p.) ficam em negrito nos cards
_NUMERO = re.compile(r"(?:[~≈]\s?)?(?:R\$\s?)?[−+]?\d[\d.,]*(?:\s?[–-]\s?\d[\d.,]*)?"
                     r"\s?(?:bi|mil|mi|%|x|p\.p\.)(?![A-Za-zÀ-ú])|R\$\s?\d[\d.,]*")


def destacar_numeros(texto):
    return _NUMERO.sub(lambda m: f"<b style='white-space:nowrap'>{m.group(0)}</b>", sem_escape(texto))


def _vazio(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or v == ""


def cartao_oportunidade(o, mostrar_aba=False):
    """Card de oportunidade: tema e nível, número-chave, o que os números mostram e o que fazer."""
    nivel = o["nivel"]
    cor = OPORT[nivel]
    num = None if _vazio(o.get("numero")) else o["numero"]
    ev = "" if (num or _vazio(o.get("evidencia"))) else f"<span class='op-aba'>{sem_escape(o['evidencia'])}</span>"
    aba = f"<span class='op-aba'>{o['aba']}</span>" if mostrar_aba else ""
    lado = (f"<div class='op-num' style='color:{cor}'>{sem_escape(num[0])}"
            f"<div class='op-num-leg'>{sem_escape(num[1])}</div></div>") if num else ""
    return (
        f"<div class='op-card' style='border-left:6px solid {cor}'>"
        f"<div class='op-top'><span class='op-tema'>{OPORT_EMOJI[nivel]} {sem_escape(o['tema'])}</span>{aba}{ev}"
        f"<span class='op-badge' style='background:{cor}26;color:{cor}'>{OPORT_DESC[nivel]}</span></div>"
        f"<div class='op-corpo'>{lado}<div class='op-texto'>"
        f"<div class='op-diag'><span class='op-rot'>O que os números mostram</span>"
        f"{destacar_numeros(o['diagnostico'])}</div>"
        f"<div class='op-acao' style='background:{cor}1A;border-left:3px solid {cor}'>"
        f"<span class='op-rot'>👉 O que fazer</span>{destacar_numeros(o['acao'])}</div>"
        f"</div></div></div>"
    )


def bloco_oportunidades(janela, aba, titulo="💡 Diagnóstico de oportunidades desta aba"):
    ops = [o for o in janela.oportunidades if o["aba"] == aba]
    if not ops:
        return
    st.markdown(f"### {titulo}")
    for nivel in ORDEM_NIVEL:
        for o in [o for o in ops if o["nivel"] == nivel]:
            st.markdown(cartao_oportunidade(o), unsafe_allow_html=True)


# ======================================================================================
# CSS global
# ======================================================================================
# ======================================================================================
# Tema claro / escuro (escolhido na barra lateral; vale para cards e gráficos)
# ======================================================================================
TEMAS = {
    "light": dict(fundo_card="#FFFFFF", borda="#E1E8F0", titulo="#142B4A", sombra="rgba(20,43,74,0.05)"),
    "dark": dict(fundo_card="#16213A", borda="#2A3A55", titulo="#E6EDF5", sombra="rgba(0,0,0,0.35)"),
}
# Cores escuras usadas em textos e linhas dos gráficos -> versão clara no tema escuro
CLAREAR = {"#4B5563": "#CBD5E1", "#4b5563": "#CBD5E1", "#111111": "#E5E7EB", "#333": "#E5E7EB", "#333333": "#E5E7EB",
           "#1F5FAD": "#7FB2F0", "#1f5fad": "#7FB2F0", "#9A6B00": "#F2C14E", "#B03A1E": "#FF8A65",
           "#142B4A": "#E6EDF5", "#4d4d4d": "#9CA3AF"}


def logo_b3():
    """Logo oficial da B3 (Wikimedia Commons, Logotipo_da_B3.svg); versão branca no tema escuro."""
    from pathlib import Path
    pasta = Path(__file__).resolve().parent.parent / "data"
    caminho = pasta / ("logo_b3_branco.svg" if tema_atual() == "dark" else "logo_b3.svg")
    return str(caminho) if caminho.exists() else None


def blocos(rotulo, opcoes, padrao, key, formato=None, ajuda=None):
    """Padrão do painel para escolher anos (e outras listas curtas): bloquinhos clicáveis."""
    escolha = st.segmented_control(rotulo, list(opcoes), default=padrao, key=key, format_func=formato or str,
                                   help=ajuda)
    return padrao if escolha is None else escolha


def bloco_trimestre(rotulo, trimestres, padrao, key):
    """Trimestre em blocos: uma fileira para o ano e outra para o trimestre (1T a 4T). Devolve '2T26'."""
    trimestres = list(trimestres)
    ano_de = lambda q: 2000 + int(q[-2:])
    anos = sorted({ano_de(q) for q in trimestres})
    padrao = padrao if padrao in trimestres else trimestres[-1]
    g_ano, g_tri = st.columns([3, 2])
    with g_ano:
        ano = blocos(f"{rotulo}: ano", anos, ano_de(padrao), f"{key}_ano")
    disponiveis = [q[:2] for q in trimestres if ano_de(q) == ano]
    pad_tri = padrao[:2] if padrao[:2] in disponiveis else disponiveis[-1]
    with g_tri:
        tri = blocos(f"{rotulo}: trimestre", disponiveis, pad_tri, f"{key}_tri_{ano}")
    return f"{tri}{str(ano)[-2:]}"


def tema_atual():
    """'light' ou 'dark': a escolha da barra lateral (?tema=) manda; senão, o tema detectado pelo navegador."""
    escolha = st.query_params.get("tema")
    if escolha in ("claro", "escuro"):
        return "dark" if escolha == "escuro" else "light"
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def seletor_tema():
    """Rádio Claro/Escuro na barra lateral. Ao trocar, grava o tema do Streamlit no navegador e recarrega."""

    atual = tema_atual()
    escolha = st.radio("🎨 Tema", ["☀️ Claro", "🌙 Escuro"], index=1 if atual == "dark" else 0, horizontal=True,
                       key="tema_sel", help="Muda as cores de todo o painel e dos gráficos.")
    nova = "dark" if "Escuro" in escolha else "light"
    if nova == atual and st.query_params.get("tema") in ("claro", "escuro"):
        # Link com ?tema= aberto num navegador que guardou o outro tema: alinha o Streamlit com a URL.
        valor = "Dark" if atual == "dark" else "Light"
        st.html(
            "<script>"
            "const k='stActiveTheme-'+location.pathname+'-v2';"
            f"if(localStorage.getItem(k)!==JSON.stringify('{valor}')){{"
            f"localStorage.setItem(k, JSON.stringify('{valor}'));location.reload();}}"
            "</script>", unsafe_allow_javascript=True)
    if nova != atual:
        valor, param = ("Dark", "escuro") if nova == "dark" else ("Light", "claro")
        # Script fixo (sem entrada do usuário): grava o tema do Streamlit no navegador e recarrega com ?tema=.
        st.html(
            "<script>"
            f"localStorage.setItem('stActiveTheme-'+location.pathname+'-v2', JSON.stringify('{valor}'));"
            f"const u=new URL(location.href);u.searchParams.set('tema','{param}');location.replace(u.toString());"
            "</script>", unsafe_allow_javascript=True)


def _clarear(cor):
    return CLAREAR.get(cor, cor) if isinstance(cor, str) else cor


def ajustar_tema(fig):
    """No tema escuro, troca textos e linhas escuros por versões claras e o fundo das caixas de rótulo."""
    if tema_atual() != "dark":
        return fig
    for a in fig.layout.annotations or []:
        if a.font and a.font.color:
            a.font.color = _clarear(a.font.color)
        if a.bgcolor and str(a.bgcolor).startswith("rgba(255,255,255"):
            a.bgcolor = "rgba(22,33,58,0.92)"
            a.font.color = "#E6EDF5"
    for t in fig.data:
        tf = getattr(t, "textfont", None)
        if tf is not None and isinstance(tf.color, str):
            tf.color = _clarear(tf.color)
        ln = getattr(t, "line", None)
        if ln is not None and isinstance(getattr(ln, "color", None), str):
            ln.color = _clarear(ln.color)
    return fig


def css():
    c = TEMAS[tema_atual()]
    return f"""
<style>
.block-container {{padding-top: 2rem; max-width: 1500px;}}
h1, h2, h3 {{color: {c['titulo']};}}
/* Indicadores-chave (padrão da Camila) */
div[data-testid="stMetric"] {{background: {c['fundo_card']}; border: 1px solid {c['borda']}; padding: 14px 16px;
    border-radius: 12px; box-shadow: 0 2px 8px {c['sombra']};}}
div[data-testid="stExpander"] {{background: {c['fundo_card']}; border-radius: 10px;}}
div[data-testid="stAlert"] {{border-radius: 10px;}}
/* Painel de alertas (padrão do Victor/João) */
.radar-card {{border-radius: 10px; padding: 12px 14px; margin-bottom: 12px; min-height: 178px;
    background: {c['fundo_card']}; border: 1px solid {c['borda']}; box-shadow: 0 2px 8px {c['sombra']}; cursor: help;}}
.rc-top {{display:flex; justify-content:space-between; align-items:flex-start; gap:8px;}}
.rc-nome {{font-weight:600; font-size:0.9rem; line-height:1.25;}}
.rc-badge {{font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:999px; white-space:nowrap;}}
.rc-formula {{font-size:0.74rem; opacity:0.65; margin-top:2px;}}
.rc-valor {{font-size:1.6rem; font-weight:700; margin-top:6px;}}
.rc-delta {{font-size:0.8rem; opacity:0.75;}}
.rc-desc {{font-size:0.8rem; margin-top:6px; line-height:1.3;}}
.rc-fonte {{font-size:0.72rem; margin-top:6px; opacity:0.6;}}
.tese {{font-size:1.1rem; font-style:italic; margin-top:-0.4rem; opacity:0.85;}}
.leitura {{font-size:0.95rem; margin:-4px 0 10px 0;}}
.oport {{background:{c['fundo_card']}; border:1px solid {c['borda']}; border-radius:8px; padding:8px 12px;
    margin-bottom:8px; font-size:0.92rem;}}
.op-card {{background:{c['fundo_card']}; border:1px solid {c['borda']}; border-radius:10px; padding:12px 16px;
    margin-bottom:12px; box-shadow: 0 2px 8px {c['sombra']};}}
.op-top {{display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-bottom:8px;}}
.op-tema {{font-weight:700; font-size:1.02rem;}}
.op-aba {{font-size:0.8rem; opacity:0.7;}}
.op-badge {{font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:999px; margin-left:auto;}}
.op-corpo {{display:flex; gap:18px; align-items:flex-start;}}
.op-num {{flex:0 0 150px; font-size:1.7rem; font-weight:800; line-height:1.1;}}
.op-num-leg {{font-size:0.74rem; font-weight:500; opacity:0.8; margin-top:4px; line-height:1.25;}}
.op-texto {{flex:1; min-width:0;}}
.op-rot {{display:block; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;
    opacity:0.65; margin-bottom:2px;}}
.op-diag {{font-size:0.92rem; margin-bottom:8px;}}
.op-acao {{font-size:0.95rem; padding:6px 10px; border-radius:6px;}}
@media (max-width: 640px) {{ .op-corpo {{flex-direction:column; gap:6px;}} .op-num {{flex:none;}} }}
</style>
"""


def aplicar_css():
    st.markdown(css(), unsafe_allow_html=True)


def cabecalho_secao(titulo, tese=None, abertura=None):
    st.divider()
    st.markdown(f"## {titulo}")
    if tese:
        st.markdown(f"<div class='tese'>{tese}</div>", unsafe_allow_html=True)
    if abertura:
        st.markdown(md(abertura))
