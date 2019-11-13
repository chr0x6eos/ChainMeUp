import datetime
import json
import os
import time
from hashlib import sha256

import blocksec2go

import requests
from flask import render_template, redirect, request

from app import app
import CardReader

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []

def fetch_posts():
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)

@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='ChainMeUp',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/submit', methods=['POST'])
def submit_textarea():
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    reader = CardReader.initReading()

    publicOne = 'None'
    publicTwo = CardReader.read_public_key(reader, 1)

    json_object = {'publicOne': publicOne,
                   'publicTwo': publicTwo.hex(),
                   'timestamp': time.time()}

    hash, sign = CardReader.generateSignature(reader, json_object)

    if CardReader.verifyPub(reader, publicTwo, hash, sign):
        requests.post(new_tx_address,
                      headers={'Content-type': 'application/json'},
                      json=json_object)

    return redirect('/')

@app.route('/newnode', methods=['POST'])
def submit_textarega():
    new_tx_address = "{}/register_node".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address, headers={'Content-type': 'application/json'}, json={'node_address': 'http://127.0.0.1:8000'})
    return redirect('/')

def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
