# 自定义一些公共的方法，比如校验登录的方法
import functools

from flask import session, current_app, g
from blog.models import User


# 定义用户登录查询的装饰器
def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id", None)
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return f(*args, **kwargs)
    return wrapper
