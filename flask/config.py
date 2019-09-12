# coding:utf-8
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER =  'smtp.qq.com'
    MAIL_PORT =  25
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '302559651@qq.com' #输入环境变量是不能加空格
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # QQ邮箱授权码：gyoufiaquygtbgfa
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]' #主题
    FLASKY_MAIL_SENDER = os.environ.get('FLASKY_MAIL_SENDER') or '302559651@qq.com' #发送邮箱
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN') or '1023499684@qq.com'#接受邮箱地址
    FLASKY_POSTS_PER_PAGE = 10 #每页显示记录量
    FLASKY_FOLLOWERS_PER_PAGE = 20 #每页显示关注者记录量
    FLASKY_COMMENTS_PER_PAGE = 10#每页显示评论数量
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True#启用慢查询
    FLASKY_SLOW_DB_QUERY_TIME = 0.5  # 慢查询时长


    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    #开发环境下的配置
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or\
        'mysql+pymysql://root:iloveyou88@localhost:3306/rct_dev?charset=utf8mb4'

class TestingConfig(Config):
    #测试环境下的配置
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
        'mysql+pymysql://root:iloveyou88@localhost:3306/rct_testing?charset=utf8mb4'
    WTF_CSRF_ENABLED = False#禁用CSRF保护

class ProductionConfig(Config):
    #生产环境中的配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
        'mysql+pymysql://root:iloveyou88@localhost:3306/rct?charset=utf8mb4'

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        #将错误发送给管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        #getattr(a,b,c) 函数用于返回一个对象属性值。如果属性b不存在，则返回c
        if getattr(cls, 'MAIL_USERNAME", None') is None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' 应用错误',
            credentials=credentials,
            secure=secure,
        )
        mail_handler.setLevel(logging.ERROR)#发生日志错误时发送
        app.logger.addHandler(mail_handler)

#使用字典的形式存储不同配置的类型
config = {
    'development' : DevelopmentConfig,
    'testing' : TestingConfig,
    'production' : ProductionConfig,
    'default' : DevelopmentConfig,
}