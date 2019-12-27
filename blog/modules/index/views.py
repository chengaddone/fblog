# index模块的视图
from . import index_blue


@index_blue.route("/")
def index():
    return "hello flask"
