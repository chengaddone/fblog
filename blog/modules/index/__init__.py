from flask import Blueprint

# index模块的蓝图对象
index_bp = Blueprint("index", __name__)

from . import views
