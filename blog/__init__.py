import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_session import Session
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis

from config import config
from .extensions import db, mail, moment, ckeditor

# 定义redis数据库
redis_store = None  # type: StrictRedis


def setup_log(config_name):
    """设置日志"""
    # 设置日志记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试级别
    # 创建日志记录器，指明日志保存的路径、日志文件的大小和保存日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*10, backupCount=10)
    # 创建日志记录的格式、日志等级、输入日志信息的文件名、行数、日志信息
    formatter = logging.Formatter("%(levelname)s %(filename)s:%(lineno)d %(message)s")
    # 为创建的日志记录器设置记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    """创建app的工厂函数"""
    # 设置日志
    setup_log(config_name)
    # 创建flask的app对象
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 导入扩展对象
    db.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    # 初始化redis数据库
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST,
                              port=config[config_name].REDIS_PORT,
                              decode_responses=True)
    # 设置session，使用flask_session中的session扩展，session用于记录用户的登录信息
    Session(app)
    # 设置csrf保护，防止csrf攻击
    CSRFProtect(app)

    # 注册蓝图
    from blog.modules.blog import blog_bp
    app.register_blueprint(blog_bp)
    from blog.modules.auth import auth_bp
    app.register_blueprint(auth_bp)
    from blog.modules.admin import admin_bp
    app.register_blueprint(admin_bp)

    @app.after_request
    def after_request(response):
        """每次前端请求之后响应之前生成随机的CSRF值,并放在响应的cookie中，下次请求会将之带回验证"""
        csrf_token = generate_csrf()
        response.set_cookie("csrf_token", csrf_token)
        return response

    # 设置全局的404页面，当有未知链接时重定向到此页面
    @app.errorhandler(404)
    def page_notfound(e):
        return render_template("blog/404.html")

    return app
