"""Paleta de cores do app: identidade visual e cor consistente por pessoa."""

from __future__ import annotations

# Paleta qualitativa, pensada para permanecer distinguível em impressão e
# para pessoas com daltonismo comum (deuteranopia/protanopia) — ordem
# escolhida para maximizar contraste entre vizinhos.
PERSON_PALETTE = [
    "#1F77B4",  # azul
    "#E45756",  # vermelho coral
    "#2CA858",  # verde
    "#F2A93B",  # laranja/âmbar
    "#7B61B3",  # roxo
    "#17A2B8",  # ciano petróleo
    "#D45DA8",  # rosa
    "#8C6D4F",  # marrom
    "#5B7DB1",  # azul acinzentado
    "#C0524A",  # terracota
    "#4F9D69",  # verde musgo
    "#B08B2C",  # mostarda
    "#9467BD",  # lilás
    "#3F8F8F",  # verde-azulado
    "#C2578D",  # magenta suave
    "#767676",  # cinza neutro (último recurso)
]

NEUTRAL_GRID = "#E7E9EE"  # célula "sem atividade" nos grids estilo GitHub

BRAND = {
    "primary": "#128C7E",   # verde-petróleo do WhatsApp
    "dark": "#075E54",
    "accent": "#25D366",    # verde vivo do WhatsApp
    "ink": "#111827",
    "muted": "#667085",
    "bg": "#F7F8FA",
    "card": "#FFFFFF",
    "line": "#E4E7EC",
}


def build_color_map(people: list) -> dict:
    """Atribui uma cor estável a cada pessoa (ordem alfabética)."""

    pessoas_ordenadas = sorted(people)

    return {
        nome: PERSON_PALETTE[indice % len(PERSON_PALETTE)]
        for indice, nome in enumerate(pessoas_ordenadas)
    }
