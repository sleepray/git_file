# coding:utf-8
'''
蓝图，定义路由和错误程序，保证多人编程不相互影响
'''
from flask import Blueprint
from ..models import Permission

main = Blueprint('main', __name__) #实例化，第一个参数为蓝图名称，第二个为当前模块包的名字

from . import views, errors # 路由保存在views模块中， 错误处理程序保存在errors模块
#from . import <some-module> 语法是 Python 的相对导入，. 用于在当前包中导入模块。
#导入这两个模块的操作，必须放在最后进行，以避免发生循环导入的错误。
# 原因在于，views 和 errors 两个模块也会导入 main 蓝图。

#避免调用render_template()多添加一个模板参数，将Permission类添加进模板上下文
@main.app_context_processor#app_context_processor 可以将所有 render_template() 都需要的变量自动传递给模板
def inject_permissions():
    return dict(Permission=Permission)