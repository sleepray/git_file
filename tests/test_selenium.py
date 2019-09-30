import re, threading, time, unittest
from selenium import webdriver
from app import create_app, db, fake
from app.models import Role, User, Post

class SeleniumTestCase(unittest.TestCase):
    client = None

    #运行测试前运行
    @classmethod
    def setUpClass(cls):
        #启动chrome
        options = webdriver.ChromeOptions() #无界浏览
        options.add_argument('headless')#add_argument读入命令行参数
        try:
            cls.client = webdriver.Chrome(options=options)
        except:
            pass

        #如果无法启动浏览器，跳过下列测试
        if cls.client:
            #创建应用
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            #禁止日志，保持输出清洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")#指定最低的日志级别，低于ERROR的级别将被忽略

            #创建数据库,并使用一些虚拟数据填充
            db.create_all()
            Role.insert_roles()
            fake.users(10)
            fake.posts(10)

            #添加管理员
            admin_role = Role.query.filter_by(name='Administrator').first()
            admin = User(email='k@k.com',username='测试selenium',password='k',role=admin_role,confirmed=True)
            db.session.add(admin)
            db.session.commit()

            #flask 1.1.1下失效，更改为0.12.2才能运行
            #在一个线程中启动Flask服务器
            cls.server_thread = threading.Thread(target=cls.app.run,
                                                 kwargs={'debug': False})
            cls.server_thread.start()

            #等待1s确保服务器已启动
            time.sleep(1)

    #运行测试后运行
    @classmethod
    def tearDownClass(cls):
        if cls.client:
            #关闭服务器以及浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            #销毁数据库
            db.drop_all()
            db.session.remove()

            #删除应用上下文
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('浏览器不能运行')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        #进入首页
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('陌生人',self.client.page_source))

        #进入登录页面
        self.client.find_element_by_link_text('登录').click()
        self.assertIn('<h1>登录</h1>', self.client.page_source)

        #登录
        self.client.find_element_by_name('email').send_keys('k@k.com')
        self.client.find_element_by_name('password').send_keys('k')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('测试selenium',self.client.page_source))

        #进入用户资料页面
        self.client.find_element_by_link_text('个人主页').click()
        self.assertIn('<h1>测试selenium</h1>', self.client.page_source)#assertIn(a,b) a in b
