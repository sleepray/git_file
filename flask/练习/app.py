import os
from flask_migrate import Migrate
from flask import Flask,render_template,session, redirect, url_for,flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

#若使用SQLite数据库，设置路径
#basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__) #实例化
app.config['SECRET_KEY'] = 'hard to guess string' #配置密匙，用来使用Flask-WTF扩展

bootstrap = Bootstrap(app)#实例化Bootstrap扩展

moment = Moment(app) #实例化Flask-Moment,作用为时间戳

# 使用 PostgreSQL
# 用户名为Relam,密码为Relam887,数据库服务器为localhost,数据库名为RCT(有BUG，还未解决)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Realm887@localhost/RCT'
# SQLite数据库
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
#MySQL 数据库 用户名为root, 密码为iloveyou88 服务器为localhost:3306(3306为端口) 数据库名称为test(MySQ需要自己建立数据库)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:iloveyou88@localhost:3306/test?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit(): #第一次访问为get请求，为False,第二次访问为post请求，为True
        user = User.query.filter_by(username=form.name.data).first()#查找数据库中有没有这个名字
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user) #将名字添加进数据库
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    # 在 GET 请求里，将保存在 Session 中的用户输入内容，传递给模板
    return render_template('index_1.html', form=form, name=session.get('name'), known = session.get('known',False),
                           current_time=datetime.utcnow())

#设置后不用再手动Import
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)