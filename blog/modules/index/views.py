# index模块的视图
from flask import current_app, render_template, g, request, jsonify

from . import index_bp
from blog.utils.common import user_login_data

from blog import constants
from blog.models import Post, Category
from ...utils.response_code import RET


@index_bp.route("/")
@user_login_data
def index():
    """首页的视图函数"""
    # 获取用户的登录信息
    user = g.user
    # 获取首页的文章列表，默认为空
    post_list = []
    try:
        post_list = Post.query.order_by(Post.clicks.desc()).limit(constants.CLICK_RANK_MAX_ARTICLE)
    except Exception as e:
        current_app.logger.error(e)
    post_list_dict = []
    for post in post_list:
        post_list_dict.append(post.to_basic_dict())
    data = {
        "user": user.to_dict() if user else None,
        "posts": post_list_dict,
    }
    return render_template("blog/index.html", data=data)


@index_bp.route('/favicon.ico')
def favicon():
    """加载网页图标"""
    # 使用send_static_file来加载静态文件
    return current_app.send_static_file("index/Blog.png")


@index_bp.route('/articles', methods=["GET"])
@user_login_data
def articles():
    """文章列表页的视图"""
    # 获取用户的登录信息
    user = g.user
    # 获取文章的分类信息
    categories = []
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())
    data = {
        "user": user.to_dict() if user else None,
        "categories": category_list,
    }
    return render_template("blog/articles.html", data=data)


@index_bp.route('/article_list', methods=["GET"])
def article_list():
    """动态获取文章列表的视图"""
    # 1.获取文章列表的参数，包括分类id和页码信息
    category_id = request.args.get("category_id", "0")  # 0为默认分类
    page = request.args.get("page", "1")  # 当前文章列表的页数，默认为1
    per_page = request.args.get("per_page", "10")  # 每一页中默认的数据数量
    # 2.校验参数
    try:
        category_id = int(category_id)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 3.构建查询条件
    filters = []
    if category_id != 0:
        filters.append(Post.category_id == category_id)
    # 4.查询数据并分页
    try:
        paginate = Post.query.filter(*filters).order_by(Post.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库查询错误")
    # 取到当前页的文章数据
    posts = paginate.items
    # 获取总页数
    total_page = paginate.pages
    # 获取当前页
    current_page = paginate.page
    # 处理数据样式
    article_list_dict = []
    for article in posts:
        article_list_dict.append(article.to_basic_dict())
    # 5.准备传输数据
    data = {
        "articleList": article_list_dict,
        "totalPage": total_page,
        "currentPage": current_page
    }
    # 6.返回数据
    return jsonify(errno=RET.OK, errmsg="ok", data=data)
