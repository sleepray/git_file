import unittest
import time
from datetime import datetime
from app import create_app,db
from app.models import User, Permission,AnonymousUser, Role,Follow

class UserModelTestCase(unittest.TestCase):
    def setUp(self): #建表
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push() #推出文本上下文
        db.create_all()
        Role.insert_roles()

    def tearDown(self):#移除表
        db.session.remove()
        db.drop_all()
        self.app_context.pop()#移除列表中的元素

    def test_password_setter(self):#测试密文是否转换
        u = User(password = 'cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self): #测试能否读取明文
        u = User(password = 'cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self): #测试密文
        u = User(password = 'cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self): #测试两次密文是否相同
        u = User(password = 'cat')
        u2 = User(password = 'cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self): #测试邮件确认令牌
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()#生成令牌
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):#测试不同账号的令牌相互使用
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):#测试超过有效期的令牌
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1) #有效期1秒
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):#测试修改密码令牌
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog')) #验证新密码

    def test_invalid_reset_token(self):#测试修改密码令牌错误能否修改密码
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertFalse(u.reset_password(token + 'a', 'horse'))
        self.assertTrue(u.verify_password('cat'))

    def test_valid_email_change_token(self):#测试修改邮箱地址
        u = User(email='k@k.com', password='k')
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('t@t.com')
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.email == 't@t.com')

    def test_invalid_email_change_token(self):#测试不同邮箱令牌是否能更改邮箱
        u1 = User(email='k@k.com', password='cat')
        u2 = User(email='t@t.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_email_change_token('r@r.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 't@t.com')

    def test_duplicate_email_change_token(self):#测试修改邮箱为数据库中已有的邮箱是否失败
        u1 = User(email='k@k.com', password='cat')
        u2 = User(email='t@t.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u2.generate_email_change_token('k@k.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 't@t.com')

    def test_user_role(self): #测试普通用户的权限
        u = User(email='x@x.com', password='x')
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_moderator_role(self):#测试审核员权限
        r = Role.query.filter_by(name='Moderator').first()
        u = User(email='k@k.com', password='k', role=r)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_administrator_role(self):#测试管理员权限
        r = Role.query.filter_by(name='Administrator').first()
        u = User(email='k@k.com', password='k', role=r)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertTrue(u.can(Permission.ADMIN))

    def teset_anoymous_user(self):#测试匿名用户权限
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_timestamps(self): # 测试时间差
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(
            (datetime.utcnow() - u.member_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 3)

    def test_ping(self): #测试ping值
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping() #更新最后访问时间
        self.assertTrue(u.last_seen > last_seen_before)

    def test_gravatar(self): #测试头像图片参数是否正确
        u = User(email='k@k.com', password='cat')
        with self.app.test_request_context('/'):#test_request_context临时的上下文请求
            gravatar = u.gravatar()
            gravatar_256 = u.gravatar(size=256)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')
        with self.app.test_request_context('/', base_url='https://example.com'):
            gravatar_ssl = u.gravatar()
        self.assertTrue('http://cn.gravatar.com/avatar/'  +
                        '61e2c054559da82ee780ca2b4bc6b3a5' in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)
        self.assertTrue('https://cn.gravatar.com/avatar/' +
                        '61e2c054559da82ee780ca2b4bc6b3a5' in gravatar_ssl)

    def test_follows(self):#测试关联表
        u1 = User(email='k@k.com', password='cat')
        u2 = User(email='t@t.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))#判断u1是否关注u2
        self.assertFalse(u1.is_followed_by(u2))#判断u1是否被u2关注
        timestamp_before = datetime.utcnow()
        u1.follow(u2) #u1关注u2
        db.session.add(u1)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.followed.count() == 2)#判断u1关注的人是不是2个
        self.assertTrue(u2.followers.count() == 2)#判断关注u2的人是不是2个
        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2) #判断u1关注的最后一个用户是不是u2
        self.assertTrue(timestamp_before <= timestamp_after)#判断关注时间差
        f = u2.followers.all()[-1]
        self.assertTrue(f.follower == u1)#判断关注u2的最后一个用户是不是u1
        u1.unfollow(u2) #取消u1关注u2
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)#判断关联表关联数量
        u2.follow(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        db.session.delete(u2)#移除u2
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)

    def test_to_json(self): #判断用户信息
        u = User(email='x@x.com', password='cat')
        db.session.add(u)
        db.session.commit()
        with self.app.test_request_context('/'):
            json_user = u.to_json()
        expected_keys = ['url', 'username', 'member_since', 'last_seen',
                         'posts_url', 'followed_posts_url', 'post_count']
        #assertEqual(a,b)判断a等于b
        self.assertEqual(sorted(json_user.keys()), sorted(expected_keys))
        self.assertEqual('/api/v1/users/' + str(u.id), json_user['url'])