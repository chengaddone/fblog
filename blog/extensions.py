# 扩展类的实例化
from flask_ckeditor import CKEditor
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

# 实例化数据库操作对象db
db = SQLAlchemy()
#
moment = Moment()
#
ckeditor = CKEditor()
# 实例化发送邮件的对象mail
mail = Mail()
