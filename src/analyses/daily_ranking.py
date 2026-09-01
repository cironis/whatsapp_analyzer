"""Quantidade de dias em que cada pessoa teve o maior número de mensagens,
caracteres, áudios ou figurinhas.
"""

from __future__ import annotations

from ..chart_common import grafico_barras_por_pessoa
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_numero
from ._daywinner import METRICAS, ranking_dias_vencidos, vencedores_por_dia

KEY = "ranking_dias"
TITLE = "Ranking de dias"
ICON = "trofeu"
REQUIRES_MEDIA = False

_NUMERACAO_SLUG = {"mensagens": "18", "caracteres": "19", "audio": "20", "figurinha": "21"}


def run(ctx) -> AnalysisResult:
    tabelas = {}
    charts = []
    insights = []

    for metrica in METRICAS:
        if metrica["requer_midia"] and not ctx.has_media:
            continue

        vencedores = vencedores_por_dia(ctx.df, metrica["chave"])
        ranking = ranking_dias_vencidos(vencedores, ctx.people)

        if ranking["dias_vencidos"].sum() == 0:
            continue

        slug = _NUMERACAO_SLUG[metrica["chave"]]
        tabelas[f"dias_com_mais_{metrica['chave']}"] = ranking

        charts.append(
            ChartArtifact(
                slug=f"{slug}_dias_com_mais_{metrica['chave']}",
                title=f"Dias com mais {metrica['plural']}",
                figure=grafico_barras_por_pessoa(
                    ranking, "dias_vencidos", f"Dias com mais {metrica['plural']}",
                    "Quantidade de dias", ctx.color_map,
                ),
            )
        )

        lider = ranking.iloc[0]
        insights.append(
            f"{lider['nome']}: {formatar_numero(lider['dias_vencidos'])} dias com mais {metrica['rotulo']}."
        )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro="Em quantos dias cada pessoa teve o maior número de mensagens, caracteres, áudios ou figurinhas.",
    )
