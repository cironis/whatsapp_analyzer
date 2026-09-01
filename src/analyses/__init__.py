"""Registro central das análises.

Para adicionar uma análise nova no futuro: crie um módulo aqui com
`KEY`, `TITLE`, `ICON`, `REQUIRES_MEDIA` e uma função `run(ctx) ->
AnalysisResult`, depois inclua o módulo na lista `ANALISES` abaixo, na
ordem em que deve aparecer no PDF e no ZIP.
"""

from . import (
    characters,
    conversations,
    daily_ranking,
    github_grid,
    media_gallery,
    media_stats,
    messages,
    person_activity,
    timeline,
    wordcloud_analysis,
)

ANALISES = [
    messages,
    person_activity,
    characters,
    conversations,
    timeline,
    media_stats,
    daily_ranking,
    github_grid,
    media_gallery,
    wordcloud_analysis,
]
