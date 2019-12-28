from flask import Blueprint

# index模块的蓝图对象
blog_bp = Blueprint("blog", __name__)

from . import views
