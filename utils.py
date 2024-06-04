"""Utility functions for the Streamlit demos."""

import json
import os
from functools import wraps

import inspect
import textwrap
import requests

import streamlit as st
import openai
import more_itertools as mit


def show_code(demo):
    """Showing the code of the demo."""
    # Showing the code of the demo.
    sourcelines, _ = inspect.getsourcelines(demo)
    st.code(textwrap.dedent("".join(sourcelines[:])))

def cache_data(temp_file):
    """Simple cache for functions that return json-encodable data."""
    def outer_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if os.path.exists(temp_file):
                return json.loads(open(temp_file, 'r', encoding='utf-8').read())

            data = func(*args, **kwargs)
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(data))
            return data
        return wrapper
    return outer_wrapper

# chuck-norris specific functions
@st.cache_data()
def get_chuck_jokes():
    """Getting the Chuck Norris jokes."""
    chuck_url = 'https://api.chucknorris.io/jokes/search?query=%25%25%25'
    result = requests.get(chuck_url).json()['result']
    return [{'id':j['id'], 'text':j['value']} for j in result]

@cache_data('chuck_jokes_moderated.json')
def get_moderated_jokes():
    """Getting the Chuck Norris jokes with moderation applied."""
    engine='text-moderation-stable'
    client, moderations = openai.Client(), []
    jokes = get_chuck_jokes()
    for my_texts in mit.chunked([j['text'] for j in jokes], 32):
        mods = client.moderations.create(input=my_texts, model=engine)
        flags = [r.flagged for r in mods.results]
        moderations.extend(flags)
    for joke, mod in zip(jokes, moderations):
        joke['moderated'] = mod
    return jokes