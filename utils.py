from functools import wraps
from flask import jsonify
from collections import OrderedDict
import signal
from contextlib import contextmanager
import traceback
import uuid

DEBUG_RAISE = True

def raise_error_api(captures, err_msg):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            try:
                return view_func(*args, **kwargs)
            except captures as e:
                if DEBUG_RAISE:
                    if e.__context__:
                        # 捕捉异常并返回
                        msg = f"{err_msg}: {str(e)} -> {str(e.__context__)}"
                    else:
                        msg = f"{err_msg}: {str(e)}"
                    traceback.print_exc()
                else:
                    msg = f"{err_msg}"
                return jsonify(
                OrderedDict(
                        status=1,
                        msg=msg,
                        data=dict()
                    )
                )
        return wrapper
    return decorator

def generate_uuid():
    return str(uuid.uuid4())