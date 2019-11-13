import datetime
import json
import os
import time
from hashlib import sha256

import blocksec2go

import requests
from flask import render_template, redirect, request

from app import app

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []

def get_reader():
  reader = None
  reader_name = 'Identiv uTrust 3700 F'
  while(reader == None):
    try:
      reader = blocksec2go.find_reader(reader_name)
      print('Found the specified reader and a card!', end='\r')
    except Exception as details:
      if('No reader found' == str(details)):
        print('No card reader found!     ', end='\r')
      elif('No card on reader' == str(details)):
        print('Found reader, but no card!', end='\r')
      else:
        print('ERROR: ' + str(details))
        raise SystemExit
  return reader

def activate_card(reader):
  try:
    blocksec2go.select_app(reader)
    print('Found the specified reader and a Blockchain Security 2Go card!')
  except Exception as details:
    print('ERROR: ' + str(details))
    raise SystemExit

def get_public_key(reader, key_id):
  try:
    if(blocksec2go.is_key_valid(reader, key_id)):
      global_counter, counter, key = blocksec2go.get_key_info(reader, key_id)
      return key
    else:
      raise RuntimeError('Key_id is invalid!')
  except Exception as details:
    print('ERROR: ' + str(details))
    raise SystemExit

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

    reader = get_reader()
    activate_card(reader)

    publicOne = 'None'
    publicTwo = get_public_key(reader, 1)

    json_object = {'publicOne': publicOne,
                   'publicTwo': publicTwo.hex(),
                   'timestamp': time.time()}

    block_string = json.dumps(json_object, sort_keys=True)
    hash_object = sha256(block_string.encode())
    hash = hash_object.digest()

    global_counter, counter, signature = blocksec2go.generate_signature(reader, 1, hash)

    if blocksec2go.verify_signature(publicTwo, hash, signature):
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
