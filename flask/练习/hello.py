from flask import Flask,request,make_response,redirect,abort

app = Flask(__name__) #实例化

#静态路由
#@app.route('/')
#def index():
    #response = make_response('<h1>This document carries a cookie!</h1>')
    #response.set_cookie('answer', '42') #添加一个cookie
    #return response

#动态路由
@app.route('/user/<name>')
def user(name):
    return '<h1>Hello, {}!</h1>'.format(name)

#重定向
@app.route('/')
def index():
    return redirect('https://www.bilibili.com') #重定向的网址

#使用abort()处理错误
@app.route('/user/<id>')
def get_user(id):
    user = load_user(id)
    if user is None:
        abort(404)
        return '<h1>Hello, {}!'.format(user.name)