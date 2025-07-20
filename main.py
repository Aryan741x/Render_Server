import os
from flask import Flask
from flask_cors import CORS
from routes import routes

app = Flask(__name__)
CORS(app, origins="*")
app.register_blueprint(routes, url_prefix="")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
