#coding:utf-8
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from ..models import Role, User,Category
from wtforms import StringField, PasswordField, BooleanField, SubmitField,TextAreaField,ValidationError,SelectField
from wtforms.validators import DataRequired,Length,Regexp,Email


class NameForm(FlaskForm):
    name = StringField('你叫什么名字', validators=[DataRequired()])
    #validators指定验证函数，DataRequired()确保提交的字段不为空
    submit = SubmitField('提交')

class EditProfileForm(FlaskForm):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('位置', validators=[Length(0, 64)])
    about_me = TextAreaField('自我介绍')
    submit = SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64),
                                             Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名需要以字母开头，包含字母、数字、点或下划线')])
    confirmed = BooleanField('已确认')
    role = SelectField('角色', coerce=int) #Selectfield下拉列表的包装,
    # 用于选择用户角色的SelectField，设定这个字段的初始值时，role_id被赋值给field.role.data，
    # 表单提交后，id从字段的data属性中提取。
    # 表单中声明SelectField时使用coerce=int参数保证这个字段的data属性值是整数。
    name = StringField('真实姓名', validators=[Length(0,64)])
    location = StringField('位置', validators=[Length(0,64)])
    about_me = TextAreaField('自我介绍')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs) #super()调用类EditProfileAdminForm
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):#当参数改变且数据库中有数据时抛出异常
        if field.data != self.user.email and\
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email 已被注册')

    def validate_username(self, field):
        if field.data != self.user.username and\
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被注册')

class PostForm(FlaskForm):
    title = StringField(u'输入文章标题', validators=[DataRequired()])
    category = SelectField(u'分类', coerce=int)
    body = PageDownField("输入文章内容", validators=[DataRequired()])#改为Markdown编辑器
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.category)
                                 for category in Category.query.order_by(Category.category).all()]

class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])#文本字段
    submit = SubmitField('提交')

