from flask import g, jsonify
from ..models import User
from .import api
from .errors import unauthorized, forbidden
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth() #初始化http认证

@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '': #email或token为空则返回False
        return False
    if password == '':#当password为空时使用token验证，否则使用email验证
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email = email_or_token).first()
    if not user: #用户不存在返回False
        return False
    g.current_user = user #g是上下文变量
    g.token_used = False
    return user.verify_password(password) #调用User模型的密码检测函数

#错误响应
@auth.error_handler
def auth_error():
    return unauthorized('无效的凭证')

@api.before_request #调用api蓝图前进行身份验证
@auth.login_required
def before_request():#如果是普通用户且没有确认账户返回
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('未经确认的用户')

@api.route('/tokens/', methods=['POST'])
def get_token():
    if g.current_user.is_anonymous or g.token_used:#如果是匿名用户或者token_used未授权用户不能登录
        return unauthorized('无效的凭据')
    return jsonify({'token':g.current_user.generate_auth_token(
        expiration = 3600), 'expiration': 3600}) #返回json格式的token,有效期1小时