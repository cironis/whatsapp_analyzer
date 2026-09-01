"""Padrão de atividade: quem manda mais mensagens, quando o grupo fala mais."""

from __future__ import annotations

import pandas as pd

from ..chart_common import grafico_barras_por_pessoa, grafico_barras_simples, grafico_heatmap_dia_hora
from ..enrich import ORDEM_DIAS_SEMANA
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_numero

KEY = "mensagens"
TITLE = "Atividade e mensagens"
ICON = "chat"
REQUIRES_MEDIA = False


def run(ctx) -> AnalysisResult:
    df = ctx.df

    por_pessoa = (
        df.groupby("nome", observed=True)
        .size()
        .reset_index(name="quantidade_mensagens")
        .sort_values("quantidade_mensagens", ascending=False)
        .reset_index(drop=True)
    )

    dia_hora = pd.crosstab(df["dia_semana"], df["hora_dia"]).reindex(
        index=ORDEM_DIAS_SEMANA, columns=range(24), fill_value=0
    )

    por_dia_semana = (
        df.groupby("dia_semana", observed=False)
        .size()
        .reindex(ORDEM_DIAS_SEMANA, fill_value=0)
        .reset_index(name="quantidade_mensagens")
    )

    por_hora = (
        df.groupby("hora_dia", observed=True)
        .size()
        .reindex(range(24), fill_value=0)
        .rename_axis("hora_dia")
        .reset_index(name="quantidade_mensagens")
    )

    charts = [
        ChartArtifact(
            slug="01_mensagens_por_pessoa",
            title="Mensagens por pessoa",
            figure=grafico_barras_por_pessoa(
                por_pessoa, "quantidade_mensagens", "Mensagens por pessoa",
                "Quantidade de mensagens", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="02_heatmap_dia_hora",
            title="Mensagens por dia da semana e hora",
            figure=grafico_heatmap_dia_hora(dia_hora, "Quando o grupo mais conversa"),
        ),
        ChartArtifact(
            slug="03_mensagens_por_dia_semana",
            title="Mensagens por dia da semana",
            figure=grafico_barras_simples(
                por_dia_semana, "dia_semana", "quantidade_mensagens",
                "Mensagens por dia da semana", "Dia da semana", "Quantidade de mensagens",
            ),
        ),
        ChartArtifact(
            slug="04_mensagens_por_hora",
            title="Mensagens por hora do dia",
            figure=grafico_barras_simples(
                por_hora, "hora_dia", "quantidade_mensagens",
                "Mensagens por hora do dia", "Hora do dia", "Quantidade de mensagens",
            ),
        ),
    ]

    lider = por_pessoa.iloc[0]
    dia_mais_ativo = por_dia_semana.sort_values("quantidade_mensagens", ascending=False).iloc[0]
    hora_mais_ativa = int(por_hora.sort_values("quantidade_mensagens", ascending=False).iloc[0]["hora_dia"])

    insights = [
        f"{lider['nome']} é quem mais manda mensagens: {formatar_numero(lider['quantidade_mensagens'])} no total.",
        f"{dia_mais_ativo['dia_semana']} é o dia da semana com mais mensagens.",
        f"O horário de pico da conversa é por volta das {hora_mais_ativa}h.",
    ]

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables={
            "mensagens_por_pessoa": por_pessoa,
            "mensagens_dia_hora": dia_hora,
            "mensagens_por_dia_semana": por_dia_semana,
            "mensagens_por_hora": por_hora,
        },
        charts=charts,
        insights=insights,
        intro="Visão geral de quem fala mais e em que dias e horários a conversa mais acontece.",
    )
