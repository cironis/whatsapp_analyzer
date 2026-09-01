# WhatsApp Analyzer

Aplicativo Streamlit que recebe o `.zip` exportado de uma conversa do WhatsApp
(com ou sem mídia) e devolve:

- um **`.zip`** com todos os gráficos em PNG;
- um **relatório em PDF**, com capa, KPIs e uma seção por análise.

Antes de gerar o relatório, é possível **renomear cada participante**, para
que o apelido original do WhatsApp não precise aparecer no PDF nem nas
imagens, e escolher o **período a analisar**: todo o histórico, um mês/ano
específico (mostrando o mês inteiro) ou um intervalo de datas personalizado.
O período escolhido sempre aparece de forma explícita na capa do relatório.

## Rodando localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicando no Streamlit Community Cloud

1. Suba este repositório no GitHub (sem incluir nenhum `.zip` de conversa real
   — o `.gitignore` já bloqueia isso).
2. Em [share.streamlit.io](https://share.streamlit.io), aponte para este
   repositório e para o arquivo `app.py`.
3. Pronto — o `requirements.txt` e o `.streamlit/config.toml` já configuram
   tudo o que o app precisa.

Nenhuma biblioteca do app depende de navegador/Chromium (os gráficos são
gerados com `matplotlib`, não `plotly`+`playwright`), então não é necessário
nenhum pacote de sistema extra além do `requirements.txt`.

## Estrutura do código

```
app.py                      → interface Streamlit (upload → renomear → período → gerar)
src/
  parsing.py                 → lê o .zip/.txt exportado e extrai as mensagens
  media_store.py              → acesso aos anexos dentro do .zip (se houver)
  enrich.py                   → colunas derivadas (dia da semana, tipo de conteúdo, etc.)
  colors.py, style.py, icons.py, chart_common.py → identidade visual dos gráficos
  analyses/                   → uma análise por módulo (ver abaixo)
  report/
    pdf_builder.py             → monta o PDF (capa + uma seção por análise)
    zip_builder.py              → empacota os PNGs
  pipeline.py                  → orquestra parsing → análises → PDF/ZIP
```

### Adicionando uma nova análise no futuro

Cada análise é um módulo em `src/analyses/` com:

- `KEY`, `TITLE`, `ICON` (nome de um ícone em `src/icons.py`) e
  `REQUIRES_MEDIA` (`True` se só funcionar com o .zip contendo os arquivos de
  mídia de verdade);
- uma função `run(ctx) -> AnalysisResult`, em que `ctx` (`AnalysisContext`)
  já traz o DataFrame enriquecido, o mapa de cores por pessoa, a lista de
  participantes e se há mídia disponível.

Depois é só importar o módulo e incluí-lo na lista `ANALISES` em
`src/analyses/__init__.py`, na ordem em que deve aparecer no PDF e no ZIP. O
pipeline, o ZIP e o PDF não precisam de nenhuma outra mudança.

## Privacidade

Todo o processamento acontece em memória durante a sessão do Streamlit —
nada é salvo em disco além de arquivos temporários usados para medir a
duração dos áudios, que são apagados assim que a análise termina.
