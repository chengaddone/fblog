# 管理模块的视图
import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, session, redirect, url_for, g, jsonify, abort


from . import admin_bp
from blog.models import User, Category, Post, Comment, AboutMe
from blog.utils.common import user_login_data
from ... import constants, db
from ...utils.image_storage import storage
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
    # 3.读取图片并上传
    try:
        index_image_data = index_image.read()
        key = storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="图片上传失败")
    # 4.创建文章对象
    article = Post()
    article.title = title
    article.content = content
    article.digest = digest
    article.index_image_url = constants.QINIU_DOMIN_PREFIX + key
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


@admin_bp.route("/article_list")
def article_list():
    """管理页面文章的列表显示"""
    return None


@admin_bp.route("article_category", methods=["GET", "POST"])
def article_category():
    """管理文章分类的视图"""
    if request.method == "GET":
        # 查询所以的文章分类
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            abort(404)
        category_dict_list = []
        for category in categories:
            category_dict_list.append(category.to_dict())
        data = {
            "categories": category_dict_list
        }
        return render_template("admin/article_category.html", data=data)
    # post请求，更改文章的分类信息
    # 1.取参数
    category_name = request.json.get("category_name")
    category_id = request.json.get("category_id")
    # 2.校验参数
    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    if category_id:
        # 当分类的id存在，则为修改已有的分类
        try:
            category_id = int(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")
        if not category:
            current_app.logger.error()
            return jsonify(errno=RET.NODATA, errmsg="没有查询到相关分类信息")
        category.name = category_name
        # 提交到数据库
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库插入失败")
        return jsonify(errno=RET.OK, errmsg="编辑分类成功")
    else:
        # 新增分类信息
        category = Category()
        category.name = category_name
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="数据库插入失败")
        return jsonify(errno=RET.OK, errmsg="新增分类成功")


@admin_bp.route("/comment_list")
def comment_list():
    """获取评论审核页面"""
    # 获取当前页
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    comments = []
    comment_list_dict = []
    current_page = 1
    total_page = 1
    # 请求待审核的评论列表
    try:
        paginate = Comment.query.filter(Comment.status == 0)\
            .order_by(Comment.create_time.desc())\
            .paginate(page, constants.ADMIN_ARTICLE_PAGE_MAX_COUNT, False)
        comments = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    for comment in comments:
        comment_list_dict.append(comment.to_dict())
    data = {
        "comments": comment_list_dict,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/comment_audit.html", data=data)


@admin_bp.route("/comment_audit", methods=["POST"])
def comment_audit():
    """评论审核的视图"""
    # 1.获取参数
    comment_id = request.json.get("commentId")
    action = request.json.get("action")
    # 2.校验参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    if action not in ("agree", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    # 3.查找到要审核的信息
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="系统错误：数据库查询错误，请稍后再试")
    if not comment:
        return jsonify(errno=RET.DATAERR, errmsg="无效的数据")
    # 4.操作数据库
    if action == "agree":
        comment.status = 1
    else:
        comment.status = -1
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="系统错误，数据修改失败，请稍后再试")
    return jsonify(errno=RET.OK, errmsg="ok")


@admin_bp.route("/nickname_list")
def nickname_list():
    """用户昵称审核的列表显示视图"""
    # 1.获取当前的页数
    page = request.args.get("page", 1)
    # 2.校验数据
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    # 3.获取修改过名称的用户并分页
    users = []
    user_list_dict = []
    current_page = 1
    total_page = 1
    try:
        paginate = User.query.filter(User.is_admin != 1, User.name_state == 0)\
            .order_by(User.update_time.desc())\
            .paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    for user in users:
        user_list_dict.append(user.to_admin_dict())
    # 4.准备回传的数据
    data = {
        "users": user_list_dict,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/nickname_audit.html", data=data)


@admin_bp.route("/nickname_audit", methods=["POST"])
def nickname_audit():
    """用户昵称审核请求的接收视图"""
    # 1.获取参数
    user_id = request.json.get("userId")
    action = request.json.get("action")
    # 2.校验参数
    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    try:
        user_id = int(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    if action not in ("agree", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    # 3.查找到要审核的用户信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="系统错误：数据库查询错误，请稍后再试")
    if not user:
        return jsonify(errno=RET.DATAERR, errmsg="无效的数据")
    # 4.操作数据库
    if action == "reject":
        try:
            other = User.query.filter(User.nick_name == user.old_name).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="系统错误：数据库查询错误，请稍后再试")
        if not other:  # 没有重名的用户
            user.nick_name = user.old_name
        else:
            user.nick_name = user.email
    user.name_state = 1
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="系统错误，数据修改失败，请稍后再试")
    return jsonify(errno=RET.OK, errmsg="ok")


@admin_bp.route("/leave_word")
def leave_word():
    """留言审核页面的视图"""
    return render_template("admin/leave_word.html")


@admin_bp.route("/admin_head_pic", methods=["GET", "POST"])
@user_login_data
def admin_head_pic():
    """管理员上传头像的接口"""
    user = g.user
    if request.method == "GET":
        return render_template("admin/head_pic.html", data={"user": user.to_dict()})
    # post请求代表上传头像
    # 1.取到图片资源
    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="图片读取失败")
    # 2.上传图片到七牛云
    try:
        key = storage(avatar)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="图片上传到七牛云失败")
    # 3.将头像的路径写入用户数据库
    user.avatar_url = constants.QINIU_DOMIN_PREFIX + key
    # 4.上传到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="系统错误：数据上传至数据库失败，请稍后再试")
    # 拼接并返回图片的地址
    data = {
        "avatar_url": constants.QINIU_DOMIN_PREFIX + key
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@admin_bp.route("/reset_head_pic", methods=["POST"])
@user_login_data
def reset_head_pic():
    """将管理员的头像清空，重新设置为Gravatar网站中的头像"""
    user = g.user
    if user.is_admin == 1:
        user.avatar_url = ""
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="系统错误：数据库更新失败，请稍后再试")
        data = {
            "avatar_url": user.to_dict().get("avatar_url")
        }

        return jsonify(errno=RET.OK, errmsg="OK", data=data)
    else:
        return jsonify(errno="10010", errmsg="无效的请求")


@admin_bp.route("/edit_page_about_me", methods=["GET", "POST"])
def edit_page_about_me():
    """编辑‘关于我’页面的视图"""
    info = []
    try:
        info = AboutMe.query.all()
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
    if not info:
        about_me = None
    else:
        about_me = info[0]
    if request.method == "GET":
        # get请求，返回页面
        return render_template("admin/about_me.html", data={"about_me": about_me.to_dict() if about_me else None})
    # TODO post请求代表修改内容
    # if not about_me:
