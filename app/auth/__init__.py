from flask import Blueprint

auth = Blueprint('auth', __name__) #创建用户认证蓝图

from .import views