from flask import Flask, jsonify
from models.lever import Lever

app = Flask(__name__)
lever = Lever()

@app.route("/lever/pull/up", methods=["POST"])
def pull_up():
    return jsonify({"message": lever.pull_up()})

@app.route("/lever/pull/down", methods=["POST"])
def pull_down():
    return jsonify({"message": lever.pull_down()})

@app.route("/lever/seal", methods=["POST"])
def seal():
    return jsonify({"message": lever.seal()})

@app.route("/lever/pause", methods=["POST"])
def pause():
    return jsonify({"message": lever.pause()})

@app.route("/lever/resume", methods=["POST"])
def resume():
    return jsonify({"message": lever.resume()})

@app.route("/lever/state", methods=["GET"])
def state():
    return jsonify(lever.state())

if __name__ == "__main__":
    app.run(debug=True)



