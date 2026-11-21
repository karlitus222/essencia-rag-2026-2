# Roteiro para a demonstração

O vídeo fica para a etapa final. Este roteiro descreve somente ações que podem ser demonstradas com os serviços locais; não utiliza respostas gravadas para simular uma chamada ao modelo.

1. Apresentar a finalidade: uma central de ajuda para uma loja fictícia, com consulta a guias próprios. Mostrar que não é uma consulta livre à internet ou ao estoque real.
2. Abrir **Conheça a base** e consultar a ficha da Garrafa Essencial. Mostrar a capacidade, o preço do catálogo inicial e as características que não foram informadas.
3. Abrir **Como funciona**, mostrando os cinco passos e os dados reais do índice: documentos, trechos e dimensão dos vetores.
4. No Qdrant, abrir `http://127.0.0.1:6336/dashboard`, selecionar a coleção cujo nome aparece na interface e mostrar os pontos. Explicar que cada ponto guarda o vetor e os metadados do trecho, incluindo texto e origem.
5. Fazer uma pergunta por significado: **Quero algo para carregar meu computador nas costas.** Mostrar o trecho da Mochila Urbana recuperado por similaridade.
6. Perguntar: **Qual a capacidade da Garrafa Essencial e o preço no catálogo inicial?** Abrir **Ver como a resposta foi encontrada**. Mostrar o tempo de busca, o tempo de geração, a similaridade, os trechos e os rótulos de fonte.
7. Mostrar no código `rag.py` a transformação da pergunta com `/api/embed`, a consulta `/points/query` ao Qdrant e a montagem do contexto enviado para `/api/chat`. Destacar que o modelo de texto recebe o conteúdo recuperado no banco.
8. Perguntar: **Qual a composição química da atmosfera de Júpiter?** Conferir que nenhum trecho ultrapassa o limite e que a geração não é acionada.
9. Perguntar: **Quantas horas dura a bateria do Fone Studio?** Mostrar que a ficha não documenta a duração, embora a pergunta encontre o produto correto.
10. Apresentar o README, as instruções de execução e os testes. Explicar que referências válidas não garantem ausência de erro e que os guias são fictícios.

Antes de gravar, iniciar o Docker e executar `python -m streamlit run app.py`. Se os documentos mudaram, atualizar o índice. Uma primeira consulta pode demorar mais por causa do carregamento do modelo na CPU.

Após a gravação, acrescentar o link do vídeo no README e entregar no Gennera o link do GitHub e o link do vídeo, conforme o enunciado. Não enviar a atividade como concluída sem esses dois links.
