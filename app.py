import json

import streamlit as st

from rag import Rag, ServiceError, read_documents

st.set_page_config(page_title="Essência · Central de ajuda", page_icon="✳", layout="wide")
st.markdown("""<style>
.stApp {background:#faf8f4; color:#302d29;}
[data-testid="stSidebar"] {background:#f0ece5;}
.block-container {max-width:1140px;padding-top:2.1rem;}
.marca {font-family:Georgia,serif;font-size:1.45rem;letter-spacing:.03em;color:#7d3d48;}
.abertura {padding:28px 32px;background:#eee6df;border:1px solid #e2d5ca;border-radius:20px;margin:18px 0 24px;}
.abertura h1 {font-family:Georgia,serif;font-weight:500;font-size:2.7rem;line-height:1.15;margin:0 0 12px;color:#513438;}
.abertura p {max-width:650px;font-size:1.03rem;margin:0;color:#675c55;}
.stButton>button {border-radius:10px;}
[data-testid="stChatMessage"] {border-radius:16px;background:white;border:1px solid #e8e0d7;}
div[data-testid="stMetric"] {padding:12px 16px;background:white;border:1px solid #e8e0d7;border-radius:12px;}
</style>""", unsafe_allow_html=True)

client = Rag()
documents = read_documents(client.settings.documents_dir)
st.session_state.setdefault("messages", [])

with st.sidebar:
    st.markdown('<div class="marca">✳ essência</div>', unsafe_allow_html=True)
    st.caption("CENTRAL DE AJUDA")
    st.divider()
    st.subheader("Uma pergunta de cada vez")
    st.write("Consulte características dos produtos e orientações de compra, entrega e atendimento.")
    st.caption("Demonstração acadêmica. Loja e condições de atendimento fictícias.")
    st.divider()
    try:
        manifest = client.manifest()
        st.success(f"Base pronta · {manifest['documents']} guias")
        ready = True
    except (ServiceError, ValueError, KeyError) as error:
        st.info(str(error))
        manifest, ready = None, False
    if st.button("Preparar base" if not ready else "Atualizar base", icon=":material/sync:", use_container_width=True):
        try:
            with st.status("Preparando os guias…", expanded=True) as status:
                progress = st.progress(0, text="Gerando os vetores dos documentos")
                manifest = client.index(lambda done, total: progress.progress(done / total, text=f"{done} de {total} trechos preparados"))
                status.update(label=f"Base pronta: {manifest['chunks']} trechos armazenados", state="complete", expanded=False)
            st.toast("Guias atualizados. Você já pode perguntar.", icon="✅")
            st.rerun()
        except (ServiceError, ValueError, KeyError) as error:
            st.error(str(error))
    if st.button("Limpar conversa", icon=":material/delete_sweep:", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("As perguntas desta conversa ficam somente na sessão. O assistente não acessa pedidos ou dados de clientes.")

st.markdown('<div class="marca">essência <span style="color:#a99488">/</span> central de ajuda</div>', unsafe_allow_html=True)
st.markdown("""<div class="abertura"><h1>Como podemos<br>ajudar no seu dia?</h1>
<p>Encontre respostas nos nossos guias, com o caminho até a informação sempre à vista.</p></div>""", unsafe_allow_html=True)

tab_chat, tab_guides, tab_flow = st.tabs(["Converse com os guias", "Conheça a base", "Como funciona"])


def show_answer(result):
    st.markdown(result["answer"])
    used = [item for item in result["matches"] if item["label"] in result["sources"]]
    if used:
        st.caption("Fontes utilizadas: " + " · ".join(f"[{x['label']}] {x['title']}" for x in used))
    with st.expander("Ver como a resposta foi encontrada"):
        st.caption("Similaridade é uma medida de proximidade entre vetores; não é probabilidade de a resposta estar correta.")
        a, b, c = st.columns(3)
        a.metric("Busca e embedding", f"{result['retrieval_seconds']:.1f} s")
        b.metric("Geração", f"{result['generation_seconds']:.1f} s")
        c.metric("Trechos recuperados", len(result["matches"]))
        if result["matches"]:
            for match in result["matches"]:
                st.markdown(f"**[{match['label']}] {match['title']}** · similaridade `{match['score']:.3f}`")
                st.text(match["text"])
                st.caption(f"Arquivo: {match['file']} · trecho {match['chunk']}")
        else:
            st.write("Nenhum trecho atingiu o limite mínimo. A geração pelo modelo não foi acionada.")
            if result["top_score"] is not None:
                st.caption(f"Maior similaridade encontrada: {result['top_score']:.3f}")
        st.caption(f"Coleção consultada: {result['manifest']['collection']}")
        st.caption(f"Embeddings: {result['manifest']['embedding_model']} · {result['manifest']['dimension']} dimensões · limite {client.settings.min_score:.2f}")


with tab_chat:
    if not st.session_state.messages:
        st.write("**Experimente uma pergunta**")
        examples = ["Qual mochila vocês têm para levar um notebook?", "Como funciona a entrega em Teresina?", "Qual é a capacidade da garrafa térmica?"]
        cols = st.columns(3)
        for column, example in zip(cols, examples):
            if column.button(example, disabled=not ready, use_container_width=True):
                st.session_state["pending_question"] = example
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="✳" if message["role"] == "assistant" else None):
            if message["role"] == "assistant":
                show_answer(message["result"])
            else:
                st.markdown(message["content"])
    typed = st.chat_input("Pergunte sobre produtos ou atendimento…", disabled=not ready, max_chars=600)
    question = typed or st.session_state.pop("pending_question", None)
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="✳"):
            try:
                with st.spinner("Consultando os guias e preparando a resposta…", show_time=True):
                    result = client.answer(question)
                show_answer(result)
                st.session_state.messages.append({"role": "assistant", "result": result})
            except (ServiceError, ValueError, KeyError) as error:
                st.error(str(error))
                st.caption("A pergunta não gerou uma resposta válida. Confira os serviços ou tente reformulá-la.")
    st.caption("As informações são do catálogo inicial de demonstração. Confirme preço e disponibilidade com o atendimento.")

