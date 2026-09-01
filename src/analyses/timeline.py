"""Evolução recente: mensagens e caracteres por dia, pessoa a pessoa.

Por padrão mostra os últimos 30 dias disponíveis no histórico. Quando o
pipeline filtra a análise por um mês/ano específico, `ctx` chega com a
janela e o título já calculados para o mês inteiro (ver `pipeline.py`).
"""

from __future__ import annotations

import pandas as pd

from ..chart_common import grafico_linha_temporal
from ..models import AnalysisResult, ChartArtifact

KEY = "linha_do_tempo"
TITLE = "Evolução recente"
ICON = "relogio"
REQUIRES_MEDIA = False

QUANTIDADE_DIAS = 30


def run(ctx) -> AnalysisResult:
    df = ctx.df

    if ctx.janela_recente_inicio is not None and ctx.janela_recente_fim is not None:
        data_inicial, data_final = ctx.janela_recente_inicio, ctx.janela_recente_fim
    else:
        data_final = df["data_calendario"].max()
        data_inicial = max(
            data_final - pd.Timedelta(days=QUANTIDADE_DIAS - 1), df["data_calendario"].min()
        )

    titulo_janela = ctx.janela_recente_titulo or f"Últimos {QUANTIDADE_DIAS} dias"

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
            title=f"Mensagens por dia — {titulo_janela}",
            figure=grafico_linha_temporal(
                mensagens, "data_calendario", "quantidade_mensagens", "nome",
                f"Mensagens por dia e pessoa — {titulo_janela}",
                "Quantidade de mensagens", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="11_caracteres_ultimos_30_dias",
            title=f"Caracteres por dia — {titulo_janela}",
            figure=grafico_linha_temporal(
                caracteres, "data_calendario", "total_caracteres", "nome",
                f"Caracteres enviados por dia e pessoa — {titulo_janela}",
                "Quantidade de caracteres", ctx.color_map,
            ),
        ),
    ]

    insights = [
        f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}.",
    ]

    return AnalysisResult(
        key=KEY,
        title=titulo_janela,
        icon=ICON,
        tables={"mensagens_30_dias": mensagens, "caracteres_30_dias": caracteres},
        charts=charts,
        insights=insights,
        intro=f"Mensagens e caracteres por dia, pessoa a pessoa — {titulo_janela}.",
    )
