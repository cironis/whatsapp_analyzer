"""Quem puxa e quem encerra as conversas, a maior sequência de dias ativos,
médias por conversa (mensagens e figurinhas) e os recordes de conversa mais
longa — por duração e por quantidade de mensagens.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from ..chart_common import grafico_barras_por_pessoa
from ..colors import BRAND
from ..enrich import (
    MAPA_DIAS_SEMANA,
    maior_sequencia_do_grupo_com_periodo,
    maior_sequencia_por_pessoa,
    resumo_por_conversa,
    sequencia_atual_por_pessoa,
)
from ..models import AnalysisResult, ChartArtifact
from ..style import FIGSIZE_PADRAO, estilizar_eixo, rodape_assinatura, rotular_barras
from ..utils import formatar_duracao_extensa, formatar_numero, truncar

KEY = "conversas"
TITLE = "Conversas e sequências"
ICON = "faisca"
REQUIRES_MEDIA = False


def _grafico_sequencia_atual_vs_recorde(tabela: pd.DataFrame, titulo: str):
    """Duas barras por pessoa: sequência de dias consecutivos em andamento
    agora vs. o recorde histórico dela — para ver quem está perto de bater
    o próprio recorde.
    """

    largura = max(FIGSIZE_PADRAO[0], 1.3 * len(tabela) + 3)
    fig, ax = plt.subplots(figsize=(largura, FIGSIZE_PADRAO[1]))

    posicoes = range(len(tabela))
    largura_barra = 0.34

    ax.bar(
        [p - largura_barra / 2 for p in posicoes], tabela["sequencia_atual"],
        width=largura_barra, color=BRAND["accent"], label="Sequência atual", zorder=3,
    )
    ax.bar(
        [p + largura_barra / 2 for p in posicoes], tabela["maximo_dias_consecutivos"],
        width=largura_barra, color=BRAND["primary"], label="Recorde histórico", zorder=3,
    )

    ax.set_title(titulo)
    ax.set_ylabel("Dias consecutivos")
    ax.set_xticks(list(posicoes))
    ax.set_xticklabels([truncar(n, 16) for n in tabela["nome"]])
    topo = max(tabela["sequencia_atual"].max(), tabela["maximo_dias_consecutivos"].max(), 1)
    ax.set_ylim(0, topo * 1.22)
    estilizar_eixo(ax)
    rotular_barras(ax, "{:.0f}")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def _pessoas_da_conversa(df: pd.DataFrame, numero_conversa: int, people: list) -> pd.DataFrame:
    """Quantas mensagens cada pessoa mandou em uma conversa específica."""

    conversa = df.loc[df["numero_conversa"] == numero_conversa]

    return (
        conversa.groupby("nome", observed=True)
        .size()
        .reindex(people, fill_value=0)
        .reset_index(name="quantidade_mensagens")
        .sort_values("quantidade_mensagens", ascending=False)
        .reset_index(drop=True)
    )


def _formatar_periodo_dias(inicio: pd.Timestamp, fim: pd.Timestamp) -> str:
    """Formata o período (datas, sem hora) de uma sequência de dias consecutivos."""

    if inicio.normalize() == fim.normalize():
        return f"em {inicio.strftime('%d/%m/%Y')}"

    return f"de {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"


def _formatar_intervalo(inicio: pd.Timestamp, fim: pd.Timestamp) -> str:
    """Dia(s) da semana e horário de uma conversa, por extenso."""

    if inicio.normalize() == fim.normalize():
        dia_semana = MAPA_DIAS_SEMANA[inicio.dayofweek]
        return (
            f"{dia_semana}, {inicio.strftime('%d/%m/%Y')}, "
            f"das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}"
        )

    return (
        f"de {MAPA_DIAS_SEMANA[inicio.dayofweek]}, {inicio.strftime('%d/%m/%Y %H:%M')} "
        f"até {MAPA_DIAS_SEMANA[fim.dayofweek]}, {fim.strftime('%d/%m/%Y %H:%M')}"
    )


def run(ctx) -> AnalysisResult:
    df = ctx.df

    iniciadas = (
        df.loc[df["primeira_mensagem_conversa"]]
        .groupby("nome", observed=True)
        .size()
        .reset_index(name="conversas_iniciadas")
        .sort_values("conversas_iniciadas", ascending=False)
        .reset_index(drop=True)
    )

    finalizadas = (
        df.loc[df["ultima_mensagem_conversa"]]
        .groupby("nome", observed=True)
        .size()
        .reset_index(name="conversas_finalizadas")
        .sort_values("conversas_finalizadas", ascending=False)
        .reset_index(drop=True)
    )

    sequencias = maior_sequencia_por_pessoa(df)
    tamanho_sequencia_grupo, inicio_sequencia_grupo, fim_sequencia_grupo = maior_sequencia_do_grupo_com_periodo(df)
    dias_possiveis_periodo = int((df["data_calendario"].max() - df["data_calendario"].min()).days + 1)

    sequencia_atual = sequencia_atual_por_pessoa(df)
    comparacao_sequencias = sequencias[["nome", "maximo_dias_consecutivos"]].merge(
        sequencia_atual, on="nome", how="left"
    )
    comparacao_sequencias["sequencia_atual"] = comparacao_sequencias["sequencia_atual"].fillna(0).astype(int)

    resumo = resumo_por_conversa(df)

    media_mensagens_grupo = float(resumo["quantidade_mensagens"].mean())
    media_figurinhas_grupo = float(resumo["quantidade_figurinhas"].mean())

    conversas_por_pessoa = df.groupby("nome", observed=True)["numero_conversa"].nunique()
    mensagens_por_pessoa = df.groupby("nome", observed=True).size()
    figurinhas_por_pessoa = df.groupby("nome", observed=True)["figurinha"].sum()

    media_mensagens_pessoa = (
        (mensagens_por_pessoa / conversas_por_pessoa)
        .reindex(ctx.people)
        .rename("media_mensagens_por_conversa")
        .reset_index()
    )
    media_figurinhas_pessoa = (
        (figurinhas_por_pessoa / conversas_por_pessoa)
        .reindex(ctx.people)
        .rename("media_figurinhas_por_conversa")
        .reset_index()
    )

    linha_duracao = resumo.loc[resumo["duracao_segundos"].idxmax()]
    linha_contagem = resumo.loc[resumo["quantidade_mensagens"].idxmax()]
    mesma_conversa = linha_duracao["numero_conversa"] == linha_contagem["numero_conversa"]

    tabela_pessoas_duracao = _pessoas_da_conversa(df, linha_duracao["numero_conversa"], ctx.people)

    charts = [
        ChartArtifact(
            slug="07_conversas_iniciadas",
            title="Conversas iniciadas por pessoa",
            figure=grafico_barras_por_pessoa(
                iniciadas, "conversas_iniciadas", "Quem mais puxa assunto",
                "Conversas iniciadas", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="08_conversas_finalizadas",
            title="Conversas finalizadas por pessoa",
            figure=grafico_barras_por_pessoa(
                finalizadas, "conversas_finalizadas", "Quem costuma falar por último",
                "Conversas finalizadas", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="09_sequencia_dias_consecutivos",
            title="Maior sequência de dias consecutivos",
            figure=grafico_barras_por_pessoa(
                sequencias, "maximo_dias_consecutivos", "Maior sequência de dias seguidos mandando mensagem",
                f"Dias consecutivos (de {dias_possiveis_periodo} no período)", ctx.color_map,
                formato_valor="{:.0f}" + f"/{dias_possiveis_periodo}",
            ),
            caption=" · ".join(
                f"{linha['nome']}: {_formatar_periodo_dias(linha['sequencia_inicio'], linha['sequencia_fim'])}"
                for _, linha in sequencias.loc[sequencias["maximo_dias_consecutivos"] > 0].iterrows()
            ),
        ),
        ChartArtifact(
            slug="09aa_sequencia_atual_vs_recorde",
            title="Sequência atual vs. recorde, por pessoa",
            figure=_grafico_sequencia_atual_vs_recorde(
                comparacao_sequencias, "Sequência em andamento vs. recorde pessoal",
            ),
        ),
        ChartArtifact(
            slug="09b_media_mensagens_por_conversa",
            title="Média de mensagens por conversa, por pessoa",
            figure=grafico_barras_por_pessoa(
                media_mensagens_pessoa, "media_mensagens_por_conversa",
                "Quantas mensagens cada um manda, em média, por conversa",
                "Mensagens por conversa", ctx.color_map,
                formato_valor="{:.1f}", linha_media=media_mensagens_grupo,
            ),
        ),
        ChartArtifact(
            slug="09d_conversa_mais_longa_duracao",
            title="Conversa mais longa em duração — por pessoa",
            figure=grafico_barras_por_pessoa(
                tabela_pessoas_duracao, "quantidade_mensagens",
                "Quem mais falou na conversa mais longa (em duração)",
                "Mensagens nessa conversa", ctx.color_map,
            ),
        ),
    ]

    tabelas = {
        "conversas_iniciadas": iniciadas,
        "conversas_finalizadas": finalizadas,
        "sequencia_por_pessoa": sequencias,
        "sequencia_atual_vs_recorde": comparacao_sequencias,
        "media_mensagens_por_conversa": media_mensagens_pessoa,
        "conversa_mais_longa_duracao_pessoas": tabela_pessoas_duracao,
    }

    if ctx.has_media:
        charts.append(
            ChartArtifact(
                slug="09c_media_figurinhas_por_conversa",
                title="Média de figurinhas por conversa, por pessoa",
                figure=grafico_barras_por_pessoa(
                    media_figurinhas_pessoa, "media_figurinhas_por_conversa",
                    "Quantas figurinhas cada um manda, em média, por conversa",
                    "Figurinhas por conversa", ctx.color_map,
                    formato_valor="{:.2f}", linha_media=media_figurinhas_grupo,
                ),
            )
        )
        tabelas["media_figurinhas_por_conversa"] = media_figurinhas_pessoa

    quem_inicia = iniciadas.iloc[0]
    quem_finaliza = finalizadas.iloc[0]
    quem_mais_sequencia = sequencias.iloc[0]
    lider_media_mensagens = media_mensagens_pessoa.sort_values(
        "media_mensagens_por_conversa", ascending=False
    ).iloc[0]

    insights = [
        f"{quem_inicia['nome']} iniciou mais conversas: {formatar_numero(quem_inicia['conversas_iniciadas'])} vezes.",
        f"{quem_finaliza['nome']} falou por último mais vezes: {formatar_numero(quem_finaliza['conversas_finalizadas'])}.",
        f"Sequência mais longa do grupo: {formatar_numero(tamanho_sequencia_grupo)}/{dias_possiveis_periodo} dias "
        f"seguidos com mensagem, {_formatar_periodo_dias(inicio_sequencia_grupo, fim_sequencia_grupo)}. "
        f"Recorde individual: {quem_mais_sequencia['nome']}, com "
        f"{formatar_numero(quem_mais_sequencia['maximo_dias_consecutivos'])}/{dias_possiveis_periodo} dias "
        f"({_formatar_periodo_dias(quem_mais_sequencia['sequencia_inicio'], quem_mais_sequencia['sequencia_fim'])}).",
        f"Média do grupo: {media_mensagens_grupo:.1f} mensagens por conversa"
        + (f" e {media_figurinhas_grupo:.2f} figurinhas por conversa." if ctx.has_media else "."),
        f"{lider_media_mensagens['nome']} é quem mais mensagens manda por conversa, em média: "
        f"{lider_media_mensagens['media_mensagens_por_conversa']:.1f}.",
    ]

    em_andamento = comparacao_sequencias.loc[comparacao_sequencias["sequencia_atual"] > 0].sort_values(
        "sequencia_atual", ascending=False
    )
    if not em_andamento.empty:
        lider_atual = em_andamento.iloc[0]
        falta = int(lider_atual["maximo_dias_consecutivos"] - lider_atual["sequencia_atual"])
        if falta <= 0:
            insights.append(
                f"{lider_atual['nome']} está numa sequência atual de {formatar_numero(lider_atual['sequencia_atual'])} "
                "dias — igualando ou já superando o próprio recorde."
            )
        else:
            insights.append(
                f"{lider_atual['nome']} está numa sequência atual de {formatar_numero(lider_atual['sequencia_atual'])} dias — "
                f"faltam {formatar_numero(falta)} para igualar o recorde pessoal de "
                f"{formatar_numero(lider_atual['maximo_dias_consecutivos'])}."
            )

    if ctx.has_media:
        lider_media_figurinhas = media_figurinhas_pessoa.sort_values(
            "media_figurinhas_por_conversa", ascending=False
        ).iloc[0]
        insights.append(
            f"{lider_media_figurinhas['nome']} é quem mais figurinhas manda por conversa, em média: "
            f"{lider_media_figurinhas['media_figurinhas_por_conversa']:.2f}."
        )

    top_duracao = tabela_pessoas_duracao.iloc[0]
    participantes_duracao = int((tabela_pessoas_duracao["quantidade_mensagens"] > 0).sum())

    insights.append(
        f"Conversa mais longa em duração: {formatar_duracao_extensa(linha_duracao['duracao_segundos'])} seguidas, "
        f"{_formatar_intervalo(linha_duracao['inicio'], linha_duracao['fim'])} "
        f"({formatar_numero(linha_duracao['quantidade_mensagens'])} mensagens, {participantes_duracao} pessoas). "
        f"{top_duracao['nome']} foi quem mais mandou mensagem nela: {formatar_numero(top_duracao['quantidade_mensagens'])}."
    )

    if mesma_conversa:
        insights.append("Essa mesma conversa também foi a que teve mais mensagens no total.")
    else:
        tabela_pessoas_contagem = _pessoas_da_conversa(df, linha_contagem["numero_conversa"], ctx.people)
        top_contagem = tabela_pessoas_contagem.iloc[0]
        participantes_contagem = int((tabela_pessoas_contagem["quantidade_mensagens"] > 0).sum())

        charts.append(
            ChartArtifact(
                slug="09e_conversa_mais_longa_mensagens",
                title="Conversa com mais mensagens — por pessoa",
                figure=grafico_barras_por_pessoa(
                    tabela_pessoas_contagem, "quantidade_mensagens",
                    "Quem mais falou na conversa com mais mensagens",
                    "Mensagens nessa conversa", ctx.color_map,
                ),
            )
        )
        tabelas["conversa_mais_longa_mensagens_pessoas"] = tabela_pessoas_contagem

        insights.append(
            f"Conversa com mais mensagens: {formatar_numero(linha_contagem['quantidade_mensagens'])} mensagens em "
            f"{formatar_duracao_extensa(linha_contagem['duracao_segundos'])}, "
            f"{_formatar_intervalo(linha_contagem['inicio'], linha_contagem['fim'])} ({participantes_contagem} pessoas). "
            f"{top_contagem['nome']} foi quem mais mandou mensagem nela: {formatar_numero(top_contagem['quantidade_mensagens'])}."
        )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro="Uma conversa nova começa após 1h de silêncio. Quem inicia, quem encerra, "
        "as sequências de dias seguidos (recorde e a que está em andamento agora), as "
        "médias de mensagens e figurinhas por conversa e os recordes de conversa mais "
        "longa — por duração e por quantidade de mensagens.",
    )
