import os
from flask import Flask, render_template, request, make_response, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import CardReader

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
        reader = CardReader.initReading()

        pubkey = CardReader.read_public_key(reader,1)

        if pubkey is not None:
            person = Person.query.get(pubkey.hex())
        else:
            return "No or invalid pub!"

        if person is not None:
            if CardReader.auth(reader, pubkey):

                response = make_response(render_template('main.html', person=person))
                session['pk'] = pubkey

                return response
            else:
                return "Error, wrong card on key reader"
        else:
            return "PubKey not registered"


@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        reader = CardReader.initReading()
        if reader is None:
            return "No reader connected!"
        if not CardReader.initCard(reader):
            return "Card not writeable or a user is already registered with this card!"

        pubkey = CardReader.read_public_key(reader, 1)

        if pubkey is None:
            return "No pubkey!"
        else:
            pubkey = pubkey.hex()
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            phonenr = request.form['phonenr']
            email = request.form['email']

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
    app.run(debug=True)
