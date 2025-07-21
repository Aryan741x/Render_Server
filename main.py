from flask import Flask
app = Flask(__name__)
@app.route("/")
def hello():
    return "Hello from Render!"
# Do NOT add app.run()
