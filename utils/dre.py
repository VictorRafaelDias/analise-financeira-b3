"""DRE oficial da B3 (aba "IS (New Seg)" da planilha "Dados Trimestrais - Nova Segmentação", 2T26).

Usada pelas abas do Enzo e do João. Lê os valores pela LINHA da planilha (o mesmo rótulo aparece
mais de uma vez, ex.: "Despesas", "Margem líquida") e confere o rótulo de cada linha ao carregar.
Valores em R$ mil, como na planilha. Nenhum valor é alterado.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DRE_PATH = BASE_DIR / "data" / "B3_Dados_Trimestrais_2T26.xlsx"
ABA = "IS (New Seg)"

# chave -> (linha da planilha, rótulo esperado na coluna A)
LINHAS = {
    "receita_total": (4, "Receita total"),
    "mercados": (5, "Mercados"),
    "derivativos": (6, "Derivativos"),
    "renda_variavel": (7, "Renda Variável"),
    "rf_credito": (8, "Renda Fixa e Crédito"),
    "emprestimo_ativos": (9, "Empréstimo de Ativos"),
    "solucoes_mc": (10, "Soluções para Mercado de Capitais"),
    "solucoes_dados": (14, "Soluções Analíticas de Dados"),
    "tec_plataformas": (17, "Tecnologia e Plataformas"),
    "tecnologia": (18, "Tecnologia"),
    "apoio_mercado": (19, "Serviços de Apoio ao Mercado"),
    "outros": (20, "Outros"),
    "outras_receitas": (21, "Outras receitas"),
    "deducoes": (22, "Deduções da receita"),
    "pis_cofins": (23, "PIS e Cofins"),
    "iss": (24, "Impostos sobre serviços"),
    "receita_liquida": (25, "Receita líquida"),
    "despesas": (26, "Despesas"),
    "pessoal": (27, "Pessoal e encargos"),
    "ti": (28, "Tecnologia da informação"),
    "da": (29, "Depreciação e amortização"),
    "atrelada": (30, "Atrelada ao faturamento"),
    "terceiros": (31, "Serviços de terceiros"),
    "manutencao": (32, "Manutenção em geral"),
    "comunicacoes": (33, "Comunicações"),
    "promocao": (34, "Promoção e divulgação"),
    "impostos_taxas": (35, "Impostos e taxas"),
    "honorarios": (36, "Honorários do conselho/comitês"),
    "cetip": (37, "Relacionadas à combinação com a Cetip"),
    "diversas": (38, "Diversas"),
    "resultado_operacional": (39, "Resultado operacional"),
    "impairment": (41, "Redução ao valor recuperável de ativos (impairment)"),
    "equivalencia": (42, "Resultado de equivalência patrimonial"),
    "descontinuidade_eq": (43, "Descontinuidade do método de equivalência patrimonial"),
    "alienacao_coligadas": (44, "Resultado de alienação de investimentos em coligadas"),
    "resultado_financeiro": (45, "Resultado financeiro"),
    "lair": (50, "Resultado antes da tributação sobre o lucro"),
    "ir": (51, "Imposto de renda e contribuição social"),
    "ir_corrente": (52, "Corrente"),
    "ir_diferido": (53, "Diferido"),
    "lucro": (56, "Lucro (prejuízo) líquido do período"),
    "lucro_acionistas": (59, "Acionistas"),
    "ebitda": (66, "EBITDA"),
    "aj_cetip": (67, "Despesas relacionadas à combinação com a Cetip"),
    "aj_incentivo": (68, "Alteração de programa/metodologia de incentivo de longo prazo"),
    "aj_outros": (69, "Outros efeitos não-recorrentes"),
    "ebitda_recorrente": (79, "EBITDA recorrente"),
    "lucro_recorrente": (121, "Lucro líquido recorrente"),
}

# Componentes de receita que somam exatamente a Receita total (segmentação do Enzo)
SEGMENTOS = [
    ("mercados", "Mercados"),
    ("solucoes_mc", "Soluções para Mercado de Capitais"),
    ("solucoes_dados", "Soluções Analíticas de Dados"),
    ("tecnologia", "Tecnologia"),
    ("apoio_mercado", "Serviços de Apoio ao Mercado"),
    ("outros", "Outros"),
    ("outras_receitas", "Outras receitas"),
]

# Despesas sem D&A (linhas 27–38 exceto 29), com o potencial de oportunidade de cada uma (critério do João)
DESPESAS = [
    ("pessoal", "Pessoal e encargos", "Médio", "Maior custo; parte é remuneração variável e pode acompanhar o resultado."),
    ("ti", "Tecnologia da informação", "Alto", "Licenças, nuvem e processamento: contratos renegociáveis."),
    ("atrelada", "Atrelada ao faturamento", "Baixo", "Acompanha a receita; reduzir significa reduzir receita."),
    ("terceiros", "Serviços de terceiros", "Alto", "Consultorias e jurídico: contratos renegociáveis."),
    ("manutencao", "Manutenção em geral", "Médio", "Pode ser renegociada ou internalizada."),
    ("comunicacoes", "Comunicações", "Médio", "Contratos de comunicação."),
    ("promocao", "Promoção e divulgação", "Médio", "Gasto discricionário de marketing."),
    ("impostos_taxas", "Impostos e taxas", "Baixo", "Tributos fixos, pouco espaço de gestão."),
    ("honorarios", "Honorários do conselho/comitês", "Baixo", "Governança: custo estrutural."),
    ("cetip", "Relacionadas à combinação com a Cetip", "Baixo", "Despesa ligada a uma aquisição passada."),
    ("diversas", "Diversas", "Médio", "Grupo residual: vale abrir e revisar."),
]
DEDUCOES = [
    ("pis_cofins", "PIS e Cofins", "Médio", "Tributo federal sobre o faturamento; depende de planejamento tributário."),
    ("iss", "Impostos sobre serviços", "Baixo", "ISS municipal: alíquota fixada pelo município."),
]


@st.cache_data
def carregar_dre():
    """Devolve (valores, rótulos): valores com índice = chave de LINHAS e colunas = períodos
    ('1T20'…'2T26' e '2020'…'2025'), em R$ mil."""
    raw = pd.read_excel(DRE_PATH, sheet_name=ABA, header=None)
    cols = {}
    for i, h in enumerate(raw.iloc[1]):
        s = str(h).strip()
        s = s[:-2] if s.endswith(".0") else s
        if i >= 2 and s not in ("", "nan"):
            cols[s] = i
    linhas = {}
    for k, (n, _) in LINHAS.items():
        linhas[k] = pd.to_numeric(raw.iloc[n - 1, list(cols.values())], errors="coerce").values
    valores = pd.DataFrame(linhas, index=list(cols)).T
    rotulos = {k: str(raw.iloc[n - 1, 0]).strip() for k, (n, _) in LINHAS.items()}
    # Planilha completa (para a tabela "DRE gerencial" do João)
    completa = raw.iloc[3:, [0] + list(cols.values())].copy()
    completa.columns = ["Conta / Indicador"] + list(cols)
    completa = completa.dropna(subset=["Conta / Indicador"])
    completa["Conta / Indicador"] = completa["Conta / Indicador"].astype(str).str.strip()
    completa.insert(0, "Linha", completa.index + 1)
    return valores, rotulos, completa.reset_index(drop=True)


def validar_dre(valores, rotulos):
    erros = []
    for k, (n, esperado) in LINHAS.items():
        if rotulos[k] != esperado:
            erros.append(f"Linha {n} da IS (New Seg) é '{rotulos[k]}', esperado '{esperado}'.")
    for ano in anos_dre(valores):
        soma = sum(valores.loc[k, ano] for k, _ in SEGMENTOS)
        if abs(soma - valores.loc["receita_total", ano]) > 1:
            erros.append(f"Segmentos não somam a Receita total em {ano}.")
        desp = sum(valores.loc[k, ano] for k, *_ in DESPESAS) + valores.loc["da", ano]
        if abs(desp - valores.loc["despesas", ano]) > 1:
            erros.append(f"Linhas 27–38 não somam as Despesas em {ano}.")
        ebitda = valores.loc["receita_liquida", ano] + valores.loc["despesas", ano] - valores.loc["da", ano]
        if abs(ebitda - valores.loc["ebitda", ano]) > 1:
            erros.append(f"Receita líquida + despesas sem D&A não fecha com o EBITDA em {ano}.")
        lucro = valores.loc["lair", ano] + valores.loc["ir", ano]
        if abs(lucro - valores.loc["lucro", ano]) > 1:
            erros.append(f"LAIR + IR não fecha com o lucro em {ano}.")
    return erros


def anos_dre(valores):
    return [c for c in valores.columns if c.isdigit()]


def trimestres_dre(valores):
    return [c for c in valores.columns if not c.isdigit()]


def anual(valores, anos):
    """DataFrame anos x chaves (anos fechados), em R$ mil."""
    return valores[[str(a) for a in anos]].T.rename(index=int)


def trimestral(valores, ano_ini, ano_fim):
    qs = [q for q in trimestres_dre(valores) if ano_ini <= 2000 + int(q[-2:]) <= ano_fim]
    return valores[qs].T
