import requests
import streamlit as st
from sentence_transformers import SentenceTransformer
from duckdb import connect
from pathlib import Path
import pandas as pd
import json
import time


st.set_page_config(page_title="Chuck Norris DB", page_icon="🌍",layout="wide")

DB_NAME = "jokes_e5_sm_v2.duckdb"
PARAMS_NAME = "jokes_e5_sm_v2.json"
building = False
built = False

def get_db_ro(): return connect(database = DB_NAME, read_only = True)
def get_db_rw(): return connect(database = DB_NAME, read_only = False)

def build_it():
    global building, built
    if building: return
    #
    def api_cn_jokes(): return requests.get ('https://api.chucknorris.io/jokes/search?query=%25%25%25').json()['result']
    def clean_result(result): return [{'id':j['id'], 'text':j['value']} for j in result]
    def get_chuck_jokes(): return clean_result(api_cn_jokes())
    def get_joke_params():
        jokes = get_chuck_jokes()
        joke_ids = [joke['id'] for joke in jokes]
        joke_strs = [joke['text'] for joke in jokes]
        joke_queries = ['query: ' + joke_str for joke_str in joke_strs]
        my_model = SentenceTransformer('intfloat/e5-small-v2')
        joke_embeddings = my_model.encode(joke_queries, normalize_embeddings=True)
        joke_tpls = zip(joke_ids, joke_strs, joke_embeddings.tolist())
        joke_params = [list(t) for t in joke_tpls]
        return joke_params
    #
    def build_chuck_db():
        if not Path(PARAMS_NAME).exists():
            joke_params = get_joke_params()
            with open(PARAMS_NAME, 'w') as f:
                json.dump(joke_params, f)
        else:
            with open(PARAMS_NAME, 'r') as f:
                joke_params = json.load(f)
        #
        db_rw = get_db_rw()
        db_rw.execute("CREATE TABLE if not exists jokes (id STRING, text STRING, embedding FLOAT[384])")
        db_rw.executemany("INSERT INTO jokes VALUES (?, ?, ?)", joke_params)
        db_rw.checkpoint()
        db_rw.close()
        db_ro = get_db_ro()
        n_results = db_ro.execute('select count(1) from jokes').fetchall()[0][0]
        db_ro.close()
        return n_results

    if Path(DB_NAME).exists():
        built = True
        my_db = connect(database = DB_NAME, read_only = True)    
        n_jokes = my_db.execute('select count(1) from jokes').fetchall()[0][0]
        my_db.close()
        st.write(f"Database {DB_NAME} contains {n_jokes} jokes.")
    else:
        building = True
        n_jokes = build_chuck_db()
        st.write(f"Database built with {n_jokes} jokes at {DB_NAME}")

build_it()

my_model = SentenceTransformer('intfloat/e5-small-v2')
my_db = get_db_ro()    

def e5_embed(str, model = my_model):
    return model.encode([str], normalize_embeddings=True)[0]

def search_duck(query, model = my_model, db = my_db):
    db.execute(f"SELECT array_cosine_similarity(embedding, ?::FLOAT[384]) as score, text "
                    "FROM jokes ORDER BY score DESC LIMIT 100",
                    parameters = [e5_embed(query)])
    return db.fetchall()

old_query = None
query = st.text_input("Search", "technology")
st.button('Re-Load')
if len(query) > 5 and old_query != query:
    start = time.time()
    results = search_duck(query)
    end = time.time()
    df = pd.DataFrame(results, columns = ['score', 'joke'])
    st.write(f"Search took {end - start:.2f} seconds.")
    st.table(df)
    old_query = query
