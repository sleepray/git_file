from flask import Flask,render_template,session, redirect, url_for,flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime

'''
表单提交
'''

app = Flask(__name__) #实例化
app.config['SECRET_KEY'] = 'hard to guess string' #配置密匙，用来使用Flask-WTF扩展

bootstrap = Bootstrap(app)#实例化Bootstrap扩展

moment = Moment(app) #实例化Flask-Moment,作用为时间戳

class NameForm(FlaskForm):
    name = StringField('你叫什么名字', validators=[DataRequired()])
    #validators指定验证函数，DataRequired()确保提交的字段不为空
    submit = SubmitField('提交')

@app.route('/', methods=['GET', 'POST']) #处理get和post请求
def index():
    form = NameForm() #保存了表单提交的信息
    # 表单post通过了验证后返回True,用户第一次通过浏览器导航到该 URL 时,采用get方法，返回False
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            #当之前的名字和现在名字不一样时，设置消息
            flash('哟，改名字啦！')
        # 在 POST 请求里，将用户输入的内容保存到 Session 中
        session['name'] = form.name.data
        return redirect(url_for('index')) #重定向为index函数
    # 在 GET 请求里，将保存在 Session 中的用户输入内容，传递给模板
    return render_template('index_1.html', form=form, name=session.get('name'),current_time=datetime.utcnow())

@app.errorhandler(404)  #404错误处理
def page_not_found(e):
    return render_template('404.html',
                           current_time=datetime.utcnow()), 404