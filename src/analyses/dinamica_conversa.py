"""Dinâmica da troca de mensagens dentro de uma conversa já em andamento:
quanto tempo cada pessoa demora para responder, e quem costuma retomar a
palavra depois da outra pessoa falar (vs. quem só recebe resposta).

Só conta como "resposta" uma mensagem que muda de remetente e continua a
mesma conversa (não conta o início de uma conversa nova, depois de 1h de
silêncio — isso já é coberto por "Conversas e sequências").
"""

from __future__ import annotations

import pandas as pd

from ..chart_common import grafico_barras_por_pessoa
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_duracao, formatar_numero

KEY = "dinamica_conversa"
TITLE = "Dinâmica da conversa"
ICON = "relogio"
REQUIRES_MEDIA = False

LIMITE_RESPOSTA_RAPIDA_SEGUNDOS = 60


def _respostas_dentro_da_conversa(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por "troca de turno": mensagem que muda de remetente sem
    sair da mesma conversa. `nome` é quem respondeu, `nome_anterior` é quem
    tinha mandado a mensagem respondida.
    """

    nome_anterior = df["nome"].shift(1)
    data_anterior = df["data"].shift(1)
    conversa_anterior = df["numero_conversa"].shift(1)

    mascara = (df["nome"] != nome_anterior) & (df["numero_conversa"] == conversa_anterior)

    respostas = df.loc[mascara, ["data", "nome", "numero_conversa"]].copy()
    respostas["nome_anterior"] = nome_anterior.loc[mascara]
    respostas["tempo_resposta_segundos"] = (respostas["data"] - data_anterior.loc[mascara]).dt.total_seconds()

    return respostas


def run(ctx) -> AnalysisResult:
    df = ctx.df

    respostas = _respostas_dentro_da_conversa(df)

    if respostas.empty:
        return AnalysisResult(key=KEY, title=TITLE, icon=ICON)

    respostas["resposta_rapida"] = respostas["tempo_resposta_segundos"] <= LIMITE_RESPOSTA_RAPIDA_SEGUNDOS

    resumo_tempo = (
        respostas.groupby("nome", observed=True)
        .agg(
            quantidade_respostas=("tempo_resposta_segundos", "size"),
            mediana_segundos=("tempo_resposta_segundos", "median"),
            media_segundos=("tempo_resposta_segundos", "mean"),
            respostas_rapidas=("resposta_rapida", "sum"),
        )
        .reindex(ctx.people, fill_value=0)
        .reset_index()
    )
    resumo_tempo["mediana_minutos"] = resumo_tempo["mediana_segundos"] / 60
    divisor = resumo_tempo["quantidade_respostas"].astype(float).replace(0.0, float("nan"))
    resumo_tempo["percentual_respostas_rapidas"] = (
        (resumo_tempo["respostas_rapidas"] / divisor * 100).fillna(0.0)
    )
    resumo_tempo["mediana_formatada"] = resumo_tempo["mediana_segundos"].apply(formatar_duracao)

    quem_respondeu = resumo_tempo.loc[resumo_tempo["quantidade_respostas"] > 0].copy()

    charts = []
    tabelas = {"resumo_tempo_resposta": resumo_tempo}
    insights = []

    if not quem_respondeu.empty:
        charts.append(
            ChartArtifact(
                slug="27_tempo_resposta_mediana",
                title="Tempo de resposta (mediana) por pessoa",
                figure=grafico_barras_por_pessoa(
                    quem_respondeu.sort_values("mediana_minutos"), "mediana_minutos",
                    "Quanto tempo cada pessoa demora para responder, em geral",
                    "Minutos até responder (mediana)", ctx.color_map, formato_valor="{:.1f}",
                ),
            )
        )
        charts.append(
            ChartArtifact(
                slug="27b_percentual_respostas_rapidas",
                title="Respostas rápidas por pessoa",
                figure=grafico_barras_por_pessoa(
                    quem_respondeu.sort_values("percentual_respostas_rapidas", ascending=False),
                    "percentual_respostas_rapidas",
                    f"Respostas dadas em até {LIMITE_RESPOSTA_RAPIDA_SEGUNDOS}s",
                    "% das respostas dessa pessoa", ctx.color_map, formato_valor="{:.0f}%",
                ),
            )
        )

        mais_rapido = quem_respondeu.sort_values("mediana_segundos").iloc[0]
        mais_lento = quem_respondeu.sort_values("mediana_segundos", ascending=False).iloc[0]
        insights.append(
            f"{mais_rapido['nome']} é quem responde mais rápido, em geral: mediana de "
            f"{mais_rapido['mediana_formatada']}."
        )
        if mais_lento["nome"] != mais_rapido["nome"]:
            insights.append(
                f"{mais_lento['nome']} é quem demora mais para responder, em geral: mediana de "
                f"{mais_lento['mediana_formatada']}."
            )
        campea_rapidas = quem_respondeu.sort_values("percentual_respostas_rapidas", ascending=False).iloc[0]
        insights.append(
            f"{campea_rapidas['nome']} é quem mais responde na hora: "
            f"{campea_rapidas['percentual_respostas_rapidas']:.0f}% das respostas em até "
            f"{LIMITE_RESPOSTA_RAPIDA_SEGUNDOS}s."
        )

    # Quem retoma a conversa (iniciou a troca de turno) vs. quem é respondido
    retomou = (
        respostas.groupby("nome", observed=True)
        .size()
        .reindex(ctx.people, fill_value=0)
        .rename("vezes_que_retomou")
        .reset_index()
        .sort_values("vezes_que_retomou", ascending=False)
        .reset_index(drop=True)
    )
    foi_respondido = (
        respostas.groupby("nome_anterior", observed=True)
        .size()
        .reindex(ctx.people, fill_value=0)
        .rename("vezes_que_foi_respondido")
        .reset_index()
        .rename(columns={"nome_anterior": "nome"})
        .sort_values("vezes_que_foi_respondido", ascending=False)
        .reset_index(drop=True)
    )

    charts.append(
        ChartArtifact(
            slug="27c_quem_retoma_conversa",
            title="Quem mais retoma a conversa",
            figure=grafico_barras_por_pessoa(
                retomou, "vezes_que_retomou",
                "Quantas vezes cada pessoa voltou a falar depois da outra pessoa",
                "Quantidade de vezes", ctx.color_map,
            ),
        )
    )
    charts.append(
        ChartArtifact(
            slug="27d_quem_e_mais_respondido",
            title="Quem mais é respondido",
            figure=grafico_barras_por_pessoa(
                foi_respondido, "vezes_que_foi_respondido",
                "Quantas vezes a mensagem de cada pessoa foi seguida de resposta da outra",
                "Quantidade de vezes", ctx.color_map,
            ),
        )
    )
    tabelas["quem_retoma_conversa"] = retomou
    tabelas["quem_e_mais_respondido"] = foi_respondido

    lider_retoma = retomou.iloc[0]
    lider_respondido = foi_respondido.iloc[0]
    insights.append(
        f"{lider_retoma['nome']} é quem mais retoma a conversa depois da outra pessoa falar: "
        f"{formatar_numero(lider_retoma['vezes_que_retomou'])} vezes."
    )
    insights.append(
        f"{lider_respondido['nome']} é quem mais recebe resposta da outra pessoa: "
        f"{formatar_numero(lider_respondido['vezes_que_foi_respondido'])} vezes."
    )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro=(
            "Quanto tempo cada pessoa demora para responder dentro de uma conversa já em "
            "andamento, e quem costuma retomar a palavra depois da outra pessoa falar."
        ),
    )
