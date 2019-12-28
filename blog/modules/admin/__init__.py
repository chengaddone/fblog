# 后台管理模块的蓝图
from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import views
