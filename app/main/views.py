#coding:utf-8
from flask_sqlalchemy import get_debug_queries
from datetime import datetime
from flask import render_template, session, redirect, url_for,current_app, flash,request,abort,make_response
from . import main
from .forms import NameForm,EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from .. import db
from flask_login import login_user,login_required, logout_user,current_user
from ..models import User,Role,Permission,AnonymousUser,Post,Comment,Category, Like
from ..decoratots import admin_required,permission_required
from ..email import send_email

#带有博文的首页
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    #如果提交的数据通过验证就新增一个
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        #current_user 是个当前线程代理对象,需要通过_get_current_object()方法获取到真实的 User 模型对象，再传给数据库
        post = Post(title = form.title.data, category = Category.query.get(form.category.data),
                    body=form.body.data,author = current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index')) #重定向到当前蓝图下的 index()，可以简写为 .index
    page = request.args.get('page', 1, type=int) #页数渲染从reuqest.args中获取，默认为1，参数为整数
    show_followed = False
    if current_user.is_authenticated:#根据cookie值是否非空决定显示主页文章
        show_followed = bool(request.cookies.get('show_followed', ''))
        posts_amount = (current_user.followed_posts.order_by(Post.timestamp.desc()).count(),
                        Post.query.order_by(Post.timestamp.desc()).count())
    else:
        posts_amount = Post.query.order_by(Post.timestamp.desc()).count()#如果是匿名用户
    if show_followed:#非空，调用用户关注人的文章
        query = current_user.followed_posts
    else:
        query = Post.query#为空，调用所有人的文章
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    #第一个参数为当前页数，第二个参数是每页显示多少记录，第三个参数表示没有记录的分页是否引发404错误
    posts = pagination.items#按时间的倒序将当前页面记录的博文取出
    return render_template('index.html', form=form, posts=posts,show_followed=show_followed,redir='.index',
                           pagination=pagination,posts_amount=posts_amount,current_time=datetime.utcnow(),page=page)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    #如果用户不存在，返回404错误
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts, current_time=datetime.utcnow(), redir='.user')

#将每个分类的博文全部调取
@main.route('/category/<int:id>')#自动分配id，每个id为一类
def category(id):
    category = Category.query.get_or_404(id)
    category_1 = Category.query.get_or_404(1)
    category_2 = Category.query.get_or_404(2)
    category_3 = Category.query.get_or_404(3)
    page = request.args.get('page', 1, type=int)
    if page <= 0:
        page = (category.posts.count() - 1) / \
                current_app.config['FLASKY_POSTS_PER_PAGE'] + 1
    pagination = category.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page = current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)#根据时间倒序
    posts = pagination.items
    return render_template('category.html', category = category,current_time=datetime.utcnow(),
                           category_1=category_1,category_2=category_2,category_3=category_3,
                            posts = posts, pagination = pagination, redir = '.category', page = page)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():# 第一次访问为get请求，为False,第二次访问为post请求，为True
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('你的资料已经修改成功')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form, current_time=datetime.utcnow())

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id) #id不正确时返回404错误(非管理员访问时返回)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('用户资料已更新')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user, current_time=datetime.utcnow())

#文章固定链接
@main.route('/post/<int:id>',methods=['GET', 'POST'])
def post(id):#根据博文d更改posts，一个id只循环一次，所以只有一个博文渲染出来
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body = form.body.data,
                          post = post,author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('评论发布成功')
        return redirect(url_for('.post', id=post.id, page= -1))
    page = request.args.get('page', 1, type=int)
    if page == -1: #提交评论后请求评论最后一页
        page = (post.comments.count() - 1) // \
                current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1#评论数除每页显示评论数,且为整除
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post],comments=comments,form=form,
                           pagination=pagination,current_time=datetime.utcnow(),redir='.post')

@main.route('/post/delete/<int:id>')
@login_required
def post_delete(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    post.delete()
    flash('文章已删除')
    return redirect(url_for('.index'))

@main.route('/post/like/<int:id>/<redir>')
@login_required
def post_like(id, redir):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1 ,type = int)
    if current_user.is_like_post(post):#如果点过赞，就取消
        like = Like.query.filter_by(post_id = post.id).first()
        db.session.delete(like)
    else:#如果没点赞就加入
        like = Like(post = post, author = current_user._get_current_object())
        db.session.add(like)
    db.session.commit()
    redir_frament = ''.join(('post', str(post.id)))
    if redir == '.index':
        return redirect(url_for('.index', page=page, _anchor=redir_frament))
    elif redir == '.post':
        return redirect(url_for('.post', id = post.id))
    elif redir == '.category':
        return redirect(url_for('.category', page=page, id=post.category.id, _anchor=redir_frament))
    elif redir == '.user':
        return redirect(url_for('.user', username = current_user._get_current_object().username, _anchor=redirect_frament))

@main.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):#根据博文id找出博文
    post = Post.query.get_or_404(id) #当博文里没有这个id时报错
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.category = Category.query.get(form.category.data)
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('博文修改成功')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    form.category.data = post.category_id
    form.body.data = post.body
    return render_template('edit_post.html', form=form, current_time=datetime.utcnow())

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户未注册')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('你已经关注过该用户了')
        return redirect(url_for('.user', username=username,current_time=datetime.utcnow()))
    current_user.unfollow(user)
    db.session.commit()
    flash('你已经取消关注 %s.' % username)
    return redirect(url_for('.user', username=username,current_time=datetime.utcnow()))

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户未注册')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('你已经关注过该用户了')
        return redirect(url_for('.user', username=username,current_time=datetime.utcnow()))
    current_user.follow(user)
    db.session.commit()
    flash('你已成功关注 %s.' % username)
    return redirect(url_for('.user', username=username,current_time=datetime.utcnow()))

@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户未注册')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    #调用该用户关注的人
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows =[{'user': item.followed, 'timestamp': item.timestamp}
              for item in pagination.items]
    return render_template('followers.html', user=user, title='关注的',
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows,current_time=datetime.utcnow())

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户未注册')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1 , type=int)
    #调用关注该用户的人
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="的关注者",
                           endpoint='.followers', pagination=pagination,
                           follows=follows,current_time=datetime.utcnow())

@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60) #30天
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))#make_response设置相应对象
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)#第一个参数为cookie名称，第二个为值
    return resp

#审核评论,读取数据库中每页评论
@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination,current_time=datetime.utcnow())

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing: #仅当再测试环境中可用
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')#werkzeug关闭函数
    if not shutdown:
        abort(500)
    shutdown()
    return '关闭...'

#数据库记录
@main.after_app_request
def after_request(response):
    for query in get_debug_queries(): #get_debug_queries() 方法会返回本次请求中的所有查询的列表
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                '慢查询: %s\n参数: %s\n时长: %fs\n上下文: %s\n' %
                (query.statement, query.parameters, query.duration, query.context)
            )
    return response
