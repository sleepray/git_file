#coding:utf-8
import hashlib,bleach
from markdown import markdown
from datetime import datetime
from . import db,login_manager
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from app.exceptions import ValidationError


class Permission:
    '''
    权限常量
    '''
    FOLLOW = 1 #关注用户
    COMMENT = 2 #对文章进行评论
    WRITE = 4  #写文章
    MODERATE = 8 #审核评论
    ADMIN = 16 #管理员操作

#关联表
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Role(db.Model):
    '''角色模型'''
    __tablename__ = 'roles' #__tablename__ 定义了该模型在数据库中的表名
    id = db.Column(db.Integer, primary_key=True) #数据类型为常规整数，作为表的主键
    name = db.Column(db.String(64), unique=True) #长字符串64位，该字段的值是唯一的
    users = db.relationship('User', backref='role', lazy='dynamic')
    permissions = db.Column(db.Integer)
    default = db.Column(db.Boolean, default=False, index=True) #只为新注册的用户设为index=True
    #db.relationship 用于定义关系，仅在Python中可见   backref 是反向引用,可以比作为建立与User的快捷方式
    #lazy='dynamic'返回一个可进行额外操作的query 对象
    #可以定义permissions = db.Column(db.Integer, nullable=False, default=0),便不必定义
    #Role模型的__init__()方法
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():  # 静态方法
        #一共三个权限，每个权限会将对应的权限值相加
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()  # 查找是否有同名角色，没有就创建
            if role is None:
                role = Role(name=r)
            #重置权限
            role.reset_permissions()
            for perm in roles[r]:
                #权限重新一个个加入进去
                role.add_permission(perm)#每个相应权限是将所有值相加，比如管理员就是1+2+4+8+16=31
            #将默认用户写进数据库
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm #先读取用户的权限值与perm进行位运算，
                                                # 再判断与perm值是否相等

    def __repr__(self):
        return '<Role %r>' % self.name

