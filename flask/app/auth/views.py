#coding:utf-8
'''
用户登录路由视图
'''
from ..email import send_email
from datetime import datetime
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user,login_required, logout_user,current_user
from . import auth
from ..models import User
from .. import db
from .forms import LoginForm, RegistrationForm,ChangePasswordForm,\
    PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm

@auth.route('/login', methods=['GET', 'POST'])
#第一次访问先调用get请求的表单，第二次再进行post请求，会有两次调用函数
def login():
    form = LoginForm()
    if form.validate_on_submit():# 第一次访问为get请求，为False,第二次访问为post请求，为True
        user = User.query.filter_by(email=form.email.data).first()#查找数据库中有没有这个邮箱用户
        if user is not None and user.verify_password(form.password.data):#如果用户存在且密码正确
            #login_user()将当前已登录用户记录到Session中，第一个参数为用户，第二个参数为是否
            #记住该用户，如果为True，即使关闭浏览器也能保持登录
            login_user(user, form.remember_me.data)
            next = request.args.get('next') #post请求会重定向，获取请求前的URL
            if next is None or not next.startswith('/'):#startswith检查是否以/开头
                next = url_for('main.index')
            return redirect(next)
        flash('错误的用户名或密码') #登陆失败闪现消息
    return render_template('auth/login.html',form=form,current_time=datetime.utcnow())

@auth.route('/logout')
@login_required
def logout():
    logout_user() #将用户在Session进行删除
    flash('你已成功退出')
    return redirect(url_for('main.index'))

@auth.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user) # 生成令牌前就需要将数据保存到数据库，不然不能获取到用户id
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, '确认你的账户',
                   'auth/email/confirm', user=user, token=token)#注意文件格式编码应为utf-8，直接用记事本创建没有编码
        flash('一封确认邮箱已经发送到你的邮箱')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form,current_time=datetime.utcnow())

@auth.route('/confirm/<token>')
@login_required #用户需要先进行登录后才能查看
def confirm(token):
    if current_user.confirmed:
        flash('你的账号已经注册')
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('你的账号确认成功,谢谢')
    else:
        flash('确认链接无效或已过期')
    return redirect(url_for('main.index'))

#在auth请求前，全局
@auth.before_app_request #使用auth.before_app_request过滤登录未确认用户用户，全局可用
def before_request():
    if current_user.is_authenticated:
        current_user.ping() #如果用户登录凭证有效，调用用户最后访问时间函数
        if not current_user.confirmed \
            and request.blueprint != 'auth' and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html',current_time=datetime.utcnow())

@auth.route('/confirm')#路由保护
@login_required #只有通过身份验证的用户才能再次请求
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email,'确认你的账号',
               'auth/email/confirm', user=current_user, token=token)
    flash('一封新的确认邮件已经发送到你的邮箱')
    return redirect(url_for('main.index'))

@auth.route('/change-passsword', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('你的密码已经更改')
            return redirect(url_for('main.index'))
        else:
            flash('老密码错误')
    return render_template("auth/change_password.html", form=form, current_time=datetime.utcnow())

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous: #如果是普通用户
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '更改你的密码',
                       'auth/email/reset_password',
                       user=user, token=token)
        flash('重置密码邮件发送到了你的邮箱')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form, current_time=datetime.utcnow())

@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('你的密码已经更新')
            return redirect(url_for('auth.login'))
        else:
            flash('不是指定更改邮箱地址，请重新更改')
    return render_template('auth/reset_password.html', form=form, current_time=datetime.utcnow())

@auth.route('/change-email', methods = ['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, '确认你的邮箱地址',
                       'auth/email/change_email',
                       user = current_user, token = token)
            flash('重置邮箱地址邮件已发送到你邮箱')
            return redirect(url_for('main.index'))
        else:
            flash('邮箱或者密码错误')
    return render_template('auth/change_email.html', form = form, current_time=datetime.utcnow())

@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('你的邮箱已经更新')
    else:
        flash('非法请求')
    return redirect(url_for('main.index'))



