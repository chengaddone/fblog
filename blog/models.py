# 项目的模型类
import hashlib

from .extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录更新时间


class User(BaseModel, db.Model):
    """用户模型类"""
    __tablename__ = "blog_user"

    id = db.Column(db.Integer, primary_key=True)  # 用户id
    nick_name = db.Column(db.String(32), unique=True, nullable=False)  # 用户昵称
    password_hash = db.Column(db.String(128), nullable=False)  # 加密密码
    email = db.Column(db.String(254), unique=True, nullable=False)  # 用户邮箱账号
    avatar_url = db.Column(db.String(128))  # 用户头像路径
    last_login = db.Column(db.DateTime, default=datetime.now)  # 上次登录时间
    is_admin = db.Column(db.Boolean, default=False)  # 是否是管理员
    signature = db.Column(db.String(512))  # 用户个性签名
    gender = db.Column(db.Enum("MAN", "WOMAN"), default="MAN")  # 用户性别
    # 当前用户所发布的文章
    post_list = db.relationship('Post', backref='user', lazy='dynamic')
    # 当前用户发布的评论
    comment_list = db.relationship('Comment', backref='user', lazy='dynamic')

    @property  # property装饰器让password方法可以以属性的样式被调用
    def password(self):
        raise AttributeError("当前属性不允许读")  # 当直接以属性的方式访问password方法，抛出异常

    @password.setter  # 相当于重写password的setter方法，让其完成相应属性的赋值功能
    def password(self, value):
        self.password_hash = generate_password_hash(value)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "avatar_url": self.avatar_url if self.avatar_url else self.gravatar(),
            "email": self.email,
            "gender": self.gender if self.gender else "MAN",
            "signature": self.signature if self.signature else "",
        }
        return resp_dict

    def to_admin_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "email": self.email,
            "register": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return resp_dict


class Post(db.Model, BaseModel):
    """博客文章模型类"""
    __tablename__ = "blog_post"

    id = db.Column(db.Integer, primary_key=True)  # 博客文章编号
    title = db.Column(db.String(256), nullable=False)  # 博客文章标题
    digest = db.Column(db.String(512), nullable=False)  # 博客文章摘要
    content = db.Column(db.Text, nullable=False)  # 博客文章内容
    clicks = db.Column(db.Integer, default=0)  # 浏览量
    index_image_url = db.Column(db.String(256))  # 博客文章列表图片路径
    category_id = db.Column(db.Integer, db.ForeignKey("blog_category.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("blog_user.id"))  # 当前文章的作者id
    status = db.Column(db.Integer, default=0)  # 当前文章状态 如果为0代表审核通过，1代表审核中，-1代表审核不通过
    reason = db.Column(db.String(256))  # 未通过原因，status = -1 的时候使用
    like_count = db.Column(db.Integer, default=0)  # 点赞条数
    # 当前文章的所有评价
    comments = db.relationship("Comment", lazy="dynamic", backref='post', cascade="all, delete-orphan")

    def to_review_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "reason": self.reason if self.reason else ""
        }
        return resp_dict

    def to_basic_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "index_image_url": self.index_image_url,
            "clicks": self.clicks,
            "like_count": self.like_count,
            "category": self.category.to_dict(),
            "comments_count": self.comments.count(),
        }
        return resp_dict

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "comments_count": self.comments.count(),
            "clicks": self.clicks,
            "category": self.category.to_dict(),
            "index_image_url": self.index_image_url,
            "author": self.user.to_dict() if self.user else None,
            "like_count": self.like_count
        }
        return resp_dict


class Category(BaseModel, db.Model):
    """文章分类"""
    __tablename__ = "blog_category"

    id = db.Column(db.Integer, primary_key=True)  # 分类编号
    name = db.Column(db.String(64), nullable=False)  # 分类名
    post_list = db.relationship('Post', backref='category', lazy='dynamic')

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "name": self.name
        }
        return resp_dict


class Comment(BaseModel, db.Model):
    """评论模型类"""
    __tablename__ = "blog_comment"

    id = db.Column(db.Integer, primary_key=True)  # 评论编号
    user_id = db.Column(db.Integer, db.ForeignKey("blog_user.id"), nullable=False)  # 用户id
    post_id = db.Column(db.Integer, db.ForeignKey("blog_post.id"), nullable=False)  # 文章id
    content = db.Column(db.Text, nullable=False)  # 评论内容
    parent_id = db.Column(db.Integer, db.ForeignKey("blog_comment.id"))  # 父评论id
    parent = db.relationship("Comment", remote_side=[id])  # 自关联
    status = db.Column(db.Integer, default=0)  # 当前新闻状态 如果为0代表审核中，1代表审核通过，-1代表审核不通过
    reason = db.Column(db.String(256))  # 未通过原因，status = -1 的时候使用

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "parent": self.parent.to_dict() if self.parent else None,
            "user": User.query.get(self.user_id).to_dict(),
            "post_id": self.post_id,
        }
        return resp_dict


class PostLike(BaseModel, db.Model):
    """文章点赞"""
    __tablename__ = "post_like"

    post_id = db.Column("comment_id", db.Integer, db.ForeignKey("blog_post.id"), primary_key=True)  # 评论编号
    user_id = db.Column("user_id", db.Integer, db.ForeignKey("blog_user.id"), primary_key=True)  # 用户编号
