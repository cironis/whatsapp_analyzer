"""Volume de texto: quem escreve mais caracteres e mensagens mais longas."""

from __future__ import annotations

from ..chart_common import grafico_barras_por_pessoa
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_numero

KEY = "caracteres"
TITLE = "Volume de texto"
ICON = "texto"
REQUIRES_MEDIA = False


def run(ctx) -> AnalysisResult:
    df = ctx.df
    texto = df.loc[~df["arquivo_midia"]]

    total_por_pessoa = (
        texto.groupby("nome", observed=True)["quantidade_caracteres"]
        .sum()
        .reset_index(name="total_caracteres")
        .sort_values("total_caracteres", ascending=False)
        .reset_index(drop=True)
    )

    media_por_pessoa = (
        texto.groupby("nome", observed=True)["quantidade_caracteres"]
        .mean()
        .round(1)
        .reset_index(name="media_caracteres")
        .sort_values("media_caracteres", ascending=False)
        .reset_index(drop=True)
    )

    charts = [
        ChartArtifact(
            slug="05_total_caracteres_por_pessoa",
            title="Total de caracteres por pessoa",
            figure=grafico_barras_por_pessoa(
                total_por_pessoa, "total_caracteres", "Total de caracteres enviados",
                "Total de caracteres", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="06_media_caracteres_por_pessoa",
            title="Média de caracteres por mensagem",
            figure=grafico_barras_por_pessoa(
                media_por_pessoa, "media_caracteres", "Média de caracteres por mensagem",
                "Caracteres (média)", ctx.color_map, formato_valor="{:.1f}",
            ),
        ),
    ]

    campeao_volume = total_por_pessoa.iloc[0]
    campeao_prolixo = media_por_pessoa.iloc[0]

    insights = [
        f"{campeao_volume['nome']} escreveu mais no total: "
        f"{formatar_numero(campeao_volume['total_caracteres'])} caracteres.",
        f"{campeao_prolixo['nome']} manda as mensagens mais longas, "
        f"com {campeao_prolixo['media_caracteres']:.0f} caracteres em média.",
    ]

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables={
            "total_caracteres_por_pessoa": total_por_pessoa,
            "media_caracteres_por_pessoa": media_por_pessoa,
        },
        charts=charts,
        insights=insights,
        intro="Quem escreve mais e quem manda as mensagens mais longas.",
    )
