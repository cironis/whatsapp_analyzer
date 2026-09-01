"""Análises que só existem quando o .zip inclui os arquivos de mídia:
duração dos áudios e as figurinhas mais repetidas por pessoa.

Figurinhas costumam se repetir (o mesmo pacote é reaproveitado); fotos
quase nunca se repetem, então o ranking usa figurinhas, não fotos.
"""

from __future__ import annotations

import tempfile
import textwrap
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image as PILImage

from ..chart_common import grafico_barras_por_pessoa
from ..colors import BRAND
from ..models import AnalysisResult, ChartArtifact
from ..style import rodape_assinatura
from ..utils import formatar_duracao, formatar_numero

try:
    from mutagen import File as MutagenFile
except ImportError:  # pragma: no cover - mutagen está no requirements.txt
    MutagenFile = None

KEY = "midia_detalhada"
TITLE = "Figurinhas e áudios"
ICON = "figurinha"
REQUIRES_MEDIA = True

QUANTIDADE_TOP_FIGURINHAS = 5


def _duracao_audio(caminho: Path):
    if MutagenFile is None:
        return None

    try:
        audio = MutagenFile(str(caminho))
        if audio is None or not hasattr(audio, "info"):
            return None
        return float(getattr(audio.info, "length", None) or 0) or None
    except Exception:
        return None


def _medir_duracoes_audio(df: pd.DataFrame, media_store) -> pd.DataFrame:
    audios = df.loc[df["arquivo_audio"]].copy()

    if audios.empty:
        return audios

    duracoes = {}
    with tempfile.TemporaryDirectory() as pasta:
        pasta = Path(pasta)
        for indice, nome_arquivo in enumerate(audios["nome_arquivo_anexo"].dropna().unique(), start=1):
            conteudo = media_store.read(nome_arquivo)
            if conteudo is None:
                continue
            extensao = Path(nome_arquivo).suffix or ".opus"
            caminho_temporario = pasta / f"audio_{indice:05d}{extensao}"
            caminho_temporario.write_bytes(conteudo)
            duracoes[nome_arquivo.casefold()] = _duracao_audio(caminho_temporario)

    audios["duracao_audio_segundos"] = (
        audios["nome_arquivo_anexo"].str.casefold().map(duracoes)
    )

    return audios


def _top_figurinhas_por_pessoa(df: pd.DataFrame, media_store, limite: int):
    figurinhas = df.loc[df["tipo_midia"] == "figurinha", ["nome", "nome_arquivo_anexo"]].dropna()

    if figurinhas.empty:
        return pd.DataFrame(columns=["nome", "posicao", "arquivo", "quantidade_envios"]), {}

    figurinhas = figurinhas.loc[figurinhas["nome_arquivo_anexo"].apply(media_store.contains)]

    if figurinhas.empty:
        return pd.DataFrame(columns=["nome", "posicao", "arquivo", "quantidade_envios"]), {}

    contagem = (
        figurinhas.groupby(["nome", "nome_arquivo_anexo"], observed=True)
        .size()
        .reset_index(name="quantidade_envios")
        .sort_values(["nome", "quantidade_envios"], ascending=[True, False])
    )

    contagem = contagem.groupby("nome", observed=True).head(limite).copy()
    contagem["posicao"] = contagem.groupby("nome", observed=True).cumcount() + 1
    contagem = contagem.rename(columns={"nome_arquivo_anexo": "arquivo"})

    miniaturas = {
        arquivo: media_store.read(arquivo)
        for arquivo in contagem["arquivo"].unique()
    }

    return contagem[["nome", "posicao", "arquivo", "quantidade_envios"]].reset_index(drop=True), miniaturas


