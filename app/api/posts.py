from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Post, Permission
from . import api
from .decorators import permission_required
from .errors import forbidden

#调用全部的博文
@api.route('/posts/')
def get_posts(): #按照时间顺序调用所有文章
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False) #每页全部博文
    posts = pagination.items
    prev = None
    if pagination.has_prev: #如果有上一页返回上一页的URL
        prev = url_for('api.get_posts', page=page-1, _external=True)#_external=True返回绝对地址
    next = None
    if pagination.has_next: #如果有下一页返回下一页的URL
        next = url_for('api.get_posts', page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev_url': prev,
        'next_url': next,
        'count': pagination.total
    })


#调用某个博文
@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())

#创建新的博文
@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_post():
    post = Post.from_json(request.json) #从提交的json数据写入博文
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    #写入数据库后返回201代码，并把Location设为刚创建的URL
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id, _external=True)}

#api修改博文
@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('权限不足')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())