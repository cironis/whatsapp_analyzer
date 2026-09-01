"""Quando cada pessoa mais fala: mensagens por dia da semana e por hora do dia,
pessoa a pessoa (complementa a visão de grupo já existente em `messages.py`).
"""

from __future__ import annotations

import pandas as pd

from ..chart_common import grafico_linhas_por_categoria
from ..enrich import ORDEM_DIAS_SEMANA
from ..models import AnalysisResult, ChartArtifact

KEY = "atividade_por_pessoa"
TITLE = "Quando cada pessoa mais fala"
ICON = "calendario"
REQUIRES_MEDIA = False

LIMITE_INSIGHTS_PESSOA = 8


def run(ctx) -> AnalysisResult:
    df = ctx.df

    pivot_dia = (
        pd.crosstab(df["nome"], df["dia_semana"])
        .reindex(index=ctx.people, columns=ORDEM_DIAS_SEMANA, fill_value=0)
    )
    pivot_hora = (
        pd.crosstab(df["nome"], df["hora_dia"])
        .reindex(index=ctx.people, columns=range(24), fill_value=0)
    )

    longo_dia = (
        pivot_dia.reset_index()
        .melt(id_vars="nome", var_name="dia_semana", value_name="quantidade_mensagens")
    )
    longo_hora = (
        pivot_hora.reset_index()
        .melt(id_vars="nome", var_name="hora_dia", value_name="quantidade_mensagens")
    )

    charts = [
        ChartArtifact(
            slug="17_mensagens_por_pessoa_dia_semana",
            title="Mensagens por dia da semana, por pessoa",
            figure=grafico_linhas_por_categoria(
                longo_dia, "dia_semana", "quantidade_mensagens", "nome",
                "Quando cada pessoa mais fala — dia da semana",
                "Dia da semana", "Quantidade de mensagens", ctx.color_map,
                ordem_x=ORDEM_DIAS_SEMANA,
            ),
        ),
        ChartArtifact(
            slug="17b_mensagens_por_pessoa_hora",
            title="Mensagens por hora do dia, por pessoa",
            figure=grafico_linhas_por_categoria(
                longo_hora, "hora_dia", "quantidade_mensagens", "nome",
                "Quando cada pessoa mais fala — hora do dia",
                "Hora do dia", "Quantidade de mensagens", ctx.color_map,
                ordem_x=list(range(24)),
            ),
        ),
    ]

    resumo = pd.DataFrame({"nome": pivot_dia.index})
    resumo["dia_mais_ativo"] = pivot_dia.idxmax(axis=1).values
    resumo["mensagens_no_dia_mais_ativo"] = pivot_dia.max(axis=1).values
    resumo["hora_mais_ativa"] = pivot_hora.idxmax(axis=1).values
    resumo["mensagens_na_hora_mais_ativa"] = pivot_hora.max(axis=1).values
    resumo["total_mensagens"] = pivot_dia.sum(axis=1).values
    resumo = resumo.sort_values("total_mensagens", ascending=False).reset_index(drop=True)

    insights = []
    for _, linha in resumo.loc[resumo["total_mensagens"] > 0].head(LIMITE_INSIGHTS_PESSOA).iterrows():
        insights.append(
            f"{linha['nome']} fala mais aos {linha['dia_mais_ativo']}, "
            f"principalmente por volta das {int(linha['hora_mais_ativa'])}h."
        )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables={
            "mensagens_por_pessoa_dia_semana": pivot_dia.reset_index(),
            "mensagens_por_pessoa_hora": pivot_hora.reset_index(),
            "resumo_horario_por_pessoa": resumo.drop(columns="total_mensagens"),
        },
        charts=charts,
        insights=insights,
        intro="Em que dias da semana e horários cada pessoa costuma mandar mais mensagens.",
    )
