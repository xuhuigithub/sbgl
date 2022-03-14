import datetime
import imp
import os
import atexit
import typing
from flask import Flask
from sqlalchemy import true
from database import init_db
from auth import auth as auth_bl
from open import open as open_bl
from api import api
from database import db_session
import tempfile
# from flask_socketio import SocketIO
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import models
import socket

app = Flask(__name__)
api.init_app(app)

if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    # The app is not in debug mode or we are in the reloaded process
    # init_db()
    pass

# 登录接口
app.register_blueprint(auth_bl)
app.register_blueprint(open_bl)
# 确保jsonify 返回编码后的文字
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

@app.teardown_request
def clean_session(exc):
    db_session.remove()

app.config["LOG_DIR"] = tempfile.mkdtemp()

def clean_log_dir():
    print("清理日志..." + app.config["LOG_DIR"])
    os.rmdir(app.config["LOG_DIR"])
# socketio = SocketIO(app)

admin = Admin(app, name='microblog', template_mode='bootstrap3')
admin.add_view(ModelView(models.PlayRole, db_session))

from flask_apscheduler import APScheduler

app.config['SCHEDULER_API_ENABLED '] = true
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# @scheduler.task('interval', id='do_job_1', seconds=30, misfire_grace_time=900)
# def job1():
#     with scheduler.app.app_context():
#         from models import Assets
#         assets: typing.List[Assets] = Assets.query.all()
#         for i in assets:
#             try:
#                 with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                     s.settimeout(3)
#                     s.connect((i.ip, 22))
#                 ssh_ok = True
#             except socket.error:
#                 ssh_ok = False
            
#             if ssh_ok:
#                 i.last_seen = datetime.datetime.now()
#                 db_session.add(i)
#                 db_session.commit()
        
from database import Base, engine
Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    atexit.register(clean_log_dir)

    app.run(host="0.0.0.0", port=5000, debug=False)
