from flask import Flask, jsonify, request
from models.lever import Lever
from states import LeverEvent
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

lever = Lever()

tick_thread = None
tick_running = False

def tick_loop():
    global tick_running
    logger.info("Tick loop started")
    
    while tick_running:
        try:
            lever.tick_update()
            time.sleep(lever.tick)
        except Exception as e:
            logger.error(f"Tick error: {e}")
            time.sleep(1)

def start_tick_thread():
    global tick_thread, tick_running
    if tick_thread is None or not tick_thread.is_alive():
        tick_running = True
        tick_thread = threading.Thread(target=tick_loop, daemon=True)
        tick_thread.start()
        logger.info("Tick thread started")

def stop_tick_thread():
    global tick_running
    tick_running = False
    logger.info("Tick thread stopped")

start_tick_thread()

@app.route('/api/lever/status', methods=['GET'])
def get_status():
    try:
        state = lever.get_state()
        message = lever.get_status_message()
        
        return jsonify({
            "success": True,
            "data": state,
            "message": message
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/pull-up', methods=['POST'])
def pull_up():
    try:
        result = lever.pull_up()
        return jsonify({
            "success": True,
            "message": result,
            "data": lever.get_state()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/pull-down', methods=['POST'])
def pull_down():
    try:
        result = lever.pull_down()
        return jsonify({
            "success": True,
            "message": result,
            "data": lever.get_state()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/pause', methods=['POST'])
def pause():
    try:
        result = lever.pause()
        return jsonify({
            "success": True,
            "message": result,
            "data": lever.get_state()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/resume', methods=['POST'])
def resume():
    try:
        result = lever.resume()
        return jsonify({
            "success": True,
            "message": result,
            "data": lever.get_state()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/stop', methods=['POST'])
def stop():
    try:
        result = lever.stop()
        return jsonify({
            "success": True,
            "message": result,
            "data": lever.get_state()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/set-heat', methods=['POST'])
def set_heat():
    try:
        data = request.get_json()
        heat = data.get('heat')
        
        if heat is None:
            return jsonify({"success": False, "error": "Heat required"}), 400
        
        lever.heat = float(heat)
        lever.save_state()
        
        return jsonify({
            "success": True,
            "message": f"Heat set to {heat}",
            "data": lever.get_state()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/reset', methods=['POST'])
def reset():
    try:
        from states import LeverState
        
        lever.position = 50
        lever.heat = 0
        lever.sealing_progress = 0
        lever.fsm.current_state = LeverState.STOPPED
        lever.save_state()
        lever.log("RESET")
        
        return jsonify({
            "success": True,
            "message": "Reset complete",
            "data": lever.get_state()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/lever/history', methods=['GET'])
def get_history():
    try:
        from db import get_connection
        
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        
        limit = request.args.get('limit', 50, type=int)
        cur.execute("SELECT * FROM lever_history ORDER BY timestamp DESC LIMIT %s", (limit,))
        history = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": history,
            "count": len(history)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/system/health', methods=['GET'])
def health():
    return jsonify({
        "success": True,
        "message": "FSM API running",
        "tick_running": tick_running,
        "current_state": lever.fsm.get_state().value
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)







