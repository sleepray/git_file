#coding:utf-8
'''
检测用户权限的装饰器
'''
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission

def permission_required(permission):
    def decorator(f): #f是装饰的函数,permission是带的参数
        @wraps(f)#将原函数对象的指定属性复制给包装函数对象
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403) #如果用户不具备权限，返回403错误
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMIN)(f)