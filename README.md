# Essência — Central de ajuda com busca vetorial

Assistente para consultar produtos e orientações de atendimento de uma loja fictícia. A aplicação recupera trechos dos guias em um banco de dados vetorial e utiliza esses trechos como contexto para gerar uma resposta em português, acompanhada de suas fontes.

Projeto de Banco de Dados · composição da 3ª nota · 2026/2.

## Objetivo

Transformar os guias da loja em uma base consultável por significado. Uma pergunta como “quero carregar meu computador nas costas” pode localizar a ficha da Mochila Urbana sem depender da ocorrência exata da palavra pesquisada no documento.

A solução funciona como uma central complementar ao [Catálogo Poliglota](https://github.com/karlitus222/catalogo-poliglota-2026-2). As fichas descrevem os seis produtos do catálogo inicial. As condições de atendimento são fictícias e identificadas como demonstração. Não há acesso aos bancos do catálogo, pedidos de clientes, telefone particular ou estoque em tempo real.

## Tecnologias

| Parte | Tecnologia |
|---|---|
| Interface | Python 3.12 e Streamlit 1.51.0 |
| Banco vetorial | Qdrant 1.20.2, persistente em volume Docker |
| Embeddings | Qwen3 Embedding 0.6B executado pelo Ollama |
| Respostas | Qwen3 1.7B executado pelo Ollama |
| Comunicação | APIs HTTP locais; cliente em biblioteca padrão do Python |
| Infraestrutura | Docker Compose e Ollama 0.40.17 |

Não é necessário contratar uma API. O primeiro uso baixa as imagens Docker e os modelos; os downloads ocupam vários gigabytes. Depois do preparo, as consultas usam os serviços locais. Recomenda-se disponibilizar pelo menos 8 GB de memória para o Docker, além da memória do sistema, e espaço livre para as imagens e os modelos. A execução em CPU é mais lenta, especialmente na primeira consulta.

## Executar

Pré-requisitos: Python 3.12 e Docker com Compose funcionando. Na pasta do repositório:

```sh
python -m venv .venv
```

Ative o ambiente no PowerShell com `.\.venv\Scripts\Activate.ps1` ou, no Linux/macOS, com `source .venv/bin/activate`. Instale a interface:

```sh
python -m pip install -r requirements.txt
docker compose up -d
docker compose exec -T ollama ollama pull qwen3-embedding:0.6b
docker compose exec -T ollama ollama pull qwen3:1.7b
python rag.py indexar
python -m streamlit run app.py
```

No Windows, `./preparar.ps1` reúne o início dos serviços, o download dos modelos e a indexação. Execute depois de instalar as dependências e ativar o ambiente virtual. Se o serviço ainda estiver iniciando, aguarde a inicialização e repita a preparação.

Abra **http://127.0.0.1:8508**. A interface permite perguntar, consultar os documentos e visualizar o fluxo RAG. O botão **Preparar base / Atualizar base** também executa a indexação. Para conferir o banco, abra **http://127.0.0.1:6336/dashboard**.

Para consultar sem a interface:

```sh
python rag.py perguntar "Qual é a capacidade da garrafa térmica?"
```

As portas estão vinculadas a `127.0.0.1`. A configuração destina-se à demonstração local. Os volumes `modelos` e `vetores` preservam dados entre reinícios. `docker compose stop` interrompe os serviços sem remover os volumes.

## Fluxo de indexação e consulta

1. Os arquivos Markdown de `conhecimento/` são lidos e divididos em trechos de até 850 caracteres, com sobreposição de 100 caracteres e preferência por limites de palavras.
2. O Ollama gera embeddings dos textos com Qwen3 Embedding. A dimensão é obtida da resposta real do modelo e usada para criar a coleção no Qdrant.
3. O banco recebe o vetor e os metadados: texto, título, arquivo, número do trecho, versão da base e modelo.
4. A pergunta recebe uma instrução de recuperação e é transformada pelo mesmo modelo de embeddings.
5. O Qdrant retorna os três trechos mais próximos por similaridade de cosseno. Somente os que atingem o limite mínimo configurado seguem para a geração.
6. A pergunta e os trechos recuperados compõem o contexto enviado ao Qwen3 1.7B. O modelo recebe instruções para usar somente as fontes e reconhecer informação ausente.
7. A resposta estruturada é validada. Referências desconhecidas ou formato inválido produzem um erro explícito, sem uma resposta inventada pela aplicação. O usuário pode abrir os trechos e conferir as fontes.

Sem trecho acima do limite, a aplicação responde que não encontrou informação suficiente e não chama o modelo de texto. Similaridade não equivale à probabilidade de uma resposta estar correta. A validação de rótulos garante referências existentes; não prova, por si só, que cada afirmação é sustentada pelo texto.

O limite inicial é 0,42. Foi escolhido após comparar perguntas de paráfrase sobre os guias com uma pergunta fora do domínio. É um ajuste exploratório para esta pequena base, não uma garantia universal de relevância.

## Atualizar os guias

Edite ou acrescente arquivos `.md` na pasta `conhecimento/` e execute `python rag.py indexar`. O programa usa um identificador baseado no conteúdo, na versão do modelo e nas regras de divisão. Alterações geram uma nova coleção, preservando a anterior. Uma indexação repetida da mesma versão utiliza IDs determinísticos e não duplica pontos.

O arquivo local `.runtime/indice.json` aponta para a versão preparada. Ele é atualizado somente após a contagem de pontos no banco coincidir com os trechos. Se os documentos ou o modelo mudarem, as consultas são interrompidas até uma nova preparação. Isso evita misturar documentos de versões diferentes ou embeddings incompatíveis.

As coleções antigas permanecem no volume até uma limpeza administrativa explícita; não existe exclusão automática. A aplicação não indexa documentos enviados pelo visitante.

## Configuração opcional

As variáveis `QDRANT_URL`, `OLLAMA_URL`, `EMBEDDING_MODEL` e `CHAT_MODEL` permitem apontar para serviços equivalentes. Os valores padrão são os do Compose. Ao alterar o modelo de embeddings, instale o novo modelo e reindexe a base. O limite de similaridade e a quantidade de resultados estão em `Settings`, no arquivo `rag.py`.

## Estrutura

```text
app.py                 interface, conversa e inspeção das fontes
rag.py                 indexação, busca semântica e geração
conhecimento/          guias e fichas dos produtos
compose.yaml           banco e servidor de modelos
preparar.ps1           preparação no Windows
tests/                 verificações de recuperação e do fluxo
docs/                  resultados e roteiro da demonstração
.runtime/              estado local do índice (não versionado)
```

## Limitações

A base é pequena e estática. Os guias podem não ter a informação solicitada, e o modelo de texto pode cometer erros mesmo recebendo contexto. A finalidade é demonstrar o fluxo real de banco vetorial e RAG. O sistema não toma decisões sobre trocas, não confirma pagamentos, não executa compras e não substitui o atendimento. Cada pergunta é consultada de forma independente; mensagens anteriores ficam visíveis, mas não são usadas como conhecimento.

## Verificação

Com os modelos instalados e os serviços ativos:

```sh
python -m unittest discover -s tests -v
```

Os testes usam Qdrant e Ollama reais e criam ou reutilizam a coleção de demonstração. Abrangem indexação sem duplicação, busca por paráfrases, pergunta fora do domínio, geração com fontes, característica não documentada, bloqueio de índice desatualizado, limites da pergunta e divisão dos documentos. A execução verificada aprovou os oito testes. Os resultados e os exemplos de respostas estão em [docs/validacao.md](docs/validacao.md).

O [roteiro da demonstração](docs/roteiro-demonstracao.md) orienta a apresentação da interface, dos pontos no banco e da montagem do contexto.

## Referências técnicas

- [Qdrant: criação de coleção](https://api.qdrant.tech/api-reference/collections/create-collection), [armazenamento de pontos](https://api.qdrant.tech/api-reference/points/upsert-points) e [consulta vetorial](https://api.qdrant.tech/api-reference/search/query-points).
- [Ollama: API de embeddings](https://docs.ollama.com/api/embed) e [API de chat](https://docs.ollama.com/api/chat).
- [Qwen3 Embedding: repositório e instruções de recuperação](https://github.com/QwenLM/Qwen3-Embedding).
- [Streamlit: AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).

O vídeo demonstrativo será acrescentado após a gravação. A preparação do código não equivale ao envio final da atividade.
