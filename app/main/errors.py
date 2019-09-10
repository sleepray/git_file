#coding:utf-8
from flask import render_template,request,jsonify
from .import main
from datetime import datetime

#蓝图中定义应用级别的错误处理，需要使用 蓝图.app_errorhandler 装饰器
@main.app_errorhandler(404)
@main.app_errorhandler(404)
def page_not_found(e):#如果请求头是json且不包含html返回json格式,否则返回html格式
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html',current_time=datetime.utcnow()), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html',current_time=datetime.utcnow()), 500

@main.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html', current_time=datetime.utcnow()), 403