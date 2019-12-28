# index模块的视图
from . import blog_bp


@blog_bp.route("/")
def index():
    return "hello flask"
