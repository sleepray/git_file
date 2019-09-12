from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post

#随机生成用户
def users(count=100):
    fake = Faker()
    i = 0
    while i < count:#fake随机生成姓名、Email、句子等数据的多种生成器
        u = User(email=fake.email(),
                 username=fake.user_name(),
                 password='password',
                 confirmed=True,
                 name=fake.name(),
                 location=fake.city(),
                 about_me=fake.text(),
                 member_since=fake.past_date())
        db.session.add(u)
        try:#如果能写入继续下一个，不行就进行回滚
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback() #rollbakc()回滚数据

#随机生成文章
def posts(count=100):
    fake = Faker() #Faker()包随机生成姓名
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()#随机一个数后交给offset进行偏移，偏移量为这个数的值
        p = Post(body=fake.text(),
                 timestamp=fake.past_date(),
                 author=u)
        db.session.add(p)
    db.session.commit()