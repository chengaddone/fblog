# 文章的视图
from flask import g, current_app, abort, render_template, jsonify, request

from blog.utils.common import user_login_data
from blog.utils.response_code import RET
from . import article_bp
from blog.models import Post, Comment
from ... import db


@article_bp.route("/<int:article_id>")
@user_login_data
def article_detail(article_id):
    """文章详情页的视图"""
    user = g.user
    # 查询博客文章的数据
    article = None
    try:
        article = Post.query.get(article_id)
    except Exception as e:
        current_app.logger.error(e)
    if not article:
        abort(404)  # 没有查询到文章数据，弹出404页面
    # 查到了文章数据，更新点击次数
    article.clicks += 1
    # 查询文章评论的数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.post_id == article.id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    comment_dict = []
    for comment in comments:
        comment_dict.append(comment.to_dict())
    data = {
        "user": user.to_dict() if user else None,
        "article": article.to_dict(),
        "comments": comment_dict
    }
    return render_template("blog/detail.html", data=data)


@article_bp.route("/article_comment", methods=["POST"])
@user_login_data
def article_comment():
    """文章评论的视图"""
    # 1.获取用户的登录信息
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 2.获取用户的评论数据
    json_data = request.json
    article_id = json_data.get("article_id")
    comment_content = json_data.get("comment_content")
    parent_id = json_data.get("parent_id")
    # 3.校验参数
    if not all([article_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(article_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 查询到要评论的文章,看文章是否存在
    try:
        article = Post.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg="未查询到文章数据")
    # 4.初始化评论模型
    comment = Comment()
    comment.user_id = user.id
    comment.post_id = article_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id
    # 5.添加到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库写入错误")
    # 6.返回响应
    data = comment.to_dict()
    return jsonify(errno=RET.OK, errmsg="评论成功", data=data)
