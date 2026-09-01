"""Evolução recente: mensagens e caracteres por dia, pessoa a pessoa."""

from __future__ import annotations

import pandas as pd

from ..chart_common import grafico_linha_temporal
from ..models import AnalysisResult, ChartArtifact

KEY = "linha_do_tempo"
TITLE = "Últimos 30 dias"
ICON = "relogio"
REQUIRES_MEDIA = False

QUANTIDADE_DIAS = 30


def run(ctx) -> AnalysisResult:
    df = ctx.df

    data_final = df["data_calendario"].max()
    data_inicial = data_final - pd.Timedelta(days=QUANTIDADE_DIAS - 1)

    periodo = pd.date_range(start=data_inicial, end=data_final, freq="D")
    grade = pd.MultiIndex.from_product([periodo, ctx.people], names=["data_calendario", "nome"]).to_frame(index=False)

    recorte = df.loc[df["data_calendario"].between(data_inicial, data_final)]

    mensagens = (
        recorte.groupby(["data_calendario", "nome"], observed=True)
        .size()
        .reset_index(name="quantidade_mensagens")
    )
    mensagens = grade.merge(mensagens, on=["data_calendario", "nome"], how="left")
    mensagens["quantidade_mensagens"] = mensagens["quantidade_mensagens"].fillna(0).astype(int)

    caracteres = (
        recorte.groupby(["data_calendario", "nome"], observed=True)["quantidade_caracteres"]
        .sum()
        .reset_index(name="total_caracteres")
    )
    caracteres = grade.merge(caracteres, on=["data_calendario", "nome"], how="left")
    caracteres["total_caracteres"] = caracteres["total_caracteres"].fillna(0).astype(int)

    charts = [
        ChartArtifact(
            slug="10_mensagens_ultimos_30_dias",
            title="Mensagens por dia — últimos 30 dias",
            figure=grafico_linha_temporal(
                mensagens, "data_calendario", "quantidade_mensagens", "nome",
                "Mensagens por dia e pessoa — últimos 30 dias",
                "Quantidade de mensagens", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="11_caracteres_ultimos_30_dias",
            title="Caracteres por dia — últimos 30 dias",
            figure=grafico_linha_temporal(
                caracteres, "data_calendario", "total_caracteres", "nome",
                "Caracteres enviados por dia e pessoa — últimos 30 dias",
                "Quantidade de caracteres", ctx.color_map,
            ),
        ),
    ]

    insights = [
        f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}.",
    ]

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables={"mensagens_30_dias": mensagens, "caracteres_30_dias": caracteres},
        charts=charts,
        insights=insights,
        intro="Mensagens e caracteres por dia, pessoa a pessoa, no último mês do histórico.",
    )
