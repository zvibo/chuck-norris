import requests
import streamlit as st
from utils import show_code, cache_data, get_chuck_jokes, get_moderated_jokes
import time

st.set_page_config(page_title="CNJokes (Raw)", page_icon="🌍",layout="wide")

def search_jokes_substring(joke_list, theme, n_to_get=10, is_moderated=False):
    found_jokes = [joke['text'] for joke in joke_list 
                   if theme.lower() in joke['text'].lower()
                   and joke['moderated'] == is_moderated]
    return found_jokes[:n_to_get]

is_unsafe = False
jokes = [j for j in get_moderated_jokes() if j['moderated'] == is_unsafe]
theme = st.text_input("Search {} Chuck Norris Jokes with **simple substring matching**".format(len(jokes)), "")
st.button('Re-Load')

if theme:
    n_jokes = 100
    start = time.time()
    here_jokes = search_jokes_substring(jokes, theme, n_to_get=n_jokes, is_moderated=False)
    end = time.time()
    st.write(f"Found {len(here_jokes)} jokes in {end-start:.2f} seconds.")
    st.table(here_jokes)
else:
    show_code(get_chuck_jokes)
    show_code(get_moderated_jokes)
    show_code(search_jokes_substring)
    show_code(cache_data)
    show_code(show_code)
    