"""Evolução da conversa ao longo do tempo: quebra mês a mês (quando o
relatório olha o histórico inteiro ou um período longo) ou semana a semana
(quando o relatório está filtrado por um mês específico). A ideia é ver se
alguém está interagindo mais ou menos, e como isso varia com o tempo.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from ..audio import medir_duracoes_audio
from ..chart_common import grafico_barras_por_pessoa, grafico_barras_simples, grafico_linhas_por_categoria
from ..colors import BRAND
from ..enrich import maior_sequencia_consecutiva
from ..models import AnalysisResult, ChartArtifact
from ..style import FIGSIZE_LARGO, FIGSIZE_PADRAO, estilizar_eixo, rodape_assinatura
from ..utils import formatar_numero, truncar

KEY = "evolucao_periodica"
TITLE = "Evolução por período"
ICON = "relogio"
REQUIRES_MEDIA = False

_MESES_ABREV = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}


def _rotulo_mes(periodo: pd.Period) -> str:
    return f"{_MESES_ABREV[periodo.month]}/{str(periodo.year)[2:]}"


def _rotulo_semana(periodo: pd.Period) -> str:
    return f"{periodo.start_time.strftime('%d/%m')}–{periodo.end_time.strftime('%d/%m')}"


def _preparar_periodos(df: pd.DataFrame, granularidade: str) -> tuple[pd.DataFrame, list, dict]:
    """Adiciona a coluna `periodo_rotulo` (categórica, em ordem cronológica) e
    calcula quantos dias de cada período realmente caem dentro do intervalo
    analisado (`dias_possiveis`) — um mês mais curto (fevereiro) ou uma
    semana/mês cortado pelas bordas do período analisado tem menos dias
    possíveis que o calendário cheio.
    """

    df = df.copy()
    data_min, data_max = df["data_calendario"].min(), df["data_calendario"].max()

    if granularidade == "semana":
        periodos = df["data"].dt.to_period("W")
        rotulos = {p: _rotulo_semana(p) for p in periodos.unique()}
    else:
        periodos = df["data"].dt.to_period("M")
        rotulos = {p: _rotulo_mes(p) for p in periodos.unique()}

    ordem = [rotulos[p] for p in sorted(rotulos)]
    df["periodo_rotulo"] = periodos.map(rotulos)

    dias_possiveis = {}
    for periodo, rotulo in rotulos.items():
        inicio_efetivo = max(periodo.start_time.normalize(), data_min)
        fim_efetivo = min(periodo.end_time.normalize(), data_max)
        dias_possiveis[rotulo] = (fim_efetivo - inicio_efetivo).days + 1

    return df, ordem, dias_possiveis


def _grafico_sequencia_por_periodo(sequencias: dict, dias_possiveis: dict, ordem_periodos: list, people: list, color_map: dict, titulo: str, rotulo_x: str):
    """Barras agrupadas: maior sequência de dias consecutivos por pessoa,
    dentro de cada período. O rótulo de cada barra mostra "dias/possíveis" —
    o denominador varia por período (calendário do mês/semana), não por pessoa.
    """

    n_pessoas = max(len(people), 1)
    largura_barra = 0.8 / n_pessoas
    posicoes_x = list(range(len(ordem_periodos)))

    largura_fig = max(FIGSIZE_LARGO[0], 1.1 * len(ordem_periodos) + 3)
    altura_fig = FIGSIZE_PADRAO[1]
    if largura_fig / altura_fig > 2.4:
        altura_fig = largura_fig / 2.4
    fig, ax = plt.subplots(figsize=(largura_fig, altura_fig))

    for indice, pessoa in enumerate(people):
        valores = [sequencias.get((periodo, pessoa), 0) for periodo in ordem_periodos]
        deslocamento = (indice - (n_pessoas - 1) / 2) * largura_barra
        posicoes = [x + deslocamento for x in posicoes_x]

        barras = ax.bar(
            posicoes, valores, width=largura_barra * 0.9,
            color=color_map.get(pessoa, BRAND["primary"]), label=pessoa, zorder=3,
        )

        for barra, periodo in zip(barras, ordem_periodos):
            altura = barra.get_height()
            ax.annotate(
                f"{int(altura)}/{dias_possiveis[periodo]}",
                xy=(barra.get_x() + barra.get_width() / 2, altura),
                xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=BRAND["ink"],
            )

    ax.set_title(titulo)
    ax.set_xlabel(rotulo_x)
    ax.set_ylabel("Dias consecutivos")
    ax.set_xticks(posicoes_x)
    ax.set_xticklabels(ordem_periodos)
    valor_maximo = max((v for v in sequencias.values()), default=0)
    ax.set_ylim(0, max(valor_maximo * 1.3, 1))
    estilizar_eixo(ax)
    plt.setp(ax.get_xticklabels(), rotation=20 if len(ordem_periodos) <= 14 else 45, ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def run(ctx) -> AnalysisResult:
    df = ctx.df

    span_dias = (df["data_calendario"].max() - df["data_calendario"].min()).days + 1

    if span_dias < 2:
        return AnalysisResult(key=KEY, title=TITLE, icon=ICON)

    granularidade = "semana" if (
        ctx.periodo_modo == "mes_ano" or (ctx.periodo_modo == "periodo" and span_dias <= 31)
    ) else "mes"

    df, ordem_periodos, dias_possiveis = _preparar_periodos(df, granularidade)

    if len(ordem_periodos) < 2:
        return AnalysisResult(key=KEY, title=TITLE, icon=ICON)

    unidade = "mês" if granularidade == "mes" else "semana"
    unidade_plural = "meses" if granularidade == "mes" else "semanas"
    titulo_secao = "Evolução mensal" if granularidade == "mes" else "Evolução semanal"
    rotulo_eixo = "Mês" if granularidade == "mes" else "Semana"

    grade = pd.MultiIndex.from_product(
        [ordem_periodos, ctx.people], names=["periodo_rotulo", "nome"]
    ).to_frame(index=False)

    charts = []
    tabelas = {}
    insights = []

    # 1) mensagens por pessoa, por período
    mensagens = (
        df.groupby(["periodo_rotulo", "nome"], observed=True)
        .size()
        .reset_index(name="quantidade_mensagens")
    )
    mensagens = grade.merge(mensagens, on=["periodo_rotulo", "nome"], how="left")
    mensagens["quantidade_mensagens"] = mensagens["quantidade_mensagens"].fillna(0).astype(int)

    charts.append(
        ChartArtifact(
            slug="26_mensagens_por_pessoa_periodo",
            title=f"Mensagens por pessoa, por {unidade}",
            figure=grafico_linhas_por_categoria(
                mensagens, "periodo_rotulo", "quantidade_mensagens", "nome",
                f"Mensagens por pessoa, {titulo_secao.lower()}",
                rotulo_eixo, "Quantidade de mensagens", ctx.color_map,
                ordem_x=ordem_periodos,
            ),
        )
    )
    tabelas["mensagens_por_pessoa_periodo"] = mensagens

    # 2) quem mais mandou mensagem em cada período
    vencedor_por_periodo = (
        mensagens.sort_values(["periodo_rotulo", "quantidade_mensagens", "nome"], ascending=[True, False, True])
        .groupby("periodo_rotulo", observed=True)
        .first()
    )
    ranking_vitorias = (
        vencedor_por_periodo["nome"]
        .value_counts()
        .reindex(ctx.people, fill_value=0)
        .rename("periodos_vencidos")
        .reset_index()
        .sort_values("periodos_vencidos", ascending=False)
        .reset_index(drop=True)
    )

    charts.append(
        ChartArtifact(
            slug="26b_quem_mais_mandou_mensagem_periodo",
            title=f"Quem mais mandou mensagem, por {unidade}",
            figure=grafico_barras_por_pessoa(
                ranking_vitorias, "periodos_vencidos",
                f"Em quantos(as) {unidade_plural} cada pessoa mandou mais mensagens",
                f"Quantidade de {unidade_plural}", ctx.color_map,
            ),
        )
    )
    tabelas["quem_mais_mandou_mensagem_periodo"] = ranking_vitorias

    lider_geral = ranking_vitorias.iloc[0]
    insights.append(
        f"{lider_geral['nome']} foi quem mais mandou mensagem na maioria dos(as) {unidade_plural}: "
        f"{formatar_numero(lider_geral['periodos_vencidos'])} de {formatar_numero(len(ordem_periodos))}."
    )

    primeiro_periodo, ultimo_periodo = ordem_periodos[0], ordem_periodos[-1]
    comparativo = mensagens.pivot(index="nome", columns="periodo_rotulo", values="quantidade_mensagens")
    variacao = (comparativo[ultimo_periodo] - comparativo[primeiro_periodo]).sort_values(ascending=False)

    if variacao.iloc[0] > 0:
        quem_mais_cresceu = variacao.index[0]
        insights.append(
            f"{quem_mais_cresceu} foi quem mais aumentou o envio de mensagens entre {primeiro_periodo} e "
            f"{ultimo_periodo}: de {formatar_numero(comparativo.loc[quem_mais_cresceu, primeiro_periodo])} "
            f"para {formatar_numero(comparativo.loc[quem_mais_cresceu, ultimo_periodo])}."
        )
    if variacao.iloc[-1] < 0:
        quem_mais_caiu = variacao.index[-1]
        insights.append(
            f"{quem_mais_caiu} foi quem mais reduziu o envio de mensagens entre {primeiro_periodo} e "
            f"{ultimo_periodo}: de {formatar_numero(comparativo.loc[quem_mais_caiu, primeiro_periodo])} "
            f"para {formatar_numero(comparativo.loc[quem_mais_caiu, ultimo_periodo])}."
        )

    # 2b) maior sequência de dias consecutivos dentro de cada período, por pessoa
    sequencia_periodo = (
        df.groupby(["periodo_rotulo", "nome"], observed=True)["data_calendario"]
        .apply(lambda serie: maior_sequencia_consecutiva(serie)[0])
        .reset_index(name="maximo_dias_consecutivos")
    )
    sequencia_periodo = grade.merge(sequencia_periodo, on=["periodo_rotulo", "nome"], how="left")
    sequencia_periodo["maximo_dias_consecutivos"] = sequencia_periodo["maximo_dias_consecutivos"].fillna(0).astype(int)
    sequencia_periodo["dias_possiveis"] = sequencia_periodo["periodo_rotulo"].map(dias_possiveis)

    sequencias_dict = {
        (linha.periodo_rotulo, linha.nome): linha.maximo_dias_consecutivos
        for linha in sequencia_periodo.itertuples()
    }

    charts.append(
        ChartArtifact(
            slug="26bb_sequencia_dias_por_periodo",
            title=f"Maior sequência de dias consecutivos, por pessoa e por {unidade}",
            figure=_grafico_sequencia_por_periodo(
                sequencias_dict, dias_possiveis, ordem_periodos, ctx.people, ctx.color_map,
                f"Maior sequência de dias seguidos, {titulo_secao.lower()}", rotulo_eixo,
            ),
        )
    )
    tabelas["sequencia_dias_por_periodo"] = sequencia_periodo

    melhor_sequencia_periodo = sequencia_periodo.loc[sequencia_periodo["maximo_dias_consecutivos"].idxmax()]
    if melhor_sequencia_periodo["maximo_dias_consecutivos"] > 0:
        insights.append(
            f"Melhor sequência dentro de um(a) só {unidade}: {melhor_sequencia_periodo['nome']}, com "
            f"{formatar_numero(melhor_sequencia_periodo['maximo_dias_consecutivos'])}/"
            f"{formatar_numero(melhor_sequencia_periodo['dias_possiveis'])} dias, em "
            f"{melhor_sequencia_periodo['periodo_rotulo']}."
        )

    # 3) figurinhas por pessoa e total, por período (não depende de mídia real)
    figurinhas = (
        df.loc[df["figurinha"]]
        .groupby(["periodo_rotulo", "nome"], observed=True)
        .size()
        .reset_index(name="quantidade_figurinhas")
    )
    figurinhas = grade.merge(figurinhas, on=["periodo_rotulo", "nome"], how="left")
    figurinhas["quantidade_figurinhas"] = figurinhas["quantidade_figurinhas"].fillna(0).astype(int)

    if figurinhas["quantidade_figurinhas"].sum() > 0:
        charts.append(
            ChartArtifact(
                slug="26c_figurinhas_por_pessoa_periodo",
                title=f"Figurinhas por pessoa, por {unidade}",
                figure=grafico_linhas_por_categoria(
                    figurinhas, "periodo_rotulo", "quantidade_figurinhas", "nome",
                    f"Figurinhas por pessoa, {titulo_secao.lower()}",
                    rotulo_eixo, "Quantidade de figurinhas", ctx.color_map,
                    ordem_x=ordem_periodos,
                ),
            )
        )
        tabelas["figurinhas_por_pessoa_periodo"] = figurinhas

        figurinhas_totais = (
            figurinhas.groupby("periodo_rotulo", observed=True)["quantidade_figurinhas"]
            .sum()
            .reindex(ordem_periodos)
            .reset_index()
        )
        charts.append(
            ChartArtifact(
                slug="26d_figurinhas_totais_periodo",
                title=f"Figurinhas enviadas no grupo, por {unidade}",
                figure=grafico_barras_simples(
                    figurinhas_totais, "periodo_rotulo", "quantidade_figurinhas",
                    f"Total de figurinhas enviadas, {titulo_secao.lower()}",
                    rotulo_eixo, "Quantidade de figurinhas",
                ),
            )
        )
        tabelas["figurinhas_totais_periodo"] = figurinhas_totais

    # 4) duração de áudio por pessoa e total, por período (precisa dos arquivos reais)
    if ctx.has_media:
        audios = medir_duracoes_audio(df, ctx.media_store)

        if not audios.empty:
            audio_por_pessoa = (
                audios.groupby(["periodo_rotulo", "nome"], observed=True)["duracao_audio_segundos"]
                .sum()
                .reset_index(name="duracao_audio_segundos")
            )
            audio_por_pessoa = grade.merge(audio_por_pessoa, on=["periodo_rotulo", "nome"], how="left")
            audio_por_pessoa["duracao_audio_segundos"] = audio_por_pessoa["duracao_audio_segundos"].fillna(0.0)
            audio_por_pessoa["duracao_audio_minutos"] = (audio_por_pessoa["duracao_audio_segundos"] / 60).round(2)

            if audio_por_pessoa["duracao_audio_minutos"].sum() > 0:
                charts.append(
                    ChartArtifact(
                        slug="26e_duracao_audio_por_pessoa_periodo",
                        title=f"Duração de áudio por pessoa, por {unidade}",
                        figure=grafico_linhas_por_categoria(
                            audio_por_pessoa, "periodo_rotulo", "duracao_audio_minutos", "nome",
                            f"Duração de áudio por pessoa, {titulo_secao.lower()}",
                            rotulo_eixo, "Minutos de áudio", ctx.color_map,
                            ordem_x=ordem_periodos,
                        ),
                    )
                )
                tabelas["duracao_audio_por_pessoa_periodo"] = audio_por_pessoa

                audio_total_periodo = (
                    audio_por_pessoa.groupby("periodo_rotulo", observed=True)["duracao_audio_minutos"]
                    .sum()
                    .reindex(ordem_periodos)
                    .reset_index()
                )
                charts.append(
                    ChartArtifact(
                        slug="26f_duracao_audio_total_periodo",
                        title=f"Duração total de áudio no grupo, por {unidade}",
                        figure=grafico_barras_simples(
                            audio_total_periodo, "periodo_rotulo", "duracao_audio_minutos",
                            f"Duração total de áudio, {titulo_secao.lower()}",
                            rotulo_eixo, "Minutos de áudio",
                        ),
                    )
                )
                tabelas["duracao_audio_total_periodo"] = audio_total_periodo

    return AnalysisResult(
        key=KEY,
        title=titulo_secao,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro=(
            f"Como a atividade do grupo muda {('mês a mês' if granularidade == 'mes' else 'semana a semana')} "
            "— para ver quem está interagindo mais ou menos, e quando isso muda."
        ),
    )
