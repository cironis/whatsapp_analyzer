"""WhatsApp Analyzer — interface Streamlit.

Fluxo: 1) enviar o .zip exportado do WhatsApp → 2) renomear participantes
(opcional) → 3) gerar e baixar o ZIP de gráficos e o PDF do relatório.
"""

from __future__ import annotations

import streamlit as st

from src.parsing import ArquivoInvalidoError
from src.pipeline import carregar_para_renomear, executar_analise

st.set_page_config(page_title="WhatsApp Analyzer", page_icon="💬", layout="centered")

if "dados" not in st.session_state:
    st.session_state.dados = None
    st.session_state.arquivo_id = None
    st.session_state.resultado = None

st.title("💬 Analisador de Conversas do WhatsApp")
st.write(
    "Envie o **.zip** exportado de uma conversa do WhatsApp (com ou sem mídia) e "
    "receba um pacote com os gráficos em imagem e um relatório em PDF — sem que os "
    "apelidos originais do WhatsApp precisem aparecer no relatório."
)

with st.expander("Como exportar a conversa do WhatsApp"):
    st.markdown(
        "No WhatsApp: abra a conversa → **⋮ (mais opções)** → **Mais** → "
        "**Exportar conversa**. Escolha **Incluir mídia** para liberar as análises "
        "de imagens e áudio, ou **Sem mídia** para um arquivo bem mais leve (as "
        "demais análises continuam funcionando normalmente). Depois é só enviar o "
        "**.zip** gerado aqui embaixo.\n\n"
        "Nada do que você envia é salvo: o processamento acontece só durante esta "
        "sessão e os arquivos ficam apenas na memória enquanto a página está aberta."
    )

arquivo = st.file_uploader("**1. Envie o arquivo .zip da conversa**", type=["zip"])

if arquivo is not None:
    identidade = (arquivo.name, arquivo.size)

    if st.session_state.arquivo_id != identidade:
        st.session_state.arquivo_id = identidade
        st.session_state.resultado = None
        st.session_state.dados = None

        with st.spinner("Lendo o arquivo..."):
            try:
                st.session_state.dados = carregar_para_renomear(arquivo.getvalue(), arquivo.name)
            except ArquivoInvalidoError as erro:
                st.error(str(erro))
            except Exception as erro:  # noqa: BLE001 - mostrado ao usuário
                st.error(f"Não foi possível ler o arquivo enviado: {erro}")

dados = st.session_state.dados

if dados is not None:
    if not dados.nomes_originais:
        st.warning("Nenhuma pessoa foi identificada nesse arquivo. Verifique se é uma exportação válida.")
    else:
        if dados.media_store.has_media:
            st.success(
                f"Arquivo lido: **{len(dados.nomes_originais)} participantes** encontrados, "
                "com mídia incluída — todas as análises estarão disponíveis."
            )
        else:
            st.info(
                f"Arquivo lido: **{len(dados.nomes_originais)} participantes** encontrados, "
                "sem mídia incluída. As análises de fotos e duração de áudio ficam fora do "
                "relatório; todas as demais continuam normalmente."
            )

        st.write("**2. Renomeie os participantes (opcional)**")
        st.caption(
            "Troque o apelido do WhatsApp por um nome ou codinome de sua escolha. "
            "Deixe como está para manter o nome original."
        )

        sufixo = f"{identidade[0]}_{identidade[1]}"

        if st.button("✨ Anonimizar automaticamente (Pessoa 1, Pessoa 2, ...)"):
            for indice, nome in enumerate(dados.nomes_originais, start=1):
                st.session_state[f"nome_{indice}_{sufixo}"] = f"Pessoa {indice}"

        mapa_nomes = {}
        colunas = st.columns(2)

        for indice, nome in enumerate(dados.nomes_originais, start=1):
            chave = f"nome_{indice}_{sufixo}"
            coluna = colunas[indice % 2]
            novo_nome = coluna.text_input(nome, value=nome, key=chave)
            mapa_nomes[nome] = (novo_nome or "").strip() or nome

        rotulo_grupo = st.text_input(
            "Nome da conversa (aparece na capa do relatório)",
            value="Conversa do WhatsApp",
            key=f"rotulo_{sufixo}",
        )

        st.write("**3. Gerar o relatório**")

        if st.button("🚀 Gerar análise", type="primary"):
            barra = st.progress(0.0, text="Iniciando...")
            total_etapas = 9
            contador = {"n": 0}

            def _progresso(titulo: str) -> None:
                contador["n"] += 1
                barra.progress(min(contador["n"] / total_etapas, 0.95), text=f"Analisando: {titulo}")

            try:
                resultado = executar_analise(
                    dados,
                    mapa_nomes,
                    rotulo_grupo=rotulo_grupo.strip() or "Conversa do WhatsApp",
                    progresso=_progresso,
                )
                st.session_state.resultado = resultado
                barra.progress(1.0, text="Concluído!")
            except Exception as erro:  # noqa: BLE001 - mostrado ao usuário
                st.session_state.resultado = None
                barra.empty()
                st.error(f"Ocorreu um erro ao gerar a análise: {erro}")

resultado = st.session_state.resultado

if resultado is not None:
    st.write("---")
    st.subheader("Pronto! 🎉")

    meta = resultado.meta
    coluna1, coluna2, coluna3, coluna4 = st.columns(4)
    coluna1.metric("Participantes", meta["num_pessoas"])
    coluna2.metric("Mensagens", f"{meta['total_mensagens']:,}".replace(",", "."))
    coluna3.metric("Dias com conversa", meta["dias_com_mensagem"])
    coluna4.metric("Sequência recorde", f"{meta['maior_sequencia']} dias")

    coluna_zip, coluna_pdf = st.columns(2)

    with coluna_zip:
        st.download_button(
            "📦 Baixar imagens (.zip)",
            data=resultado.zip_bytes,
            file_name="graficos_whatsapp.zip",
            mime="application/zip",
            use_container_width=True,
        )

    with coluna_pdf:
        st.download_button(
            "📄 Baixar relatório (.pdf)",
            data=resultado.pdf_bytes,
            file_name="relatorio_whatsapp.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    st.caption(
        "Dica: as palavras mencionadas dentro das mensagens (inclusive nomes de outras "
        "pessoas citadas na conversa) não são removidas das nuvens de palavras — só os "
        "remetentes são renomeados conforme configurado acima."
    )
