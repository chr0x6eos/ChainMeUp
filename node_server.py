from datetime import datetime
import os
from hashlib import sha256
import json
import time
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, session, make_response, render_template
import requests
import blocksec2go

import CardReader


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def proof_of_work(self, block):
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block.hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        announce_new_block(new_block)
        return new_block.index

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

blockchain = Blockchain()
blockchain.create_genesis_block()

peers = set()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    # REQUIRED: Get Public Key
    tx_data = request.get_json()
    required_fields = ["publicOne", "publicTwo", "timestamp"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 404

    blockchain.add_new_transaction(tx_data)
    return "Success", 201

@app.route('/chain', methods=['GET'])
def get_chain():
    consensus()
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})

@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)


@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    peers.add(node_address)
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    blockchain = Blockchain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"])
        proof = block_data['hash']
        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        else:  # the block is a genesis block, no verification needed
            blockchain.chain.append(block)
    return blockchain

@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201

@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


def consensus():
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        print('{}/chain'.format(node))
        response = requests.get('{}/chain'.format(node))
        print("Content", response.content)
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))

class Person(db.Model):
    pubkey = db.Column(db.String(256), primary_key=True)
    lastname = db.Column(db.String(20), nullable=False)
    firstname = db.Column(db.String(20), nullable=False)
    phonenr = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return '<People %r>' % self.pubkey
@app.route('/', methods=['GET'])
def index():
    response = make_response(render_template('index.html'))
    session.clear()

    if request.method == "GET":
        return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        json_object = request.get_json()
        pubkey = json_object['pubkey']
        print(pubkey)
        if pubkey is not None:
            person = Person.query.get(pubkey)
        else:
            return "No or invalid pub!"

        if person is not None:
            response = make_response(render_template('main.html', person=person))
            session['pk'] = pubkey

            return response
        else:
            return "PubKey not registered"


@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        json_object = request.get_json()
        pubkey = json_object['pubkey']
        firstname = json_object['firstname']
        lastname = json_object['lastname']
        phonenr = json_object['phonenr']
        email = json_object['email']

        new_person = Person(pubkey=pubkey, firstname=firstname, lastname=lastname, phonenr=phonenr, email=email,
                                date_created=datetime.now())
        try:
            db.session.add(new_person)
            db.session.commit()

            response = make_response(render_template('main.html',person=new_person))
            session['pk'] = pubkey

            return response

        except Exception as ex:
            raise ex

    elif request.method == 'GET':
        return render_template('register.html')

    else:
        people = Person.query.all()
        return render_template('main.html', people=people)

if __name__ == "__main__":
    app.config.update(
        # Set the secret key to a sufficiently random value
        SECRET_KEY=os.urandom(24),
        # Set the session cookie to be secure
        SESSION_COOKIE_SECURE=True,
        # Set the session cookie for our app to a unique name
        SESSION_COOKIE_NAME='ChainMeUP-WebSession',
        # Set CSRF tokens to be valid for the duration of the session. This assumes you’re using WTF-CSRF protection
        WTF_CSRF_TIME_LIMIT=None
    )
    app.run(host='0.0.0.0',debug=True, port=8000)
