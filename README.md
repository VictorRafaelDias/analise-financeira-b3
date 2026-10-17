# 📊 Análise Financeira B3

## ▶️ Abrir o painel com um clique

[![Abrir o painel no GitHub](https://github.com/codespaces/badge.svg)](https://codespaces.new/VictorRafaelDias/analise-financeira-b3?quickstart=1)

1. Clique no botão acima e em **Create codespace** (ou **Resume**, se já tiver um).
2. O GitHub monta o ambiente, instala tudo e sobe o painel sozinho. Na primeira vez leva 2–3 minutos.
3. O painel abre numa aba nova do navegador. Se o navegador bloquear, vá na aba **PORTS** (rodapé) e clique no 🌐
   da porta **8501**.

Tudo roda dentro do GitHub: não precisa instalar nada no computador. Para economizar a cota gratuita, feche a aba
quando terminar (o codespace para sozinho depois de 30 minutos parado).

**No computador (Windows):** depois de clonar ou baixar o repositório, dê dois cliques em `abrir_painel.bat`.

**Tema claro ou escuro:** escolha em **🎨 Tema**, no topo da barra lateral. Vale para o painel e os gráficos.

**Logo da B3:** `data/logo_b3.svg` (oficial, de [Wikimedia Commons · Logotipo_da_B3.svg](https://commons.wikimedia.org/wiki/File:Logotipo_da_B3.svg)) e `data/logo_b3_branco.svg` (mesma marca em branco, para o tema escuro).

Painel em **Streamlit** que analisa a **B3 S.A. – Brasil, Bolsa, Balcão** (B3SA3) a partir de dados oficiais.
Projeto Integrador III · Tecnologia em Ciência de Dados.

> Pergunta central: como a B3 gera valor para a economia e para o acionista, e onde estão as oportunidades de melhoria?

## 👥 Equipe e abas

| Aba | Tema | Responsável | Arquivo |
|---|---|---|---|
| 🏛️ Visão geral | Ficha técnica, ODS impactados, ferramentas e fontes | Grupo | `abas/introducao.py` |
| 📈 Desenvolvimento de Mercado | Investidores, custódia, emissões, IPOs, CRI/CRA, LCI/LCA, bancos e ODS | Camila | `abas/camila.py`, `abas/camila_mercado.py` |
| 💰 Receita & Diversificação | Segmentos de receita, Renda Variável x Renda Fixa, margens | Enzo | `abas/enzo.py` |
| ⚙️ Eficiência & Lucratividade | Ponte de resultado, custos, margens, DRE gerencial | João | `abas/joao.py` |
| 🏦 Solidez Financeira | Caixa x dívida, alavancagem, conversão de caixa, retorno ao acionista | Victor | `abas/victor.py` |
| 🎯 Conclusão | Consolidação das oportunidades das quatro abas | Grupo | `abas/conclusao.py` |

## ▶️ Como rodar

```bash
git clone https://github.com/VictorRafaelDias/analise-financeira-b3.git
cd analise-financeira-b3
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abre em `http://localhost:8501`. No Windows PowerShell, rode um comando por linha (o PowerShell 5.1 não aceita `&&`).

## 🧩 Padrões do painel (valem para todas as abas)

Todos ficam em [`utils/comum.py`](utils/comum.py). Use as funções em vez de recriar o visual:

| Padrão | Origem | Função |
|---|---|---|
| Explicação ao passar o mouse | João | `GLOSSARIO`, `explica()`, `dica()` |
| Cor de oportunidade (Alto, Médio, Baixo, Nulo, Forte) | João | `cor_oport()`, `legenda_oportunidade()` |
| Tela cheia e opções de escala (zoom, autoescala) | Enzo | `mostrar_grafico()` |
| Glossário | João | `glossario(aba)` |
| Painel de alertas | João e Victor | `painel_alertas()` |
| Janela de período igual | Enzo | objeto `Janela` (barra lateral do `app.py`) |
| Indicadores-chave | Camila | `kpis()` |
| Bloco de diagnóstico e fonte | Victor | `diagnostico()`, `fonte()` |
| Oportunidades para a Conclusão | grupo | `oportunidade()`, `bloco_oportunidades()` |

Dica: em `st.markdown`, use `c.md(texto)` quando houver mais de um "R$" no texto (dois cifrões viram fórmula).

## 🗂️ Estrutura

```
app.py                 # página única: janela de período + abas
abas/                  # uma aba por pessoa (+ visão geral e conclusão)
utils/comum.py         # padrões compartilhados
utils/dre.py           # leitura da DRE oficial (IS New Seg) com validação
utils/solidez_*.py     # base e gráficos da aba de solidez
data/                  # planilhas oficiais da B3 (2T26)
```

## 📚 Fontes

- **B3 · RI**: Central de Resultados, “Dados Trimestrais – Nova Segmentação” (2T26) e ITR 2T26.
- **B3 · dados de mercado**: pessoas físicas, emissões corporativas, renda fixa bancária.
- **Moody's Local Brasil**: faixas de alavancagem e cobertura de juros.
- **Banco Central**: taxa Selic.
- Séries de IPOs e valor de mercado dos bancos: levantamentos de mercado citados na aba da Camila.

Regra do grupo: **nenhum valor da B3 é alterado**. Só usamos somas, diferenças e razões sobre as linhas oficiais;
incoerências aparecem destacadas, não corrigidas.

## 🔀 Como contribuir

1. Crie uma branch para a sua aba: `git checkout -b camila/ipos` (nome/assunto).
2. Mexa só no(s) arquivo(s) da sua aba; mudanças em `utils/comum.py` afetam todas as abas, então combine com o grupo.
3. Rode o app e confira a sua aba antes de subir.
4. Abra um Pull Request para a `main` e peça revisão de alguém do grupo.
