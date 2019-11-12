from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashlib import sha256
import json
import requests

#from app import app

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
posts = []

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class Person(db.Model):
    pubkey = db.Column(db.String(256), primary_key=True)
    lastname = db.Column(db.String(20), nullable=False)
    firstname = db.Column(db.String(20), nullable=False)
    phonenr = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return '<People %r>' % self.pubkey


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        # id = db.Column(db.INTEGER, primary_key=True)
        pubkey = request.form['pubkey']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        phonenr = request.form['phonenr']
        email = request.form['email']

        new_person = Person(pubkey=pubkey, firstname=firstname, lastname=lastname, phonenr=phonenr, email=email,
                            date_created=datetime.now())

        try:
            db.session.add(new_person)
            db.session.commit()
            return redirect('/')
        except Exception as ex:
            raise ex
    else:
        people = Person.query.all()

        return render_template('index.html', people=people)

'''
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
