# coding:utf-8
import os
from threading import Thread
from flask_mail import Message,Mail
from flask_migrate import Migrate
from flask import Flask,render_template,session, redirect, url_for,flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from email import charset
#添加utf-8编码
charset.add_charset('utf-8', charset.SHORTEST, charset.BASE64, 'utf-8')

app = Flask(__name__) #实例化


app.config['SECRET_KEY'] = 'hard to guess string' #配置密匙，用来使用Flask-WTF扩展

app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = '302559651@qq.com'
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True
#将账户名和密码放在环境变量里读取，但我的环境变量好像出问题了，不能设置，所以直接写入
# QQ邮箱授权码：kokczdimuxyobjdg
app.config['MAIL_USERNAME'] = '302559651' #账号
app.config['MAIL_PASSWORD'] = 'kokczdimuxyobjdg' #授权码
app.config['FLASKY_ADMIN'] = '1023499684@qq.com'#收件人邮件
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:iloveyou88@localhost:3306/test?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)#实例化Bootstrap扩展
mail = Mail(app) #初始化
moment = Moment(app) #实例化Flask-Moment,作用为时间戳
db = SQLAlchemy(app)
migrate = Migrate(app,db) # 初始化（数据迁徙）

class Role(db.Model):
    '''角色模型'''
    __tablename__ = 'roles' #__tablename__ 定义了该模型在数据库中的表名
    id = db.Column(db.Integer, primary_key=True) #数据类型为常规整数，作为表的主键
    name = db.Column(db.String(64), unique=True) #长字符串64位，该字段的值是唯一的
    users = db.relationship('User', backref='role')
    #db.relationship 用于定义关系，仅在Python中可见   backref 是反向引用

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    '''用户模型'''
    __tablenmae__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # 长字符串64位，该字段的值是唯一的，并为该字段创建索引
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    #db.ForeignKey 用于定义外键，引用的字段在数据库中呈现

    def __repr__(self):
        return '<User %r>' % self.username

class NameForm(FlaskForm):
    name = StringField('你叫什么名字', validators=[DataRequired()])
    #validators指定验证函数，DataRequired()确保提交的字段不为空
    submit = SubmitField('提交')

def send_async_email(app,msg):
    with app.app_context():  #创建程序上下文
        mail.send(msg)

#参数为：收件人地址、主题、渲染邮件正文的模板、关键字参数
def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to],charset='utf-8')#utf-8编码
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg]) #后台线程
    thr.start()
    return thr

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():  # 第一次访问为get请求，为False,第二次访问为post请求，为True
        user = User.query.filter_by(username=form.name.data).first()  # 查找数据库中有没有这个名字
        #如果数据库中没有这个名字就发送一封邮箱
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)  # 将名字添加进数据库
            db.session.commit()
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index_1.html', form=form, name=session.get('name'), known = session.get('known',False),
                           current_time=datetime.utcnow())
if __name__ == "__main__":
    app.run()