with tab_guides:
    st.subheader("Guias que ajudam a responder")
    st.write("Você pode ler a mesma base utilizada na consulta. Nenhuma busca é feita na internet durante a resposta.")
    search = st.text_input("Filtrar guias pelo título", placeholder="Ex.: mochila, entrega, pagamento")
    for doc in documents:
        if search.casefold() not in doc["title"].casefold():
            continue
        with st.expander(doc["title"]):
            st.markdown(doc["text"])
            st.caption(doc["file"])

with tab_flow:
    st.subheader("Da pergunta à resposta, com contexto")
    steps = st.columns(5)
    for column, title, description in zip(steps,
            ["01 · Pergunta", "02 · Embedding", "03 · Busca", "04 · Contexto", "05 · Resposta"],
            ["Você escreve uma dúvida.", "O modelo representa seu significado em um vetor.",
             "O Qdrant recupera os trechos mais próximos.", "Os trechos aprovados são enviados ao modelo de texto.",
             "O modelo responde e indica as fontes consultadas."]):
        column.markdown(f"**{title}**")
        column.write(description)
    st.divider()
    st.write("Na preparação, os guias são divididos em trechos com sobreposição. Os embeddings ficam armazenados no Qdrant com o texto, o título e a origem. A busca usa similaridade de cosseno. Apenas os trechos que atingem o limite mínimo seguem para a geração.")
    st.write("Se nenhum trecho atingir esse limite, a aplicação informa a limitação sem consultar o modelo de texto. Mesmo com trechos próximos, uma característica pode não estar documentada; o modelo é instruído a reconhecer essa ausência. As fontes ficam disponíveis para conferência.")
    if manifest:
        a, b, c = st.columns(3)
        a.metric("Documentos", manifest["documents"])
        b.metric("Vetores armazenados", manifest["chunks"])
        c.metric("Dimensões por vetor", manifest["dimension"])
        st.code(json.dumps(manifest, ensure_ascii=False, indent=2), language="json")
    st.caption(f"Modelo de embeddings: {client.settings.embedding_model} · modelo de texto: {client.settings.chat_model}")
