# -*- coding: utf-8 -*-
# @Author: wangchao
# @Time: 20-3-2 上午9:44

from datetime import datetime
from flask import current_app, request
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app import db
import hashlib
from bs4 import BeautifulSoup


# 角色
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, doc="名称")
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role % r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0Xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class Follow(db.Model):
    """
    用户关系表
    """
    __table__name = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True, doc="关注者")
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True,doc="被关注者")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True, doc="邮箱")
    username = db.Column(db.String(64), unique=True, index=True,
                         doc="用户名")
    password_hash = db.Column(db.String(128), doc="密码")
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'),
                        doc="权限")
    confirmed = db.Column(db.Boolean, default=False, doc="是否验证")
    about_me = db.Column(db.Text(), doc="关于我")
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow,
                          doc="登录时间")
    avatar_hash = db.Column(db.String(32), doc="头像")
    article = db.relationship('Article', backref='author', lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all,delete-orphan',
                               doc="关注我的用户")
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined',
                                                   doc="关注用户"),
                                lazy='dynamic', cascade='all,delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic',
                               doc="评论")
    topic = db.Column(db.String(128), doc="用户关注的主题")
    timestamp = db.Column(db.DateTime, index=True,
                          default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        # 给用户赋予角色
        if self.role is None:
            # 若email是管理员的邮箱则赋予管理员角色
            if self.email == current_app.config['ADMIN'][0]:
                self.role = Role.query.filter_by(permissions=0xff).first()
            else:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        设置密码
        :param password: 密码
        :return:
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        验证密码
        :param password: 密码
        :return: bool
        """
        return check_password_hash(self.password_hash, password)

    def generate_token(self, expiration=3600):
        """
        生成token
        :param expiration: 有效时间
        :return: str
        """
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({'id': self.id, "username": self.username}).decode()

    def confirm(self, token):
        """
        账号验证
        :param token: token
        :return: bool
        """
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except Exception as e:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can(self, permissions):
        """
        角色验证
        :param permissions: 权限(int)
        :return: bool
        """
        # 进行and运算再对比验证
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        """
        管理员权限
        :return: bool
        """
        return self.can(Permission.ADMINISTER)

    def ping(self):
        """
        用户一登录就写入登录时间
        :return:
        """
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        """
        生成头像
        :param size: 图片大小(像素)
        :param default: 默认图片生成方式
        :param rating: 图片级别
        :return: URL
        """
        if request.is_secure:
            url = 'https://secure.gravatar.com/avator'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        params = {
            "url": url,
            "hash": hash,
            "size": size,
            "default": default,
            "rating": rating
        }
        return '{url}/hash?s={size}&d={default}&r={rating}'.format(**params)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Article.query.join(Follow, Follow.followed_id == Article.author_id) \
            .filter(Follow.follower_id == self.id)

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                print(user.username)
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __repr__(self):
        return '<User % r>' % self.username


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, doc="标题")
    summary = db.Column(db.Text, doc="摘要")
    body = db.Column(db.Text, doc="内容")
    body_md = db.Column(db.Text, doc="内容markdown")
    body_html = db.Column(db.Text, doc="内容带html")
    timestamp = db.Column(db.DateTime, index=True,
                          default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                          doc="作者")
    comments = db.relationship('Comment', backref='article', lazy='dynamic',
                               doc="评论")
    read = db.Column(db.Integer, default=0, doc="阅读量")

    @staticmethod
    def create(**kwargs):
        # 使用BeautifulSoup提取标题和简要
        soup = BeautifulSoup(kwargs["body_html"], "html.parser")

        # 获取body
        kwargs["body"] = soup.get_text().replace("\n", "")
        # 获取标题
        title = soup.find("h1").text
        kwargs["title"] = title if title else ""

        # 获取摘要,去掉h1标签,且去掉回车符号,且取前100个字符作为简介
        [s.extract() for s in soup("h1")]
        kwargs["summary"] = soup.get_text().replace("\n", "")[:100]

        article = Article.query.filter_by(title=kwargs["title"],
                                          author_id=kwargs["author_id"]).first()
        try:
            if article:
                article.body_html = kwargs["body_html"]
                article.body_md = kwargs["body_md"]
                article.summary = kwargs["summary"]
                article.title = kwargs["title"]
                article.body = kwargs["body"]
            else:
                article = Article(**kwargs)
                db.session.add(article)

            db.session.commit()
            return True
        except Exception as ex:
            print(str(ex))
            return False


# 监听body字段
# db.event.listen(Post.body, 'set', Post.on_changed_body)
# db.event.listen(Post.title, 'set', Post.on_changed_title)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean,default=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))


# db.event.listen(Comment.body, 'set', Comment.on_changed_body)
