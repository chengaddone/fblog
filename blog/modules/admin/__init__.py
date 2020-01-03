# 后台管理模块的蓝图
from flask import Blueprint, session, request, url_for, redirect

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import views


@admin_bp.before_request
def check_admin():
    """校验管理员权限的请求钩子"""
    # 如果不是管理员，也不是访问管理员的登录页，则跳转到首页
    is_admin = session.get("is_admin", False)
    if not is_admin and not request.url.endswith(url_for("admin.login")):
        return redirect("/")
