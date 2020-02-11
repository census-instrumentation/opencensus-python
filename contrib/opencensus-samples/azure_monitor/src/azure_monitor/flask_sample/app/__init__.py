from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from opencensus.ext.flask.flask_middleware import FlaskMiddleware

app = Flask(__name__)
app.config.from_object(Config)
middleware = FlaskMiddleware(app)
db = SQLAlchemy(app)

from app import routes

if __name__ == '__main__':
    app.run(host='localhost', port=5000, threaded=True)
