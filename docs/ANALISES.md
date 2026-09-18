# Catálogo de análises do relatório

Referência rápida de tudo que o relatório gera — sem precisar montar o PDF. Lista as
análises na mesma ordem em que aparecem no PDF/ZIP (`src/analyses/__init__.py`), com os
gráficos e tabelas que cada uma produz.

> **Importante:** este arquivo deve ser atualizado sempre que uma análise for
> adicionada, removida ou alterada (novos gráficos/tabelas, mudança de critério, etc.)
> em `src/analyses/`. Ver `src/analyses/__init__.py` para a lista viva de módulos.

## Estrutura do PDF (fora da lista de análises)
1. **Capa** — KPIs gerais (`src/report/pdf_builder.py::_construir_capa`). Não tem mais a
   frase sobre os nomes terem sido configurados por quem gerou o relatório.
2. **Resumo das análises** (`_construir_resumo_geral`) — logo após a capa: para cada
   análise incluída, mostra o título, a intro e todos os insights (o mesmo texto que
   aparece depois no início de cada seção — fica duplicado de propósito, para dar uma
   visão geral rápida sem precisar folhear o PDF inteiro).
3. Uma seção por análise (lista abaixo), cada uma repetindo sua própria intro/insights
   antes dos gráficos.

## 1. Atividade e mensagens (`messages.py`)
Visão geral de quem fala mais e quando o grupo mais conversa.
- **Gráficos:** mensagens por pessoa · heatmap dia da semana × hora · mensagens por dia
  da semana · mensagens por hora do dia.
- **Tabelas:** mensagens por pessoa · mensagens por dia/hora (cross-tab) · mensagens por
  dia da semana · mensagens por hora.

## 2. Quando cada pessoa mais fala (`person_activity.py`)
Mesma ideia do item 1, mas quebrada pessoa a pessoa.
- **Gráficos:** mensagens por dia da semana, por pessoa (linhas) · mensagens por hora do
  dia, por pessoa (linhas).
- **Tabelas:** mensagens por pessoa × dia da semana · mensagens por pessoa × hora ·
  resumo do horário mais ativo por pessoa.

## 3. Volume de texto (`characters.py`)
Quem escreve mais e quem manda as mensagens mais longas.
- **Gráficos:** total de caracteres por pessoa · média de caracteres por mensagem, por
  pessoa (com linha de média do grupo).
- **Tabelas:** total de caracteres por pessoa · média de caracteres por pessoa.

## 4. Conversas e sequências (`conversations.py`)
Quem puxa e quem encerra conversas (janela de silêncio = 1h para começar uma nova
conversa), sequências de dias ativos e recordes de conversa mais longa.
- **Gráficos:** conversas iniciadas por pessoa · conversas finalizadas por pessoa ·
  maior sequência de dias consecutivos, por pessoa (rótulo de cada barra no formato
  "dias/possíveis", ex.: "10/59" — o denominador é o total de dias do período
  analisado; legenda abaixo do gráfico mostra o período exato — início e fim — da
  sequência de cada pessoa) · sequência atual (em andamento) vs. recorde histórico, por
  pessoa (duas barras por pessoa) · média de mensagens por conversa, por pessoa · média
  de figurinhas por conversa, por pessoa (só com mídia) · quem mais falou na conversa
  mais longa em duração · quem mais falou na conversa com mais mensagens (só aparece se
  for uma conversa diferente da mais longa em duração).
- **Tabelas:** conversas iniciadas · conversas finalizadas · sequência por pessoa (com
  data de início e fim da maior sequência) · sequência atual vs. recorde · média de
  mensagens por conversa · média de figurinhas por conversa (com mídia) ·
  participantes da conversa mais longa em duração · participantes da conversa com mais
  mensagens (quando distinta).
- **Insights:** também citam o período (datas) da sequência recorde do grupo e da
  pessoa líder, e se alguém está perto de bater o próprio recorde agora.

## 5. Dinâmica da conversa (`dinamica_conversa.py`)
Quanto tempo cada pessoa demora para responder dentro de uma conversa já em andamento
(não conta o início de uma conversa nova após 1h de silêncio — isso é o item 4), e quem
costuma retomar a palavra depois da outra pessoa falar vs. quem só recebe resposta. Só
aparece se houver pelo menos uma troca de turno no período analisado.
- **Gráficos:** tempo de resposta (mediana) por pessoa · % de respostas dadas em até 60s
  por pessoa · quantas vezes cada pessoa retomou a conversa depois da outra pessoa falar
  (quem inicia a troca de turno) · quantas vezes a mensagem de cada pessoa foi seguida
  de resposta de outra pessoa (quem é mais respondido).
- **Tabelas:** resumo de tempo de resposta por pessoa (mediana, média, % rápidas) ·
  quem retoma a conversa · quem é mais respondido.

## 6. Evolução recente (`timeline.py`)
Mensagens e caracteres por dia, pessoa a pessoa. Por padrão os últimos 30 dias; se o
relatório for filtrado por mês/ano, mostra o mês inteiro.
- **Gráficos:** mensagens por dia e pessoa (linha temporal) · caracteres por dia e
  pessoa (linha temporal).
- **Tabelas:** mensagens por dia (janela) · caracteres por dia (janela).

