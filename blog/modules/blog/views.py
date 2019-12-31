# index模块的视图
from flask import current_app, render_template, g

from . import blog_bp
from blog.utils.common import user_login_data


@blog_bp.route("/")
@user_login_data
def index():
    user = g.user
    data = {
        "user": user.to_dict() if user else None
    }
    return render_template("blog/index.html", data=data)


@blog_bp.route('/favicon.ico')
def favicon():
    """加载网页图标"""
    # 使用send_static_file来加载静态文件
    return current_app.send_static_file("blog/Blog.png")
