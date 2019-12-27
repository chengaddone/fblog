from flask import Flask

from config import config


def create_app():
    """创建app的工厂函数"""
    # 创建flask的app对象
    app = Flask(__name__)
    # 加载配置
    # app.config.from_object(config[config_name])

    # 注册蓝图
    from blog.modules.index import index_blue
    app.register_blueprint(index_blue)

    return app
