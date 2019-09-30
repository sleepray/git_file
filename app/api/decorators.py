from functools import wraps
from flask import g
from .errors import forbidden

def permission_required(permission):
    def decorator(f):#f是装饰的函数,permission是带的参数
        @wraps(f)#将原函数对象的指定属性复制给包装函数对象
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('权限不足')
            return f(*args, **kwargs)
        return decorated_function
    return decorator