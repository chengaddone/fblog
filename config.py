import logging

from redis import StrictRedis


class Config(object):
    """项目的配置"""
    DEBUG = True
    SECRET_KEY = "ADJKsad25*-dsof@$5098"
    # 配置mysql数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:940606@127.0.0.1:3306/f_blog"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 配置redis数据库
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    # 配置session存储位置，存在redis中
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session签名
    SESSION_USER_SIGNER = True
    # 设置session需要过期，且过期时间为7天
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400*7
    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发环境的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境的配置"""
    DEBUG = False
    LOG_LEVEL = logging.WARNING


class TestingConfig(Config):
    """单元测试的环境配置"""
    DEBUG = True
    TESTING = True


config = {
    "development": DevelopmentConfig,
    "productionConfig": ProductionConfig,
    "testing": TestingConfig
}
