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
    new_tx_address = "{}/".format(CONNECTED_NODE_ADDRESS)
    return requests.get(new_tx_address).text

@app.route('/register')
def register():
    new_tx_address = "{}/register".format(CONNECTED_NODE_ADDRESS)
    return requests.get(new_tx_address).text

@app.route('/login')
def login():
    new_tx_address = "{}/login".format(CONNECTED_NODE_ADDRESS)
    return requests.get(new_tx_address).text

@app.route('/login', methods=['POST'])
def submit_login():
    new_tx_address = "{}/login".format(CONNECTED_NODE_ADDRESS)
    reader = CardReader.initReading()
    publicOne = CardReader.read_public_key(reader, 1)
    if CardReader.auth(reader, publicOne):
        return requests.post(new_tx_address,headers={'Content-type': 'application/json'},json={'pubkey': publicOne.hex()}).text
    else:
        return "PubKey not found."

    return redirect('/')

@app.route('/register', methods=['POST'])
def submit_register():
    new_tx_address = "{}/register".format(CONNECTED_NODE_ADDRESS)
    reader = CardReader.initReading()
    if reader is None:
        return "No reader connected!"
    if not CardReader.initCard(reader):
        return "Card not writeable or a user is already registered with this card!"

    pubkey = CardReader.read_public_key(reader, 1)

    if pubkey is None:
        return "No pubkey!"
    else:
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        phonenr = request.form['phonenr']
        email = request.form['email']
        return requests.post(new_tx_address,headers={'Content-type': 'application/json'},json={'pubkey': pubkey.hex(), 'firstname': firstname, 'lastname': lastname, 'email': email, 'phonenr': phonenr}).text
    return redirect('/')
'''
@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='ChainMeUp',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)
'''


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
