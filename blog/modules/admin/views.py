# 管理模块的视图
import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, session, redirect, url_for, g, jsonify, abort


from . import admin_bp
from blog.models import User, Category, Post
from blog.utils.common import user_login_data
from ... import constants, db
from ...utils.response_code import RET


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """管理端的登录页"""
    if request.method == "GET":
        # get请求代表访问登录页面，返回登录页面的模板
        # 返回模板前先判断是否有管理员登录，如果有，直接重定向到管理端的首页
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        if user_id and is_admin:
            user = User.query.get(user_id)
            data = {
                "user": user.to_dict() if user else None
            }
            return render_template("admin/index.html", data=data)
        return render_template("admin/login.html")
    # 登录操作
    # 1.获取登录的参数
    username = request.form.get("username")
    password = request.form.get("password")
    # 2.校验参数
    if not all([username, password]):
        return render_template("admin/login.html", errmsg="用户名密码不能为空")
    # 3.查询到当前登录的用户
    try:
        user = User.query.filter(User.nick_name == username, User.is_admin == 1).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="系统错误，请稍后再试")
    if not user:
        return render_template("admin/login.html", errmsg="无效的用户名")
    # 4.校验密码
    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="用户名密码错误")
    # 5.将用户信息保存到session中
    session["user_id"] = user.id
    session["email"] = user.email
    session["nick_name"] = user.nick_name
    session["is_admin"] = True
    return redirect(url_for("admin.index"))


@admin_bp.route("/logout")
def logout():
    """管理页面的退出登录"""
    session.pop("user_id", None)
    session.pop("email", None)
    session.pop("nick_name", None)
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/index")
@user_login_data
def index():
    user = g.user
    data = {
        "user": user.to_dict()
    }
    return render_template("admin/index.html", data=data)


@admin_bp.route("/user_count")
def user_count():
    """管理端的用户数据展示视图"""
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin != 1).count()
    except Exception as e:
        current_app.logger.error(e)
    # 月新增用户
    mon_count = 0
    t = time.localtime()
    begin_mon_date = datetime.strptime(('%d-%02d-01' % (t.tm_year, t.tm_mon)), "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin != 1, User.create_time >= begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)
    # 日新增用户
    day_count = 0
    begin_day_date = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin != 1, User.create_time >= begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)
    # 折线图数据
    active_time = []
    active_count = []
    # 取到当前这一天的开始时间数据
    today_date = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")  # 今天的00:00:00
    # 循环取今天以前一个月每一天活跃的用户数量
    for i in range(0, 31):
        begin_date = today_date - timedelta(days=i)
        end_date = begin_date + timedelta(days=1)
        count = User.query.filter(User.is_admin != 1, User.last_login >= begin_date,
                                  User.last_login < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime('%Y-%m-%d'))
    # 反转数组，让最近的一天显示在最右边
    active_time.reverse()
    active_count.reverse()
    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }

    return render_template("admin/user_count.html", data=data)


@admin_bp.route("/user_list")
def user_list():
    """用户管理页面视图"""
    # 获取当前是第几页
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    # 获取用户列表信息并分页
    users = []
    user_list_dict = []
    current_page = 1
    total_page = 1
    try:
        paginate = User.query.filter(User.is_admin != 1).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    for user in users:
        user_list_dict.append(user.to_admin_dict())
    # 准备传输数据
    data = {
        "users": user_list_dict,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/user_list.html", data=data)


@admin_bp.route("/write_blog", methods=["GET", "POST"])
@user_login_data
def write_blog():
    """发布博客的视图"""
    user = g.user
    if request.method == "GET":
        # get请求表示写文章，返回写文章的页面
        # 获取到所有的分类信息
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        category_list = []
        for category in categories:
            category_list.append(category.to_dict())
        data = {
            "user": user.to_dict(),
            "categories": category_list
        }
        return render_template("admin/write_blog.html", data=data)
    # post请求则表示发布文章的请求
    # 1.获取提交的数据
    form_data = request.form
    title = form_data.get("title")
    digest = form_data.get("digest")
    content = form_data.get("content")
    index_image = request.files.get("index_image")
    category_id = form_data.get("category_id")
    # 2.校验参数
    if not all([title, digest, category_id, content, index_image]):
        return jsonify(errno=RET.PARAMERR, errmsg="不能有空值")
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误，请稍后在试")
    # 3.TODO 读取图片
    index_image_data = "http://47.102.100.102/blog/01.jpg"
    # 4.创建文章对象
    article = Post()
    article.title = title
    article.content = content
    article.digest = digest
    article.index_image_url = index_image_data
    article.category_id = category_id
    article.user_id = user.id
    # 5.提交到数据库
    try:
        db.session.add(article)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败，请稍后在试")
    return jsonify(errno=RET.OK, errmsg="OK")

