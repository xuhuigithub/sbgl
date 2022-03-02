import imp
import os
import atexit
from flask import Flask
from database import init_db
from auth import auth as auth_bl
from open import open as open_bl
from api import api
from database import db_session
import tempfile
# from flask_socketio import SocketIO

app = Flask(__name__)
api.init_app(app)

if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    # The app is not in debug mode or we are in the reloaded process
    init_db()
    # pass

# 登录接口
app.register_blueprint(auth_bl)
app.register_blueprint(open_bl)
# 确保jsonify 返回编码后的文字
app.config['JSON_AS_ASCII'] = False

@app.teardown_request
def clean_session(exc):
    db_session.remove()

app.config["LOG_DIR"] = tempfile.mkdtemp()

def clean_log_dir():
    print("清理日志..." + app.config["LOG_DIR"])
    os.rmdir(app.config["LOG_DIR"])
# socketio = SocketIO(app)


if __name__ == '__main__':
    atexit.register(clean_log_dir)

    app.run(host="0.0.0.0", port=5000, debug=False)