## 7. Evolução por período (`evolucao_periodica.py`)
Como a atividade do grupo muda ao longo do tempo, para ver quem está interagindo mais
ou menos. A granularidade depende do filtro de período escolhido no app (`ctx.periodo_modo`):
histórico completo ou período longo (> 31 dias) → quebra **por mês**; um mês específico
(ou período curto, ≤ 31 dias) → quebra **por semana**. Só aparece quando há pelo menos 2
períodos com mensagem. O título da seção já sai como "Evolução mensal" ou "Evolução
semanal".
- **Gráficos:** mensagens por pessoa, por período (linhas) · quem mais mandou mensagem
  em cada período (ranking de "vitórias" por pessoa) · maior sequência de dias
  consecutivos por pessoa, dentro de cada período (barras agrupadas, rótulo
  "dias/possíveis" por período — ex.: "20/31" num mês cheio, "3/7" numa semana cheia; o
  denominador usa a quantidade real de dias do período que caem dentro do intervalo
  analisado, então um mês mais curto, como fevereiro, ou uma semana/mês cortado pela
  borda do período analisado — incluindo o mês/semana ainda em andamento — aparece com
  menos dias possíveis) · figurinhas por pessoa, por período (linhas) · total de
  figurinhas enviadas, por período (barras) · duração de áudio por pessoa, por período
  (linhas, só com mídia) · duração total de áudio, por período (barras, só com mídia).
- **Tabelas:** mensagens por pessoa/período · ranking de quem mais mandou mensagem por
  período · maior sequência por pessoa/período (com dias possíveis) · figurinhas por
  pessoa/período e total por período · duração de áudio por pessoa/período e total por
  período (com mídia).
- **Insights:** quem venceu mais períodos, quem mais aumentou/reduziu o envio de
  mensagens entre o primeiro e o último período, e a melhor sequência dentro de um único
  período.

## 8. Mídia enviada (`media_stats.py`)
Quantidade de mídia por pessoa. Funciona mesmo sem os arquivos no .zip (mídia é
identificada mesmo pelo texto `<Media omitted>`).
- **Gráficos:** arquivos de mídia por pessoa · razão figurinha/mensagem por pessoa (%
  das mensagens de cada pessoa que são figurinha — não depende de mídia real) · mídia
  por tipo e pessoa, barras empilhadas (imagem/figurinha/áudio/vídeo/documento/contato —
  só quando o .zip inclui os arquivos de verdade).
- **Tabelas:** mídias por pessoa · razão figurinha/mensagem por pessoa · mídias por tipo
  e pessoa (com mídia real).

## 9. Ranking de dias (`daily_ranking.py`)
Em quantos dias cada pessoa "venceu" cada métrica (foi quem mais teve naquele dia).
- **Gráficos:** dias com mais mensagens · dias com mais caracteres · dias com mais
  áudios (com mídia) · dias com mais figurinhas (com mídia).
- **Tabelas:** uma tabela de ranking por métrica acima.

## 10. Calendário de atividade (`github_grid.py`)
Grid estilo "GitHub contributions": um quadrado por dia, colorido pela pessoa que
venceu aquele dia em cada métrica.
- **Gráficos:** calendário de mensagens · calendário de caracteres · calendário de
  áudios (com mídia) · calendário de figurinhas (com mídia).
- **Tabelas:** vencedor do dia, uma tabela por métrica acima.

## 11. Figurinhas e áudios (`media_gallery.py`)
Só aparece quando o .zip inclui os arquivos de mídia de verdade. Considera todos os
formatos de áudio classificados como tal em `src/media_store.py` (`.opus`, `.m4a`,
`.aac`, `.mp3`, `.wav`, `.ogg`/`.oga`, `.flac`, `.amr`, `.caf`, `.weba`, `.3ga` — e
qualquer extensão em anexos com prefixo `PTT-`/`AUD-`, que o WhatsApp sempre usa para
áudio independente da extensão). A duração de cada áudio é lida com `mutagen`, via o
módulo compartilhado `src/audio.py` (também usado pela "Evolução por período").
- **Gráficos:** tempo total de áudio por pessoa · duração média por áudio, por pessoa
  (com linha de média do grupo) · galeria com as 5 figurinhas mais repetidas por pessoa
  (miniaturas reais; a legenda de cada miniatura, com a posição no ranking e quantas
  vezes foi enviada, está em fonte grande — ex.: "1º · 10x").
- **Tabelas:** resumo de áudio por pessoa (quantidade total, quantidade com duração
  medida, tempo total, duração média) · áudios detalhados (data, pessoa, arquivo,
  duração) · top 5 figurinhas por pessoa.
- **Nota:** a duração média usa só os áudios com duração medida com sucesso; se algum
  áudio não puder ser lido (arquivo corrompido/formato não suportado), ele ainda entra
  na contagem total e um insight avisa quantos ficaram de fora do tempo/média.

## 12. Nuvem de palavras (`wordcloud_analysis.py`)
Palavras mais usadas, tamanho proporcional à frequência (stopwords em português
removidas; links, e-mails e números descartados).
- **Gráficos:** nuvem de palavras do grupo inteiro · uma nuvem de palavras por pessoa.
- **Tabelas:** nenhuma (só gráficos).

---

### Como adicionar/alterar uma análise
Ver o cabeçalho de `src/analyses/__init__.py`: cada análise é um módulo com `KEY`,
`TITLE`, `ICON`, `REQUIRES_MEDIA` e uma função `run(ctx) -> AnalysisResult`. Ao criar,
remover ou alterar gráficos/tabelas de uma análise, atualize este arquivo na mesma
alteração.
