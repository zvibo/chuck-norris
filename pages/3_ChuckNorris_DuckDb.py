import requests
import streamlit as st
from sentence_transformers import SentenceTransformer
from duckdb import connect
from pathlib import Path
import pandas as pd
import json
import time
from utils import show_code, cache_data, get_chuck_jokes, get_moderated_jokes


st.set_page_config(page_title="CNDuck", page_icon="🌍",layout="wide")

DB_NAME = "jokes_e5_sm_v2.duckdb"
PARAMS_NAME = "jokes_e5_sm_v2.json"
building = False

# def get_db_ro(): return connect(database = DB_NAME, read_only = True)
def db_exists(): return Path(DB_NAME).exists()
def get_db_rw(): return connect(database = DB_NAME, read_only = False)


@cache_data(PARAMS_NAME)
def get_joke_params():
    jokes = get_moderated_jokes()
    joke_ids = [joke['id'] for joke in jokes]
    joke_strs = [joke['text'] for joke in jokes]
    joke_moderations = [joke['moderated'] for joke in jokes]
    joke_queries = ['query: ' + joke_str for joke_str in joke_strs]
    my_model = SentenceTransformer('intfloat/e5-small-v2')
    joke_embeddings = my_model.encode(joke_queries, normalize_embeddings=True)
    joke_tpls = zip(joke_ids, joke_strs,  joke_moderations, joke_embeddings.tolist())
    joke_params = [list(t) for t in joke_tpls]
    return joke_params


def build_chuck_db():
    joke_params = get_joke_params()
    db_rw = get_db_rw()
    db_rw.execute("CREATE TABLE if not exists jokes (id STRING, text STRING, is_unsafe BOOLEAN, embedding FLOAT[384])")
    db_rw.executemany("INSERT INTO jokes VALUES (?, ?, ?, ?)", joke_params)
    db_rw.checkpoint()
    db_rw.close()
    n_results = db_rw.execute('select count(1) from jokes').fetchall()[0][0]
    st.write(f"Database just built with {n_results} jokes at {DB_NAME}")
    return n_results

if not db_exists(): 
    build_chuck_db()

@st.cache_resource()
def get_model():
    return SentenceTransformer('intfloat/e5-small-v2')


my_model = get_model()
my_db = get_db_rw()    

def e5_embed(str, model = my_model):
    return model.encode([str], normalize_embeddings=True)[0]

def search_duck(query, model = my_model, db = my_db, is_unsafe = False):
    db.execute(f"SELECT array_cosine_similarity(embedding, ?::FLOAT[384]) as score, text "
                    "FROM jokes where is_unsafe = ? ORDER BY score DESC LIMIT 100",
                    parameters = [e5_embed(query), is_unsafe])
    return db.fetchall()

def main():
    n_jokes = my_db.execute('select count(1) from jokes where is_unsafe = False').fetchall()[0][0]
    query = st.text_input("Search {} jokes with **DuckDB**".format(n_jokes), "")
    st.button('Re-Load')
    if len(query) > 1:
        start = time.time()
        results = search_duck(query)
        end = time.time()
        df = pd.DataFrame(results, columns = ['score', 'joke'])
        st.write(f"Search took {end - start:.2f} seconds.")
        st.table(df)
    else:
        show_code(get_joke_params)
        show_code(build_chuck_db)
        show_code(search_duck)
        show_code(e5_embed)
        show_code(main)

if __name__ == "__main__":
    main()