class User(UserMixin,db.Model):
    '''用户模型'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), unique = True, index = True)
    # 长字符串64位，该字段的值是唯一的，并为该字段创建索引
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    #db.ForeignKey 用于定义外键，引用的字段在数据库中呈现
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique = True, index = True)#用email做用户名
    confirmed = db.Column(db.Boolean, default = False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())#text与string区别是text没有长度限制
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)#注册时间
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)#最后访问时间
    avatar_hash = db.Column(db.String(32))#MD5散列值
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')#博文
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref = 'author', lazy = 'dynamic')
    #关注的人
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref =db.backref('follower', lazy='joined'),#joined导致相关对象立即从关联查询中加载
                               lazy='dynamic', cascade='all, delete-orphan')#delete-orphan删除指向已删除记录的条目
    #被关注的人
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    @property
    def password(self):
        raise AttributeError('密码是个只写属性')
        #尝试获取 password 属性的值时，会抛出一个异常，明确告知密码的密文不能直接读取。

    @password.setter
    def password(self, password):
        #generate_password_hash()用于生成密码的密文。
        # 它接收一个密码明文参数，返回加密后的密码的密文。
        self.password_hash = generate_password_hash(password)

    #获取关注的人的博文，方法实现还为理解
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(
            Follow.follower_id == self.id)


    def verify_password(self, password):
        #heck_password_hash(hash, password) 函数用于验证密码
        # 第一个参数是密码的密文，第二个参数是密码的明文
        return check_password_hash(self.password_hash, password)#返回True说明密码正确



    #生成令牌
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)#基础偏移量SECRET_KEY,有效期3600秒
        return s.dumps({'confirm': self.id}).decode('utf-8')#使用字典形式，进行编码

    #验证令牌有效性
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))#进行解码
        except:
            return False
        if data.get('confirm') != self.id:#使用字典形式读取id,增加安全性
            return False
        self.confirmed = True #确认成功后将confirmed属性设为True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration = 3600):
        s =Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({ 'reset': self.id }).decode('utf-8')

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration = 3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return Fale
        if self.query.filter_by(email = new_email).first() is not None:
            return False
        #当有新邮件更新时，重新计算其md5值
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        db.session.commit()
        return True

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']: #更据电子邮件判断是否是管理员
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:#如果存在用户且没有缓存MD5值，进行缓存
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        self.follow(self)#创建用户时，把自己设为关注者


    def can(self, perm): #检测是否具有某项操作权限
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):#判断用户是否是管理员
        return self.can(Permission.ADMIN)

    def ping(self):#更新用户最后访问时间
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    #生成获取头像的网址
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://cn.gravatar.com/avatar'
        else:
            url = 'http://cn.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash() #如果有MD5值就使用，没有就计算
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating
        )

    #避免重复编写计算，专门定义函数执行MD5散列值计算
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)#关注者是当前用户，被关注者是其他用户
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()#用户调用自己关注的人有user就删除关系
        if f:
            db.session.delete(f)#删除Follow实例

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None #判断用户自己关注的人有没有user，有返回True

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    def is_like_post(self, post):
        if post.id is None:
            return False
        return self.likes.filter_by(post_id = post.id).first() is not None#判断自己有没有点赞，有就返回True

    #生成api登录令牌
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)#expires_in 授权过期时间
        return s.dumps({'id': self.id}).decode('utf-8')

    #验证令牌
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return None
        return User.query.get(data['id'])

    #将用户序列化为一个json字典
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'followed_posts_url': url_for('api.get_user_followed_posts',id=self.id),
            'post_count': self.posts.count()
        }
        return json_user

    def __repr__(self):
        return '<User %r>' % self.username



class AnonymousUser(AnonymousUserMixin): #无需检查是否登录，放心调用current_user.can()和
                                         #current_user.is_administrator()

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser#使Flask-Login应用自定义的匿名用户类


@login_manager.user_loader
def load_user(user_id):
    # 查询用户id,若不存在则返回None
    return User.query.get(int(user_id))

#博文模型
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(128))
    body = db.Column(db.Text)#正文
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)#时间戳
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))#外键
    body_html = db.Column(db.Text)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    likes = db.relationship('Like', backref = 'post', lazy = 'dynamic')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'img']
        attrs = {
            '*': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt']
        }
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),attributes=attrs,
            tags=allowed_tags, strip=True))

    ##Markdown()文本到HTML转换分三步完成：
    #使用markdown()函数把Markdown文本转换成HTML。
    #使用Blench的clean()函数删除所有不在白名单的标签。
    #使用Blench的linkify()函数将纯文本中的URL转换成适当的<a>链接

    #将博文序列化为一个json字典
    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post

    def delete(self):
        comments = self.comments
        for comment in comments:
            db.session.delete(comment)
        likes = self.likes
        for like in likes:
            db.session.delete(like)
        db.session.delete(self)
        db.session.commit()

    #只允许客户端提交body属性
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('博文没有正文')
        return Post(body=body)

    @staticmethod
    def add_default_title():
        for post in Post.query.all():
            if not post.title:
                post.title = '默认标题'
                db.session.add(post)
                db.session.commit()

    @staticmethod
    def add_default_category():
        for post in Post.query.all():
            if not post.category:
                post.category = Category.query.filter_by(category = '默认分类').first()
                db.session.add(post)
                db.session.commit()

db.event.listen(Post.body, 'set', Post.on_changed_body)
#将 on_changed_body() 注册为 body 字段的 SQLAlchemy set 事件的监听器
#当 body 字段的值发生改变时， on_changed_body() 会被自动调用。
#该函数自动将 Markdown 转换后的 HTML 代码存储在 body_html 字段里。

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean) #根据该字段查不良评论
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr','acronym', 'b', 'code', 'em' ,'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True
        ))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('评论没有正文')
        return Comment(body=body)

db.event.listen(Comment.body, 'set', Comment.on_changed_body)

#博文分类
class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key = True)
    category = db.Column(db.Unicode(128), unique = True)
    posts = db.relationship('Post', backref = 'category', lazy = 'dynamic')

    @staticmethod
    def add_categorys():
        categorys = [
            '博客开发',
            '生活点滴',
            '默认分类'
        ]
        for c in categorys:
            category = Category.query.filter_by(category = c).first()
            if category is None:
                category = Category(category = c)
            db.session.add(category)
        db.session.commit()

    def __repr__(self):
        return '<Category %r>' % self.category

class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default= datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

