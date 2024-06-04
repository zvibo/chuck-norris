import requests
import streamlit as st
import os, time
from utils import show_code, cache_data, get_chuck_jokes, get_moderated_jokes

st.set_page_config(page_title="CNJokes(LlamaIndex)", page_icon="🌍",layout="wide")

from llama_index.core import (
    Settings,
    Document,
    VectorStoreIndex, 
    StorageContext,
    load_index_from_storage
)

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding


def load_chuck_documents():
    return [Document(text=joke['text'], metadata={'joke_id':joke['id'], 'moderated':joke['moderated']}) 
            for joke in get_moderated_jokes()]


@st.cache_resource()
def load_chuck_index():
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="intfloat/e5-small-v2"
    )
    PERSIST_DIR = "cn_cache"
    if not os.path.exists(PERSIST_DIR):
        documents = load_chuck_documents()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=PERSIST_DIR) # persist the index.
    else:
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context) # load the existing index
    return index

@st.cache_resource()
def get_joke_count():
    return len([j for j in get_moderated_jokes() if j['moderated'] == is_unsafe])


def search_jokes_llama_index(index, theme, n_to_get=10, is_moderated=False):
    retriever = index.as_retriever(similarity_top_k=n_to_get)
    results = retriever.retrieve(theme)
    return [node.get_text() for node in results 
            if node.metadata["moderated"] == is_moderated
            ][:n_to_get]


is_unsafe = False
theme = st.text_input("Search {} jokes using **LlamaIndex**".format(get_joke_count()), "")
# is_unsafe = st.checkbox("Show unsafe jokes", value=False)
st.button('Re-Load')

if theme:
    start = time.time()
    index = load_chuck_index()
    here_jokes = search_jokes_llama_index(index, theme, n_to_get=100, is_moderated=is_unsafe)
    end = time.time()
    st.write(f"Found {len(here_jokes)} jokes in {end-start:.2f} seconds.")
    st.table(here_jokes)
else:
    show_code(load_chuck_documents)
    show_code(load_chuck_index)
    show_code(search_jokes_llama_index)