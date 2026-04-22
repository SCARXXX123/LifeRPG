import os
import json
import datetime
from peewee import *

# 自动定位到项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "storage.db")
db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class UserConfig(BaseModel):
    key = CharField(unique=True)
    value = TextField()
    is_active = BooleanField(default=True)


class Hero(BaseModel):
    name = CharField(unique=True)
    career = CharField(default="UNIDENTIFIED_SUBJECT")
    password = CharField(null=True)  # 新增：存储登录密码
    # --- AI 生成的双重评语系统 ---
    # 1. 详细的行为审计报告 (Brief_Audit_Report)
    status_summary = TextField(default="WAITING_FOR_NEURAL_LINK...")
    # 2. 短促的系统点评 (System_Commentary)
    system_comment = CharField(default="SYSTEM_MONITORING_ACTIVE")

    level = IntegerField(default=1)
    exp = IntegerField(default=0)

    # 六维属性 (0-20 范围，适配你的雷达图)
    intellect = IntegerField(default=10)
    charm = IntegerField(default=10)
    energy = IntegerField(default=10)
    strength = IntegerField(default=10)
    resilience = IntegerField(default=10)
    wealth = IntegerField(default=10)

    last_update = DateTimeField(default=datetime.datetime.now)




class Skill(BaseModel):
    hero = ForeignKeyField(Hero, backref='skills', on_delete='CASCADE')
    name = CharField()
    level = IntegerField(default=1)
    exp_percent = IntegerField(default=0)
    # 对应 JS 中的状态：进化/维持/衰退/觉醒
    status = CharField(default="维持")


class DailyRecord(BaseModel):
    """
    存储每日审计后的结构化结算
    """
    hero = ForeignKeyField(Hero, backref='records')
    date = DateField(default=datetime.date.today)

    # 结算核心
    insight = CharField()  # AI 提取的当日核心洞察 (e.g. "今日数据量化过度，神经递质处于低谷")
    tags = CharField()  # 行为标签: "STATISTICS, CODING, BURMESE_LEARNING"
    summary = TextField()  # 当日详细行为审计
    # 存储 JSON 格式的数据
    # e.g. {"intellect": +1, "energy": -2}
    attribute_changes = TextField(default="{}")

    # AW 原始统计概览 (e.g. {"coding": "3h 20m", "browsing": "1h 10m"})
    activity_snapshot = TextField(null=True)


def init_db():
    db.connect(reuse_if_open=True)
    # 关键：必须把 Skill 和所有你定义的类都放进去
    db.create_tables([UserConfig, Hero, Skill, DailyRecord])
    db.close()
    print(f">>> [DATABASE] 数据库初始化成功: {DB_PATH}")