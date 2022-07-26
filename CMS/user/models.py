from uuid import uuid4

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    我们直接继承django自带的用户模型
    该模型自带了password，username，email字段
    """
    # 用户角色映射
    ROLE_CHOICE = [
        ('visitors', '浏览者'),
        ('lucky_draw', '抽奖者'),
        ('judges', '评委'),
        ('senior_judges', '高级评委'),
        ('poster_manager', '海报管理者'),
        ('admin', '管理员'),
    ]
    # 这里我们定义一个主键id，默认值为一个uuid序列
    id = models.UUIDField(default=uuid4, primary_key=True)
    # 这里我们定义一个昵称字段，默认值为'佚名'
    nickname = models.CharField(max_length=128, default='佚名')
    # 用户角色
    role = models.CharField(choices=ROLE_CHOICE, default='visitors', max_length=64)
    # 学院和专业
    grade = models.CharField(max_length=128, default='')

    @property
    def grade_r(self):
        try:
            g = Grade.objects.get(id=self.grade)
        except Exception:
            g = type('test', (), {'college': '', 'major': ''})()
        return g

    @property
    def role_display(self):
        for key, value in self.ROLE_CHOICE:
            if self.role == key:
                return value

    def to_json(self):
        """
        这个函数的作用是把数据库对应的数据字段转为字典格式，方便传入到django前端模板使用
        """
        return {
            'id': self.id, 'username': self.username, 'nickname': self.nickname,
            'email': self.email, 'role': self.role_display,
            'role_r': self.role, 'grade_r': self.grade_r
        }


class Meeting(models.Model):
    # 这里我们定义一个主键id，默认值为一个uuid序列
    id = models.UUIDField(default=uuid4, primary_key=True)
    # 这里我们定义一个会议名称字段，默认值为'无'
    title = models.CharField(max_length=128, default='无')
    # 这里我们定义一个会议开始字段，默认值为'当前时间'
    start_time = models.DateTimeField(auto_now=True)
    # 这里我们定义一个会议结束字段，默认值为'当前时间'
    end_time = models.DateTimeField(auto_now=True)
    # 这里我们定义一个会议人数字段，默认值为1
    number = models.IntegerField(default=1)

    @property
    def start_time_d(self):
        return self.start_time.strftime('%Y-%m-%d %H:%M')

    @property
    def end_time_d(self):
        return self.end_time.strftime('%Y-%m-%d %H:%M')


class Poster(models.Model):
    # 这里我们定义一个主键id，默认值为一个uuid序列
    id = models.UUIDField(default=uuid4, primary_key=True)
    # 这里我们定义一个海报名称字段，默认值为'无'
    title = models.CharField(max_length=128, default='无')
    # 这里我们定义一个摘要字段，默认值为'无'
    summary = models.CharField(max_length=256, default='无')
    # 这里我们定义一个图片路径字段
    image_path = models.FileField(upload_to='static/images/')
    # 谁发布的海报
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # 票数
    vote_number = models.IntegerField(default=0)
    # 评委分数
    one_score_total = models.IntegerField(default=0)
    # 参与的评委人数
    one_score_number = models.IntegerField(default=0)
    # 一级平均分数
    one_score_avg = models.IntegerField(default=0)
    # 高级评委分数
    two_score_total = models.IntegerField(default=0)
    # 参与的高级评委人数
    two_score_number = models.IntegerField(default=0)
    # 二级平均分数
    two_score_avg = models.IntegerField(default=0)
    # 作品等级，优秀作品等级为2，最佳作品等级为1
    level = models.IntegerField(default=0)
    # 学院和专业
    grade = models.CharField(max_length=128, default='')
    # 是否已被投票
    if_vote = models.IntegerField(default=0)

    @property
    def grade_r(self):
        try:
            g = Grade.objects.get(id=self.grade)
        except Exception:
            g = type('test', (), {'college': '', 'major': ''})()
        return g

    @property
    def one_score(self):
        return self.one_score_avg

    @property
    def two_score(self):
        return self.two_score_avg

    def save(self, **kwargs):
        if self.one_score_number == 0:
            self.one_score_avg = 0
        else:
            self.one_score_avg = self.one_score_total / self.one_score_number

        if self.two_score_number == 0:
            self.two_score_avg = 0
        else:
            self.two_score_avg = self.two_score_total / self.two_score_number
        return super().save(**kwargs)


class Luck(models.Model):
    # 这里我们定义一个主键id，默认值为一个uuid序列
    id = models.UUIDField(default=uuid4, primary_key=True)
    # 谁抽过奖
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


class Role(models.Model):
    # 用户角色映射
    ROLE_CHOICE = [
        ('visitors', '浏览者'),
        ('lucky_draw', '抽奖者'),
        ('judges', '评委'),
        ('senior_judges', '高级评委'),
        ('poster_manager', '海报管理者'),
        ('admin', '管理员'),
    ]
    # 这里我们定义一个主键id，默认值为一个uuid序列
    id = models.UUIDField(default=uuid4, primary_key=True)
    # 角色名称
    name = models.CharField(choices=ROLE_CHOICE, default='visitors', max_length=64)
    # 限制人数，如果为0，则不限制
    amount = models.IntegerField(default=0)


class Grade(models.Model):
    # 这里我们定义一个主键id，默认值为一个uuid序列
    id = models.UUIDField(default=uuid4, primary_key=True)
    # 学院名
    college = models.CharField(max_length=256, null=False, blank=False)
    # 专业名
    major = models.CharField(max_length=256, null=False, blank=False)
    # 获胜海报数量
    poster_number = models.IntegerField(default=1)
