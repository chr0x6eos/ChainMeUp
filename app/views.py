import datetime
import json
import os
import time

import requests
from flask import render_template, redirect, request, session

from app import app
import CardReader

CONNECTED_NODE_ADDRESS = "http://169.254.62.57:8000"

posts = []
pk = None

def fetch_posts(isFiltered=True):
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                ty = {}
                ty["index"] = block["index"]
                ty["hash"] = block["previous_hash"]
                ty["timestamp"] = tx["timestamp"]
                #print(tx)
                new_tx_address = "{}/api/profile".format(CONNECTED_NODE_ADDRESS)
                p1,status1 = requests.post(new_tx_address, headers={'Content-type': 'application/json'}, json={'pubkey': tx['publicOne']}).json()
                p2,status2 = requests.post(new_tx_address, headers={'Content-type': 'application/json'}, json={'pubkey': tx['publicTwo']}).json()
                #print(status1,status2)
                if status1 == 200 and status2 == 200:
                    p = p1['person']

                    ty['one'] = { "publicKey":tx['publicOne'],
                                  "lastname": p['lastname'],
                                  "firstname": p['firstname'],
                                  "email": p['email'],
                                  "phonenr": p['phonenr'],
                                  "date_created": p['date_created']
                    }
                    p = p2['person']
                    ty['two'] = {"publicKey": tx['publicTwo'],
                                 "lastname": p['lastname'],
                                 "firstname": p['firstname'],
                                 "email": p['email'],
                                 "phonenr": p['phonenr'],
                                 "date_created": p['date_created']
                                 }
                    #print(ty)
                content.append(ty)

        global posts

        if isFiltered:
            #print(_posts)
            #print(_posts[0]['one']['publicKey'])
            #posts = list(filter(lambda k: k['one']['publicKey'] == pk, _posts))
            #lambda k: print(k['one']['publicKey']), _posts
            _posts = []
            if pk is not None:
                for k in content:
                    if k['one']['publicKey'] == pk.hex():
                        _posts.append(k)
            else:
                # Return error
                pass
        else:
            _posts = content
        posts = sorted(_posts, key=lambda k: k['timestamp'],
                           reverse=True)


@app.route('/display')
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

@app.route('/me', methods=['GET', 'POST'])
def submit_login():
    global pk
    new_tx_address = "{}/login".format(CONNECTED_NODE_ADDRESS)
    if pk:
        req = requests.post(new_tx_address, headers={'Content-type': 'application/json'}, json={'pubkey': pk.hex()})
        return req.text

    reader = CardReader.initReading()
    if reader:
        pubkey = CardReader.read_public_key(reader, 1)

        if CardReader.auth(reader, pubkey):
            req = requests.post(new_tx_address,headers={'Content-type': 'application/json'},json={'pubkey': pubkey.hex()})
            pk = pubkey
            return req.text
        else:
            return "PubKey not found."
    else:
        return "No Card found!"

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
        global pk
        pk = pubkey
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        phonenr = request.form['phonenr']
        email = request.form['email']
        return requests.post(new_tx_address,headers={'Content-type': 'application/json'},json={'pubkey': pubkey.hex(), 'firstname': firstname, 'lastname': lastname, 'email': email, 'phonenr': phonenr}).text

@app.route('/')
def display():
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
    if reader:
        global pk
        publicOne = pk
        publicTwo = CardReader.read_public_key(reader, 1)
        if publicOne is not None and publicTwo is not None:
            if publicOne != publicTwo:

                json_object = {'publicOne': publicOne.hex(),
                               'publicTwo': publicTwo.hex(),
                               'timestamp': time.time()}

                hash, sign = CardReader.generateSignature(reader, json_object)

                if CardReader.verifyPub(reader, publicTwo, hash, sign):
                    requests.post(new_tx_address,
                                  headers={'Content-type': 'application/json'},
                                  json=json_object)

    return redirect('/me')

@app.route('/logout')
def logout():
    global pk
    pk = None
    return redirect('/')

def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
