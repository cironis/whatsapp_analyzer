"""Evolução da conversa ao longo do tempo: quebra mês a mês (quando o
relatório olha o histórico inteiro ou um período longo) ou semana a semana
(quando o relatório está filtrado por um mês específico). A ideia é ver se
alguém está interagindo mais ou menos, e como isso varia com o tempo.
"""

from __future__ import annotations

import pandas as pd

from ..audio import medir_duracoes_audio
from ..chart_common import grafico_barras_por_pessoa, grafico_barras_simples, grafico_linhas_por_categoria
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_numero

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


def run(ctx) -> AnalysisResult:
    df = ctx.df

    span_dias = (df["data_calendario"].max() - df["data_calendario"].min()).days + 1

    if span_dias < 2:
        return AnalysisResult(key=KEY, title=TITLE, icon=ICON)

    granularidade = "semana" if (
        ctx.periodo_modo == "mes_ano" or (ctx.periodo_modo == "periodo" and span_dias <= 31)
    ) else "mes"

    df, ordem_periodos, _dias_possiveis = _preparar_periodos(df, granularidade)

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

    intro_historico = ""

    # 5) evolução mês a mês considerando TODO o período dos dados — só faz
    # sentido no relatório mensal (que, até aqui, só olhou o mês escolhido):
    # dá pra comparar esse mês com o histórico inteiro do arquivo.
    if ctx.periodo_modo == "mes_ano" and ctx.df_historico_completo is not None:
        df_hist = ctx.df_historico_completo
        span_dias_hist = (df_hist["data_calendario"].max() - df_hist["data_calendario"].min()).days + 1

        if span_dias_hist >= 2:
            df_hist, ordem_meses, _dias_possiveis_meses = _preparar_periodos(df_hist, "mes")

            if len(ordem_meses) >= 2:
                intro_historico = (
                    " Também mostra a evolução mês a mês de mensagens, caracteres, figurinhas e áudio "
                    "por pessoa, considerando todo o período disponível nos dados (não só o mês escolhido)."
                )

                grade_meses = pd.MultiIndex.from_product(
                    [ordem_meses, ctx.people], names=["periodo_rotulo", "nome"]
                ).to_frame(index=False)

                # mensagens por pessoa, mês a mês, no histórico inteiro
                mensagens_hist = (
                    df_hist.groupby(["periodo_rotulo", "nome"], observed=True)
                    .size()
                    .reset_index(name="quantidade_mensagens")
                )
                mensagens_hist = grade_meses.merge(mensagens_hist, on=["periodo_rotulo", "nome"], how="left")
                mensagens_hist["quantidade_mensagens"] = mensagens_hist["quantidade_mensagens"].fillna(0).astype(int)

                charts.append(
                    ChartArtifact(
                        slug="26g_mensagens_por_pessoa_mes_historico",
                        title="Mensagens por pessoa, mês a mês (período total)",
                        figure=grafico_linhas_por_categoria(
                            mensagens_hist, "periodo_rotulo", "quantidade_mensagens", "nome",
                            "Mensagens por pessoa, mês a mês, considerando todo o período dos dados",
                            "Mês", "Quantidade de mensagens", ctx.color_map,
                            ordem_x=ordem_meses,
                        ),
                    )
                )
                tabelas["mensagens_por_pessoa_mes_historico"] = mensagens_hist

                # caracteres por pessoa, mês a mês, no histórico inteiro
                caracteres_hist = (
                    df_hist.groupby(["periodo_rotulo", "nome"], observed=True)["quantidade_caracteres"]
                    .sum()
                    .reset_index(name="quantidade_caracteres")
                )
                caracteres_hist = grade_meses.merge(caracteres_hist, on=["periodo_rotulo", "nome"], how="left")
                caracteres_hist["quantidade_caracteres"] = (
                    caracteres_hist["quantidade_caracteres"].fillna(0).astype(int)
                )

                charts.append(
                    ChartArtifact(
                        slug="26h_caracteres_por_pessoa_mes_historico",
                        title="Caracteres por pessoa, mês a mês (período total)",
                        figure=grafico_linhas_por_categoria(
                            caracteres_hist, "periodo_rotulo", "quantidade_caracteres", "nome",
                            "Volume de texto por pessoa, mês a mês, considerando todo o período dos dados",
                            "Mês", "Quantidade de caracteres", ctx.color_map,
                            ordem_x=ordem_meses,
                        ),
                    )
                )
                tabelas["caracteres_por_pessoa_mes_historico"] = caracteres_hist

                # figurinhas por pessoa, mês a mês, no histórico inteiro
                figurinhas_hist = (
                    df_hist.loc[df_hist["figurinha"]]
                    .groupby(["periodo_rotulo", "nome"], observed=True)
                    .size()
                    .reset_index(name="quantidade_figurinhas")
                )
                figurinhas_hist = grade_meses.merge(figurinhas_hist, on=["periodo_rotulo", "nome"], how="left")
                figurinhas_hist["quantidade_figurinhas"] = (
                    figurinhas_hist["quantidade_figurinhas"].fillna(0).astype(int)
                )

                if figurinhas_hist["quantidade_figurinhas"].sum() > 0:
                    charts.append(
                        ChartArtifact(
                            slug="26i_figurinhas_por_pessoa_mes_historico",
                            title="Figurinhas por pessoa, mês a mês (período total)",
                            figure=grafico_linhas_por_categoria(
                                figurinhas_hist, "periodo_rotulo", "quantidade_figurinhas", "nome",
                                "Figurinhas por pessoa, mês a mês, considerando todo o período dos dados",
                                "Mês", "Quantidade de figurinhas", ctx.color_map,
                                ordem_x=ordem_meses,
                            ),
                        )
                    )
                    tabelas["figurinhas_por_pessoa_mes_historico"] = figurinhas_hist

                # duração de áudio por pessoa, mês a mês, no histórico inteiro
                if ctx.has_media:
                    audios_hist = medir_duracoes_audio(df_hist, ctx.media_store)

                    if not audios_hist.empty:
                        audio_por_pessoa_hist = (
                            audios_hist.groupby(["periodo_rotulo", "nome"], observed=True)["duracao_audio_segundos"]
                            .sum()
                            .reset_index(name="duracao_audio_segundos")
                        )
                        audio_por_pessoa_hist = grade_meses.merge(
                            audio_por_pessoa_hist, on=["periodo_rotulo", "nome"], how="left"
                        )
                        audio_por_pessoa_hist["duracao_audio_segundos"] = (
                            audio_por_pessoa_hist["duracao_audio_segundos"].fillna(0.0)
                        )
                        audio_por_pessoa_hist["duracao_audio_minutos"] = (
                            audio_por_pessoa_hist["duracao_audio_segundos"] / 60
                        ).round(2)

                        if audio_por_pessoa_hist["duracao_audio_minutos"].sum() > 0:
                            charts.append(
                                ChartArtifact(
                                    slug="26j_audio_por_pessoa_mes_historico",
                                    title="Duração de áudio por pessoa, mês a mês (período total)",
                                    figure=grafico_linhas_por_categoria(
                                        audio_por_pessoa_hist, "periodo_rotulo", "duracao_audio_minutos", "nome",
                                        "Duração de áudio por pessoa, mês a mês, considerando todo o "
                                        "período dos dados",
                                        "Mês", "Minutos de áudio", ctx.color_map,
                                        ordem_x=ordem_meses,
                                    ),
                                )
                            )
                            tabelas["audio_por_pessoa_mes_historico"] = audio_por_pessoa_hist

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
            f"{intro_historico}"
        ),
    )
