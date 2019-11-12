from flask import Flask, render_template, url_for, request, redirect, make_response, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from ChainMeUp.CardReader import CardReader
import blocksec2go
from hashlib import sha256
import json
import requests


CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
posts = []

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

cardReader = CardReader()

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

    if request.method == "GET":
        return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        person = Person.query.all()
        return render_template('main.html', people=person)


@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        #id = db.Column(autoincrement=True, primary_key=True)

        if not cardReader.initCard():
            return "Card not writeable"

        pubkey = cardReader.get_Pub_hex()

        if pubkey is None:
            return "error pubkey"
        else:
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            phonenr = request.form['phonenr']
            email = request.form['email']

            new_person = Person(pubkey=pubkey, firstname=firstname, lastname=lastname, phonenr=phonenr, email=email,
                                date_created=datetime.now())
        try:
            db.session.add(new_person)
            db.session.commit()

            response = make_response(render_template('main.html'))
            response.set_cookie('pk', pubkey)

            return response

        except Exception as ex:
            raise ex

    elif request.method == 'GET':
        return render_template('register.html')

    else:
        people = Person.query.all()
        return render_template('main.html', people=people)


''''     
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
'''

if __name__ == "__main__":
    app.run(debug=True)
