import os

from app import app

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
app.run(port=9999,debug=True)