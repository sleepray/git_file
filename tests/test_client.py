import unittest,re
from app import create_app, db
from app.models import User, Role

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)#flask测试客户端对象，可以接收发送cookie

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('陌生人' in response.get_data(as_text=True))#测试能否获取首页数据，as_text=True转化为字符串

    def test_register_and_login(self):
        #注册一个新账号
        response = self.client.post('/auth/register', data={
            'email': 'k@k.com',
            'username': 'k',
            'password': 'k',
            'password2': 'k',
        })
        self.assertEqual(response.status_code, 302)#判断是否注册成功,302代表重定向

        #使用这个新账号进行登陆
        response = self.client.post('/auth/login', data={
            'email': 'k@k.com',
            'password': 'k',
        },follow_redirects=True)#follow_redirects=True自动重定向
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('你好,\s+k',
                                  response.get_data(as_text=True)))#jinjia2模板生成时会加上空格
        self.assertTrue('一封确认邮箱已经发送到你的邮箱' in response.get_data(as_text=True))

        #发送确认令牌
        user = User.query.filter_by(email='k@k.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token),follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('你的账号确认成功,谢谢' in response.get_data(as_text=True))

        #注销登陆
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('你已成功退出' in response.get_data(as_text=True))