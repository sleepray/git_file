#coding:utf-8
import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    # 启动coverage引擎，branch=True分支覆盖分析，检查不同条件的True,False，include限制测试代码
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

import sys,click,threading
from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment, Category,Like
from flask_migrate import Migrate, upgrade

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)



@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role,Post=Post,Permission=Permission, Follow=Follow, Comment=Comment,Category=Category,Like=Like)

@app.cli.command()
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')#传入--coverage选项
def test(coverage):
    '''运行单元测试'''
    #test接受到--coverage时再检测,全局代码已经运行,为了保证检测准确性，设定设置环境变量后重启脚本
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'
        #sys.argv路径与书上不一致，应修改
        os.execvp(sys.executable, [sys.executable] + [sys.argv[0]+ ".exe"] + sys.argv[1:])#重启脚本
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage 日志:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory = covdir)
        print('HTML 位置：file://%s/index.html' % covdir)
        COV.erase() #清空数据

#运行带有分析器的应用程序
@app.cli.command()
@click.option('--length', default=25,
              help='在分析器报告中包含的函数数量')
@click.option('--profile-dir', default=None,
              help='保存分析器数据文件目录')
def profile(length, profile_dir):
    '''在代码分析器下启动应用程序'''
    from werkzeug.contrib.profiler import ProfilerMiddleware#ProfilerMiddleware 是一个查看性能的中间件
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run(debug=False)

@app.cli.command()
def deploy():
    '''运行部署任务'''
    #将数据库迁移到最新版
    upgrade()

    #创建或更新用户角色
    Role.insert_roles()

    #确保所有用户都关注了自己
    User.add_self_follows()

    #更新目录分类
    Category.add_categorys()

    #添加默认标题
    Post.add_default_title()

    #添加默认分类
    Post.add_default_category()

