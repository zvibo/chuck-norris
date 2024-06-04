# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import textwrap
import requests

import streamlit as st
from functools import wraps
import more_itertools as mit

import openai
import json
import os



def show_code(demo):
    """Showing the code of the demo."""
    # Showing the code of the demo.
    sourcelines, _ = inspect.getsourcelines(demo)
    st.code(textwrap.dedent("".join(sourcelines[:])))

def cache_data(temp_file):
    """Caching the data."""
    def outer_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if os.path.exists(temp_file):
                return json.loads(open(temp_file).read())
            else:
                data = func(*args, **kwargs)
                with open(temp_file, 'w') as f:
                    f.write(json.dumps(data))
                return data
        return wrapper
    
    return outer_wrapper

# chuck-norris specific functions
@st.cache_data()
def get_chuck_jokes(): 
    chuck_url = 'https://api.chucknorris.io/jokes/search?query=%25%25%25'
    result = requests.get(chuck_url).json()['result']
    return [{'id':j['id'], 'text':j['value']} for j in result]

@cache_data('chuck_jokes_moderated.json')
def get_moderated_jokes():
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


