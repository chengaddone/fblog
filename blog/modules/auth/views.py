# 普通用户的视图
import datetime
import random
import re
import time

from flask import request, abort, current_app, make_response, jsonify, render_template, session, g

from . import auth_bp
from blog.utils.captcha.captcha import captcha
from blog import redis_store, constants, db
from blog.constants import IMAGE_CODE_REDIS_EXPIRES
from blog.emailEx import send_mail
from blog.models import User
from blog.utils.response_code import RET
from ...utils.common import user_login_data


@auth_bp.route("/image_code")
def get_image_code():
    """获取图片验证码"""
    # 1.取到传入的参数，前端访问的url为/image_code?imageCodeId=xxx
    image_code_id = request.args.get("imageCodeId", None)
    # 2.判断参数是否有值，如果没有值则主动抛出403异常
    if not image_code_id:
        return abort(403)
    # 3.生成图片验证码，并将文字内容到redis
    name, text, image = captcha.generate_captcha()
    try:
        redis_store.setex("ImageCodeId_" + image_code_id, IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)
    # 4.将图片验证码返回
    response = make_response(image)
    # 设置返回头，使浏览器更智能的识别图片信息
    response.headers["Content-Type"] = "image/jpg"
    return response


@auth_bp.route('/email_code', methods=["POST"])
def send_email_code():
    """发送邮件验证码"""
    # 1.获取传入的参数
    params_dic = request.json
    e_mail = params_dic.get("e_mail")
    image_code = params_dic.get("image_code")
    image_code_id = params_dic.get("image_code_id")
    # 2.数据校验
    if not all([e_mail, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    if not re.match(r"^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$", e_mail):
        # 校验邮箱格式是否正确
        return jsonify(errno=RET.PARAMERR, errmsg="邮箱输入有误")
    # 3.从redis中取出图片验证码
    try:
        real_image_code = redis_store.get("ImageCodeId_"+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库查询错误")
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")
    # 4.校验图片验证码
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")
    # 5.通过验证，生成验证码
    email_code_str = "%06d" % random.randint(0, 999999)
    current_app.logger.debug("验证码内容：{}".format(email_code_str))  # 以log的形式打印出来
    # 6.将验证码存入redis中
    try:
        redis_store.set("email_"+e_mail, email_code_str, constants.EMAIL_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="验证码生成或保存失败")
    # 7.发送邮件
    data = {
        "email_code": email_code_str,
        "current_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    }
    html = render_template('emails.html', data=data)
    try:
        send_mail("邮件验证码", e_mail, html)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.EMAILSENDERR, errmsg='邮件发送错误')
    return jsonify(errno=RET.OK, errmsg='ok')


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册的视图"""
    # 1.取数据
    param_dict = request.json
    e_mail = param_dict.get("e_mail")
    email_code = param_dict.get("email_code")
    password = param_dict.get("password")
    # 2.校验数据
    if not all([e_mail, email_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if not re.match(r"^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$", e_mail):
        # 校验邮箱格式是否正确
        return jsonify(errno=RET.PARAMERR, errmsg="邮箱输入有误")
    # 3.取出session中保存的邮箱验证码
    try:
        real_email_code = redis_store.get("email_"+e_mail)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")
    if not real_email_code:
        return jsonify(errno=RET.NODATA, errmsg="无效的验证码")
    # 4.校验手机验证码
    if real_email_code != email_code:
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")
    # 5.初始化User模型，并赋值
    user = User()
    user.email = e_mail
    user.nick_name = e_mail
    user.last_login = datetime.datetime.now()
    user.password = password
    # 6.添加到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")
    # 7.注册成功之后，将用户的登录信息保存到session中,并保存登录状态
    session["user_id"] = user.id
    session["email"] = user.email
    session["nick_name"] = user.nick_name
    # 8.返回响应
    return jsonify(errno=RET.OK, errmsg="注册成功")
    # TODO 重复注册的问题


@auth_bp.route("/logout")
def logout():
    """退出登录"""
    session.pop("user_id", None)
    session.pop("email", None)
    session.pop("nick_name", None)
    session.pop("is_admin", None)
    return jsonify(errno=RET.OK, errmsg="退出登录成功")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    登录视图
    :return: json
    """
    # 1.获取参数
    params_dict = request.json
    e_mail = params_dict.get("e_mail")
    password = params_dict.get("password")
    # 2.校验参数
    if not all([e_mail, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="输入不能为空")
    if not re.match(r"^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$", e_mail):
        # 校验邮箱格式是否正确
        return jsonify(errno=RET.PARAMERR, errmsg="邮箱输入有误")
    # 3.校验密码是否正确
    try:
        user = User.query.filter(User.email == e_mail).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")
    # 校验密码
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或密码错误")
    # 4.保存用户登录状态
    session["user_id"] = user.id
    session["email"] = user.email
    session["nick_name"] = user.nick_name
    user.last_login = datetime.datetime.now()
    # 5.返回响应
    return jsonify(errno=RET.OK, errmsg="登录成功")


@auth_bp.route("/change_nickname", methods=["POST"])
@user_login_data
def change_nickname():
    """修改用户昵称的视图"""
    # 1.获取当前的登录用户
    user = g.user
    # 2.获取参数
    user_id = request.json.get("userId")
    new_nickname = request.json.get("new_nickname")
    # 3.校验数据
    if not all([user_id, new_nickname]):
        return jsonify(errno=RET.PARAMERR, errmsg="输入信息有误")
    try:
        user_id = int(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="数据异常，请稍后再试")
    # 如果用户名没有改变，直接返回
    if user.nick_name == new_nickname:
        return jsonify(errno=RET.OK, errmsg="OK")
    # 用户名唯一性校验，且只有自己可以改自己账户的昵称
    try:
        other = User.query.filter(User.nick_name == new_nickname).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="系统异常，请稍后再试")
    if other:
        return jsonify(errno=RET.DATAERR, errmsg="这个名字有用主了，换个名字吧")
    if user.id != user_id:
        return jsonify(errno=RET.PARAMERR, errmsg="请求错误")
    # 4.更改用户的数据
    if user.name_state == 1:
        user.old_name = user.nick_name
        user.nick_name = new_nickname
        user.name_state = 0
    elif user.name_state == 0:
        # 用户上一次修改名字后还没有被管理员审核
        user.nick_name = new_nickname
    else:
        user.name_state = 0
        return jsonify(errno=RET.DBERR, errmsg="系统异常，请稍后再试")
    # 5.上传数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="系统异常，请稍后再试")
    return jsonify(errno=RET.OK, errmsg="ok")