def _grafico_galeria(tabela: pd.DataFrame, miniaturas: dict, limite: int):
    pessoas = tabela["nome"].drop_duplicates().tolist()

    if not pessoas:
        fig, ax = plt.subplots(figsize=(9, 3))
        ax.axis("off")
        ax.text(0.5, 0.5, "Nenhuma figurinha repetida encontrada no .zip.", ha="center", va="center")
        return fig

    fig, eixos = plt.subplots(
        nrows=len(pessoas), ncols=limite, figsize=(3.4 * limite, 3.5 * len(pessoas)), squeeze=False,
    )
    fig.suptitle("Figurinhas mais repetidas por pessoa", fontsize=18, fontweight="bold", y=0.995)

    for linha, nome in enumerate(pessoas):
        grupo = tabela.loc[tabela["nome"] == nome].sort_values("posicao").reset_index(drop=True)

        for coluna in range(limite):
            eixo = eixos[linha, coluna]
            eixo.set_facecolor("#F7F8FA")
            eixo.set_xticks([])
            eixo.set_yticks([])
            for borda in eixo.spines.values():
                borda.set_color(BRAND["line"])

            if coluna >= len(grupo):
                eixo.axis("off")
                continue

            registro = grupo.iloc[coluna]
            conteudo = miniaturas.get(registro["arquivo"])

            try:
                imagem = PILImage.open(BytesIO(conteudo)).convert("RGBA")
                eixo.imshow(imagem)
            except Exception:
                eixo.text(0.5, 0.5, "Indisponível", ha="center", va="center", transform=eixo.transAxes)

            eixo.set_title(f"{int(registro['posicao'])}º · {int(registro['quantidade_envios'])}x", fontsize=10.5, fontweight="bold")

        eixos[linha, 0].text(
            -0.25, 0.5, textwrap.fill(str(nome), width=16), transform=eixos[linha, 0].transAxes,
            ha="right", va="center", fontsize=11.5, fontweight="bold", color=BRAND["ink"],
        )

    fig.subplots_adjust(left=0.16, right=0.98, top=0.92, bottom=0.03, hspace=0.35, wspace=0.12)
    rodape_assinatura(fig)

    return fig


def run(ctx) -> AnalysisResult:
    tabelas = {}
    charts = []
    insights = []

    audios = _medir_duracoes_audio(ctx.df, ctx.media_store)

    if not audios.empty:
        audios["duracao_audio_formatada"] = audios["duracao_audio_segundos"].apply(formatar_duracao)

        resumo_audio = (
            audios.groupby("nome", observed=True)
            .agg(
                quantidade_audios=("arquivo_audio", "size"),
                tempo_total_segundos=("duracao_audio_segundos", "sum"),
            )
            .reindex(ctx.people, fill_value=0)
            .reset_index()
        )
        resumo_audio["tempo_total_minutos"] = (resumo_audio["tempo_total_segundos"] / 60).round(2)
        resumo_audio["tempo_total_formatado"] = resumo_audio["tempo_total_segundos"].apply(formatar_duracao)
        resumo_audio = resumo_audio.sort_values("tempo_total_segundos", ascending=False).reset_index(drop=True)

        charts.append(
            ChartArtifact(
                slug="14_tempo_audio_por_pessoa",
                title="Tempo total de áudio por pessoa",
                figure=grafico_barras_por_pessoa(
                    resumo_audio, "tempo_total_minutos", "Tempo total de mensagens de áudio",
                    "Minutos de áudio", ctx.color_map, formato_valor="{:.1f}",
                ),
            )
        )
        tabelas["resumo_audio_por_pessoa"] = resumo_audio
        tabelas["audios_detalhados"] = audios[
            ["data", "nome", "nome_arquivo_anexo", "duracao_audio_segundos", "duracao_audio_formatada"]
        ].sort_values("data").reset_index(drop=True)

        campeao_audio = resumo_audio.iloc[0]
        insights.append(
            f"{campeao_audio['nome']} tem mais tempo de áudio: "
            f"{campeao_audio['tempo_total_formatado']} ({formatar_numero(campeao_audio['quantidade_audios'])} áudios)."
        )

    top_figurinhas, miniaturas = _top_figurinhas_por_pessoa(ctx.df, ctx.media_store, QUANTIDADE_TOP_FIGURINHAS)

    if not top_figurinhas.empty:
        charts.append(
            ChartArtifact(
                slug="15_top_figurinhas_por_pessoa",
                title="Figurinhas mais repetidas por pessoa",
                figure=_grafico_galeria(top_figurinhas, miniaturas, QUANTIDADE_TOP_FIGURINHAS),
            )
        )
        tabelas["top_figurinhas_por_pessoa"] = top_figurinhas

    if not charts:
        return AnalysisResult(key=KEY, title=TITLE, icon=ICON)

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro="Duração dos áudios e as figurinhas que mais se repetem, pessoa a pessoa.",
    )
