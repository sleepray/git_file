#coding:utf-8
from email import charset
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message,Mail
from . import mail


#添加utf-8编码
charset.add_charset('utf-8', charset.SHORTEST, charset.BASE64, 'utf-8')

def send_async_email(app,msg):
    with app.app_context():  #创建程序上下文
        mail.send(msg)
        print('发送成功')

#参数为：收件人地址、主题、渲染邮件正文的模板、关键字参数
def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object() #实例化(暂时不知道为何这样实例化)
    print(app.config['MAIL_USERNAME'],"发送给", to , app.config['MAIL_PASSWORD'])
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to],charset='utf-8')#utf-8编码
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg]) #后台线程
    thr.start()
    return thr