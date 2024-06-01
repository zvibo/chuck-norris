import requests
import streamlit as st
from sentence_transformers import SentenceTransformer
from duckdb import connect
from pathlib import Path
import json


DB_NAME = "jokes_e5_sm_v2.duckdb"
PARAMS_NAME = "jokes_e5_sm_v2.json"



def api_cn_jokes(): return requests.get('https://api.chucknorris.io/jokes/search?query=%25%25%25').json()['result']
def clean_result(result): return [{'id':j['id'], 'text':j['value']} for j in result]
def get_chuck_jokes(): return clean_result(api_cn_jokes())
def get_joke_params():
    my_model = SentenceTransformer('intfloat/e5-small-v2')
    jokes = get_chuck_jokes()
    joke_ids = [joke['id'] for joke in jokes]
    joke_strs = [joke['text'] for joke in jokes]
    joke_queries = ['query: ' + joke_str for joke_str in joke_strs]
    joke_embeddings = my_model.encode(joke_queries, normalize_embeddings=True)
    joke_tpls = zip(joke_ids, joke_strs, joke_embeddings.tolist())
    joke_params = [list(t) for t in joke_tpls]
    return joke_params

def build_chuck_db():
    if not Path(PARAMS_NAME).exists():
        joke_params = get_joke_params()
        with open(PARAMS_NAME, 'w') as f:
            json.dump(joke_params, f)
    else:
        with open(PARAMS_NAME, 'r') as f:
            joke_params = json.load(f)

    db_rw = connect(database = DB_NAME, read_only = False)
    db_rw.execute("CREATE TABLE if not exists jokes (id STRING, text STRING, embedding FLOAT[384])")
    db_rw.executemany("INSERT INTO jokes VALUES (?, ?, ?)", joke_params)
    db_rw.checkpoint()
    db_rw.close()
    db_ro = connect(database = DB_NAME, read_only = True)
    n_results = db_ro.execute('select count(1) from jokes').fetchall()[0][0]
    db_ro.close()
    return n_results

def ensure_db_built():
    if Path(DB_NAME).exists():
        print(f"Database already exists at {DB_NAME}")
        my_db = connect(database = DB_NAME, read_only = True)    
        n_jokes = my_db.execute('select count(1) from jokes').fetchall()[0][0]
        print(f"Database contains {n_jokes} jokes.")

    else:
        n_jokes = build_chuck_db()
        print(f"Database built with {n_jokes} jokes at {DB_NAME}")

if __name__ == "__main__":
    ensure_db_built()