"""Nuvem de palavras: geral do grupo e uma por pessoa."""

from __future__ import annotations

import re

import matplotlib.pyplot as plt
from wordcloud import STOPWORDS, WordCloud

from ..colors import BRAND
from ..models import AnalysisResult, ChartArtifact
from ..style import rodape_assinatura
from ..utils import normalizar_nome_arquivo

KEY = "nuvem_palavras"
TITLE = "Nuvem de palavras"
ICON = "texto"
REQUIRES_MEDIA = False

STOPWORDS_PORTUGUES = {
    "a", "à", "agora", "aí", "ainda", "alguém", "algum", "alguma", "algumas",
    "alguns", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo",
    "as", "até", "bem", "cada", "como", "com", "da", "das", "de", "dela",
    "dele", "deles", "depois", "do", "dos", "e", "é", "ela", "elas", "ele",
    "eles", "em", "então", "era", "essa", "essas", "esse", "esses", "esta",
    "está", "estão", "estas", "este", "estes", "eu", "foi", "for", "isso",
    "isto", "já", "lá", "mais", "mas", "me", "mesmo", "meu", "minha", "muito",
    "na", "não", "nas", "nem", "no", "nos", "nós", "o", "os", "ou", "para",
    "pela", "pelas", "pelo", "pelos", "por", "porque", "pra", "pro", "qual",
    "quando", "que", "quem", "se", "sem", "ser", "seu", "só", "sua", "também",
    "te", "tem", "têm", "ter", "tu", "tudo", "um", "uma", "umas", "uns", "vai",
    "você", "vocês", "vou", "www", "http", "https",
}


def _preparar_texto(mensagens) -> str:
    texto = " ".join(mensagens.fillna("").astype(str).tolist())
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)
    texto = re.sub(r"\S+@\S+", " ", texto)
    texto = re.sub(r"\b\d+\b", " ", texto)
    texto = re.sub(r"[^\wÀ-ÿ'-]+", " ", texto, flags=re.UNICODE)
    return re.sub(r"\s+", " ", texto).strip()


def _grafico_nuvem(texto: str, titulo: str, cor_destaque: str = BRAND["primary"]):
    stopwords = set(STOPWORDS) | STOPWORDS_PORTUGUES

    nuvem = WordCloud(
        width=1600, height=900, background_color="white",
        color_func=_gerar_paleta_func(cor_destaque),
        stopwords=stopwords, collocations=False, max_words=150,
        prefer_horizontal=0.92, random_state=42,
    )

    try:
        nuvem.generate(texto or "conversa")
    except ValueError:
        nuvem.generate("conversa")

    fig, ax = plt.subplots(figsize=(13, 7.3))
    ax.imshow(nuvem, interpolation="bilinear")
    ax.set_title(titulo, fontsize=17, fontweight="bold", pad=16)
    ax.axis("off")
    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def _gerar_paleta_func(cor_base: str):
    import colorsys

    r, g, b = (int(cor_base[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    def _func(word=None, font_size=None, position=None, orientation=None, random_state=None, **kwargs):
        rng = random_state or __import__("random")
        luminosidade = max(0.22, min(0.62, l + rng.uniform(-0.18, 0.18)))
        r2, g2, b2 = colorsys.hls_to_rgb(h, luminosidade, min(1.0, s + 0.1))
        return f"rgb({int(r2 * 255)},{int(g2 * 255)},{int(b2 * 255)})"

    return _func


def run(ctx) -> AnalysisResult:
    df = ctx.df
    texto_ok = df.loc[~df["arquivo_midia"]]

    texto_geral = _preparar_texto(texto_ok["mensagem"])
    charts = [
        ChartArtifact(
            slug="16_nuvem_palavras_geral",
            title="Nuvem de palavras — grupo inteiro",
            figure=_grafico_nuvem(texto_geral, "Nuvem de palavras — conversa inteira"),
        )
    ]

    for nome in ctx.people:
        texto_pessoa = _preparar_texto(texto_ok.loc[texto_ok["nome"] == nome, "mensagem"])
        cor = ctx.color_map.get(nome, BRAND["primary"])
        charts.append(
            ChartArtifact(
                slug=f"17_nuvem_palavras_{normalizar_nome_arquivo(nome)}",
                title=f"Nuvem de palavras — {nome}",
                figure=_grafico_nuvem(texto_pessoa, f"Nuvem de palavras — {nome}", cor),
            )
        )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        charts=charts,
        insights=["As palavras mais repetidas por cada pessoa e pelo grupo como um todo."],
        intro="As palavras mais usadas, com o tamanho proporcional à frequência.",
    )
