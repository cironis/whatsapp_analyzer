"""Quantidade de mídia enviada por pessoa (funciona com ou sem os arquivos).

Sabemos que uma mensagem é mídia mesmo sem o arquivo em si (o texto vem
como `<Media omitted>`). Já a quebra por tipo (imagem/áudio/figurinha/vídeo)
só é possível quando o .zip inclui os arquivos de verdade — nesse caso o
gráfico de tipos aparece; caso contrário, mostramos só o total.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from ..chart_common import grafico_barras_por_pessoa
from ..colors import BRAND, PERSON_PALETTE
from ..models import AnalysisResult, ChartArtifact
from ..style import estilizar_eixo, rodape_assinatura
from ..utils import formatar_numero, truncar

KEY = "midia_geral"
TITLE = "Mídia enviada"
ICON = "clipe"
REQUIRES_MEDIA = False

ROTULOS_TIPO = {
    "imagem": "Imagem",
    "figurinha": "Figurinha",
    "audio": "Áudio",
    "video": "Vídeo",
    "documento": "Documento",
    "contato": "Contato",
    None: "Não identificado",
}

CORES_TIPO = {
    "imagem": PERSON_PALETTE[0],
    "figurinha": PERSON_PALETTE[3],
    "audio": PERSON_PALETTE[2],
    "video": PERSON_PALETTE[4],
    "documento": PERSON_PALETTE[7],
    "contato": PERSON_PALETTE[6],
    None: BRAND["line"],
}


def _grafico_tipos_empilhado(tabela_pivot, titulo):
    fig, ax = plt.subplots(figsize=(max(9, 1.1 * len(tabela_pivot) + 3), 5.6))

    base = None
    for tipo in tabela_pivot.columns:
        valores = tabela_pivot[tipo]
        ax.bar(
            [truncar(n, 16) for n in tabela_pivot.index], valores,
            bottom=base, label=ROTULOS_TIPO.get(tipo, str(tipo)),
            color=CORES_TIPO.get(tipo, BRAND["muted"]), width=0.6, zorder=3,
        )
        base = valores if base is None else base + valores

    ax.set_title(titulo)
    ax.set_ylabel("Quantidade de arquivos")
    estilizar_eixo(ax)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def run(ctx) -> AnalysisResult:
    df = ctx.df
    midia = df.loc[df["arquivo_midia"]]

    total_por_pessoa = (
        midia.groupby("nome", observed=True)
        .size()
        .reindex(ctx.people, fill_value=0)
        .reset_index(name="quantidade_midias")
        .rename(columns={"index": "nome"})
        .sort_values("quantidade_midias", ascending=False)
        .reset_index(drop=True)
    )

    charts = [
        ChartArtifact(
            slug="12_midias_por_pessoa",
            title="Arquivos de mídia por pessoa",
            figure=grafico_barras_por_pessoa(
                total_por_pessoa, "quantidade_midias", "Arquivos de mídia enviados por pessoa",
                "Quantidade de mídias", ctx.color_map,
            ),
        ),
    ]

    tabelas = {"midias_por_pessoa": total_por_pessoa}
    lider = total_por_pessoa.iloc[0]
    insights = [
        f"{lider['nome']} enviou mais mídia no total: {formatar_numero(lider['quantidade_midias'])} arquivos.",
    ]

    if ctx.has_media:
        pivot = (
            midia.groupby(["nome", "tipo_midia"], observed=True)
            .size()
            .unstack(fill_value=0)
            .reindex(ctx.people, fill_value=0)
        )
        ordem_tipos = [t for t in ["imagem", "figurinha", "audio", "video", "documento", "contato", None] if t in pivot.columns]
        pivot = pivot[ordem_tipos]

        charts.append(
            ChartArtifact(
                slug="13_midias_por_tipo_e_pessoa",
                title="Mídia por tipo e pessoa",
                figure=_grafico_tipos_empilhado(pivot, "Mídia enviada por tipo, pessoa a pessoa"),
            )
        )
        tabelas["midias_por_tipo_e_pessoa"] = pivot.reset_index()

        if "figurinha" in pivot.columns:
            campea_figurinha = pivot["figurinha"].idxmax()
            insights.append(
                f"{campea_figurinha} enviou mais figurinhas: {formatar_numero(pivot['figurinha'].max())}."
            )
        if "audio" in pivot.columns:
            campea_audio = pivot["audio"].idxmax()
            insights.append(
                f"{campea_audio} enviou mais áudios: {formatar_numero(pivot['audio'].max())}."
            )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro="Quantidade de fotos, vídeos, áudios, figurinhas e documentos enviados por cada pessoa.",
    )
