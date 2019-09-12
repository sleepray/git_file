from flask import Flask,render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime


'''
Jinja2渲染模板
'''
app = Flask(__name__) #实例化

bootstrap = Bootstrap(app)#实例化Bootstrap扩展

moment = Moment(app) #实例化Flask-Moment,作用为时间戳

@app.route('/')
def index():
    return render_template('index.html',
                            current_time=datetime.utcnow())

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name,
                           current_time=datetime.utcnow())

#使用errorhandler装饰器自定义错误处理函数
@app.errorhandler(404)  #404错误处理
def page_not_found(e):
    return render_template('404.html',
                           current_time=datetime.utcnow()), 404

@app.errorhandler(500)  #500错误处理
def internal_server_error(e):
    return render_template('500.html',
                           current_time=datetime.utcnow()),500

