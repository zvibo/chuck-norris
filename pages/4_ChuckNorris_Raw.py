import requests
import streamlit as st

st.set_page_config(page_title="Chuck Norris Jokes", page_icon="🌍",layout="wide")

# from llama_index.core import (
#     Document,
#     VectorStoreIndex, 
#     StorageContext,
#     load_index_from_storage
# )
# def load_chuck_index():
#     PERSIST_DIR = "cn_cache"
#     if not os.path.exists(PERSIST_DIR):
#         # load the documents and create the index

#         documents = load_chuck_documents()
#         index = VectorStoreIndex.from_documents(documents)
#         # store it for later
#         index.storage_context.persist(persist_dir=PERSIST_DIR)
#     else:
#         # load the existing index
#         storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
#         index = load_index_from_storage(storage_context)
#     return index

@st.cache_data()
def get_chuck_jokes(): 
    result = requests.get('https://api.chucknorris.io/jokes/search?query=%25%25%25').json()['result']
    return [{'id':j['id'], 'text':j['value']} for j in result]

jokes = get_chuck_jokes()

def get_chuck_norris_jokes(data, theme, n_to_get=10):
    found_jokes = [joke['text'] for joke in data if theme.lower() in joke['text'].lower()]
    return found_jokes[:n_to_get]
    # retriever = index.as_retriever(similarity_top_k=n_to_get)
    # results = retriever.retrieve(theme)
    # return [node.get_text() for node in results]

# st.markdown("# Chuck Norris Jokes")
# st.sidebar.header("Chuck Norris Jokes")

c1, c2 = st.columns(2)

# Theme selection
with c1:
    st.title("Chuck Norris Jokes")
    st.write("There are a total of {} jokes in the system.".format(len(jokes)))
    st.write("Select a theme to generate Chuck Norris jokes.")
    theme = st.text_input("Enter your theme (e.g. skills, technology, nature, history, invincibility, meta, etc.)", "technology")
    n_jokes = st.text_input("Enter the number of jokes to generate", 10)
    st.button('Re-Load')
    
    n_jokes = int(n_jokes)
    here_jokes = get_chuck_norris_jokes(jokes, theme, n_to_get=n_jokes)
    
with c2:
    st.table(here_jokes)
