# coding:utf-8
'''
应用程序包构造器
'''
from flask_pagedown import PageDown
from flask import Flask,render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager

pagedown = PageDown()
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager() #flask-login初始化
login_manager.login_view = 'auth.login' #设置登录视图，使用蓝图设置视图

def create_app(config_name): #初始化
    app = Flask(__name__)
    app.config.from_object(config[config_name]) # 获取相应的配置类
    config[config_name].init_app(app) # 将配置传入运行config的init_app函数进行初始化
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    # 将路由和自定义错误页面放这
    from .main import main as main_blueprint #导入main蓝图
    app.register_blueprint(main_blueprint) # 注册蓝图


    from .auth  import auth as auth_blueprint #导入蓝图 auth
    #设置了url_prefix参数后，蓝图中的路由都会自动加上参数前缀
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api import api as api_blueprint #导入api蓝图
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app