from flask import request
from . import open
from api.user import user as user_model
from auth import basic_auth
from dao.user import UserDAO
from dao import DataBaseCommitException
from utils import raise_error_api
from flask_restplus import marshal_with
from api import wrapresp

DAO = UserDAO()

@open.route('/api/updateME', methods=['PUT'])
@basic_auth.login_required
@raise_error_api(captures=(DataBaseCommitException,), err_msg="数据查询异常")
@wrapresp
@marshal_with(user_model)
def update_me():
    return DAO.update(request.authorization.username, request.json)
