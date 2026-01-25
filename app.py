from flask import Flask, jsonify
from models.lever import Lever

app = Flask(__name__)

lever = Lever()

@app.route("/lever/pull/up", methods=["POST"])
def pull_up():
    result = lever.pull_up()
    return jsonify(result), 200


@app.route("/lever/pull/down", methods=["POST"])
def pull_down():
    result = lever.pull_down()
    return jsonify(result), 200


@app.route("/lever/pause", methods=["POST"])
def pause():
    result = lever.pause()
    return jsonify(result), 200


@app.route("/lever/resume", methods=["POST"])
def resume():
    result = lever.resume()
    return jsonify(result), 200


@app.route("/lever/state", methods=["GET"])
def get_state():
    state = lever.get_state()
    return jsonify(state), 200


if __name__ == "__main__":
    app.run(debug=True)




