#coding:utf-8
'''
登陆表单
'''
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..models import User

class LoginForm(FlaskForm):
    #PasswordField()表示属性为type='password'的<input>元素，BooleanField()表示复选框
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('让我保持登录')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64),
                                             Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1,64),
        #Regexp()使用正则表达式
        Regexp('[\u4e00-\u9fa5_A-Za-z0-9_.]*$', 0,
               '用户名只能包含中文,字母、数字、点或下划线')])
    password = PasswordField('密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码不一致')])
        #EqualTo()验证两次密码正确
    password2 = PasswordField('重复密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first(): #如果数据库中存在，抛出异常
            raise ValidationError('Email已经被注册了')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经被注册了')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('老密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码不一致')
    ])
    password2 = PasswordField('重复密码', validators=[DataRequired()])
    submit = SubmitField('更改密码')

    def validate_password(self, field):
        if User.query.filter_by(password=field.data.lower()).first():
            raise ValidationError('新密码不能与老密码相同')

class ChangeEmailForm(FlaskForm):
    email = StringField('新的邮箱', validators=[DataRequired(), Length(1,64),
                                            Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('更改邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('该邮箱已被注册')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                          Email()])
    sumbit = SubmitField('重设密码')

class PasswordResetForm(FlaskForm):
    email = StringField('邮箱', validators = [DataRequired(), Length(1, 64),
                                            Email()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码不一致')
    ])
    password2 = PasswordField('重复密码', validators=[DataRequired()])
    submit = SubmitField('重设密码')

    def validate_email(self, field):
        if User.query.filter_by(email = field.data).first() is None:
            raise ValidationError('未知的邮箱')

