from flask import url_for
import unittest, json, re
from base64 import b64encode
from app import create_app, db, api
from app.models import User, Role, Post, Comment

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    #返回API发送的头部,包含了身份认证凭据和 MIME 类型
    def get_api_headers(self, username, password):
        return {
            'Authorization':
                'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def test_no_auth(self):
        response = self.client.get('/api/v1/posts/',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)#判断用户是否有身份凭证

    def test_bad_auth(self):
        #添加一个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='k@k.com', password='k', confirm=True, role=r)
        db.session.add(u)
        db.session.commit()

        #使用错误的密码登陆
        response = self.client.get(
            '/api/v1/posts/', headers=self.get_api_headers('x@x.com', 'j')
        )
        self.assertEqual(response.status_code, 401)

    def test_token_auth(self):
        #添加一个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='k@k.com', password='k', confirmed=True,
                 role=r)
        db.session.add(u)
        db.session.commit()

        #错误令牌内容
        response = self.client.get(
            '/api/v1/posts/',headers=self.get_api_headers('bad-token', ''))
        self.assertEqual(response.status_code, 401)

        #获取token
        response = self.client.post(
            '/api/v1/tokens/',headers=self.get_api_headers('k@k.com', 'k'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        #正确的token进行登陆
        response = self.client.get(
            '/api/v1/posts/',headers=self.get_api_headers(token, '')
        )
        self.assertEqual(response.status_code, 200)

        #验证登陆有效性
    def test_anonymous(self):
        response = self.client.get(
            '/api/v1/posts/',headers=self.get_api_headers('', '')
        )
        self.assertEqual(response.status_code, 401)

    def test_unconfirmed_account(self):
        #添加一个为确认用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='x@x.com', password='x', confirm=False, role=r)
        db.session.add(u)
        db.session.commit()

        #获取未确认账户列表
        response = self.client.get(
            '/api/v1/posts/',headers=self.get_api_headers('x@x.com', 'x')
        )
        self.assertEqual(response.status_code, 403)


    def test_posts(self):
        #添加用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)#判断用户是否存在，存在通过用例
        u = User(email='k@k.com', password='k', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        #发表博文
        response = self.client.post(
            '/api/v1/posts/',headers=self.get_api_headers('k@k.com', 'k'),
            data = json.dumps({'body': '发表博客内容测试*日志*'})#dumps()将字典转换为str,直接将字典类型写入json会报错
        )
        self.assertEqual(response.status_code, 201)#判断博文是否已创建
        url = response.headers.get('Location')
        self.assertIsNotNone(url)#判断url是否已创建

        #获取刚发布的博文
        response = self.client.get(url, headers=self.get_api_headers('k@k.com', 'k'))
        self.assertEqual(response.status_code, 200)#判断是否连接到该博文
        json_response = json.loads(response.get_data(as_text=True))#loads解码字符串类型
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], '发表博客内容测试*日志*')
        self.assertEqual(json_response['body_html'],'<p>发表博客内容测试<em>日志</em></p>')
        json_post = json_response

        #从当前用户处获取所有博文
        response = self.client.get(
            '/api/v1/users/{}/posts/'.format(u.id),headers=self.get_api_headers('k@k.com','k')
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        #用户关注者的所有博文
        response = self.client.get(
            '/api/v1/users/{}/timeline/'.format(u.id),
            headers=self.get_api_headers('k@k.com', 'k')
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        #编辑博文
        response = self.client.put(
            url,headers=self.get_api_headers('k@k.com', 'k'),
            data=json.dumps({'body': '修改博文测试'})
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], '修改博文测试')
        self.assertEqual(json_response['body_html'], '<p>修改博文测试</p>')

    def test_users(self):
        #添加两个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='x@x.com', username='x', password='x', confirmed=True, role=r)
        u2 = User(email='j@j.com', username='j', password='j', confirmed=True, role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        #获取用户
        response = self.client.get(
            '/api/v1/users/{}'.format(u1.id),
            headers=self.get_api_headers('j@j.com', 'j')
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'x')
        response = self.client.get(
            '/api/v1/users/{}'.format(u2.id),
            headers=self.get_api_headers('j@j.com', 'j')
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'j')

    def test_comments(self):
        #添加两个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='x@x.com', username='x', password='x', confirmed=True, role=r)
        u2 = User(email='j@j.com', username='j', password='j', confirmed=True, role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        #添加一个博文
        post = Post(body='api评论', author=u1)
        db.session.add(post)
        db.session.commit()

        #写一个评论
        response = self.client.post(
            '/api/v1/posts/{}/comments/'.format(post.id),
            headers=self.get_api_headers('j@j.com', 'j'),
            data=json.dumps({'body': 'Good [post](http://example.com)!'})
        )
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data(as_text=True))
        url = response.headers.get('Location')
        self.assertIsNotNone(url)
        self.assertEqual(json_response['body'],'Good [post](http://example.com)!')
        self.assertEqual(re.sub('<.*?>', '', json_response['body_html']), 'Good post!')#检测html格式转换成功没有

        #获取新评论
        response = self.client.get(url, headers=self.get_api_headers('x@x.com', 'x'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['body'], 'Good [post](http://example.com)!')

        #添加其他评论
        comment = Comment(body='谢谢', author=u1, post=post)
        db.session.add(comment)
        db.session.commit()

        #从评论中获得两条评论
        response = self.client.get(
            '/api/v1/posts/{}/comments/'.format(post.id),
            headers=self.get_api_headers('j@j.com', 'j')
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 2)

        #获取所有评论
        response = self.client.get(
            '/api/v1/posts/{}/comments/'.format(post.id),
            headers=self.get_api_headers('j@j.com', 'j')

        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 2)