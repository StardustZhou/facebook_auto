#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Charles on 19-3-16
# Function: 任务调度模块相关表结构定义, 可通过执得本脚本在数据库中直接创建或删除表


from sqlalchemy import (
    Column, Integer, String, DateTime, Table, ForeignKey)
from sqlalchemy.orm import relationship
from db.basic import Base, engine


class User(Base):
    __tablename__ = 'user'
    __table_args__ = {"useexisting": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    # account = Column(String(255), unique=True)
    # password = Column(String(255))
    # name = Column(String(255), default='', server_default='')
    category = Column(Integer, ForeignKey('user_category.category'))
    token = Column(String(255), default='', server_default='')
    # 记录该用户可以创建的[任务类型id]列表(TaskCategory.id), 以分号分割"1;2;3", 默认为空,代表可以创建所有类型的任务
    enable_tasks = Column(String(255), default='', server_default='')


class UserCategory(Base):
    __tablename__ = 'user_category'
    # 用户身份,1-普通用户,2-管理员
    category = Column(Integer, primary_key=True)
    name = Column(String(255))  # 类别名称,如普通用户,管理员...
    description = Column(String(255), default='', server_default='')


class Scheduler(Base):
    __tablename__ = 'scheduler'
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 执行模式： 
    # 0-立即执行（只执行一次）, 
    # 1-间隔执行并不立即开始（间隔一定时间后开始执行,并按设定的间隔周期执行下去）, 如果设置了start_date, 则从start_date指定的时间点开始执行 
    # 2-间隔执行,但立即开始（执行多次）
    # 3-定时执行,指定时间执行（执行一次）
    mode = Column(Integer, default=0, server_default='0')
    interval = Column(Integer, default=600, server_default='600')       # 间隔时长, 单位秒

    # 作用有二：
    # 1作为定时间任务的执行时间, 仅mode=3时有效
    # 2作为周期任务的首次启动时间, 仅mode=1时有效
    start_date = Column(DateTime(3))

    # 该任务的终止时间
    end_date = Column(DateTime(3))

    def __repr__(self):
        return "id:{}, mode:{}, interval:{}, start_date:{}, end_date:{}. ".format(
            self.id, self.mode, self.interval, self.start_date, self.end_date)


task_account_group_table = Table(
    'task_account_group', Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('task_id', Integer, ForeignKey("task.id")),
    Column('account_id', Integer, ForeignKey("account.id"))
)


class TaskAccountGroup(Base):
    __table__ = task_account_group_table


class TaskCategory(Base):
    """
    任务类型表
    """
    __tablename__ = 'task_category'
    # 1--fb自动养账号, 2-fb刷广告好评, 3- fb仅登录浏览, 4- fb点赞, 5- fb发表评论, 6- fb post状态, 7- fb 聊天, 8- fb 编辑个人信息, 未完待续...
    category = Column(Integer, primary_key=True)
    name = Column(String(255))

    processor = Column(String(255))  # 任务的处理函数名, 不能为空, 代码逻辑中将依赖这个函数名进行任务分发
    configure = Column(String(2048), default='', server_default='')    # 每种任务类型的配置参数, 形如：name:title:type(bool/int/float/str):default[:option1[|option2[|optionN]] [\r\n(new line)]
    description = Column(String(2048), default='', server_default='')


class Task(Base):
    """
    任务表, 对用户层承现
    """
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), default='', server_default='')

    # 任务类型, 0-养账号,1-刷好评,其他待续
    category = Column(Integer, ForeignKey('task_category.category'))

    # 任务的创建者
    creator = Column(Integer, ForeignKey('user.id'))

    # 任务调度规则
    scheduler = Column(Integer, ForeignKey('scheduler.id'))

    # 一个任务同时占用多个账号
    accounts = relationship('Account',
                            secondary=task_account_group_table)  # ,
    # back_populates='parents')

    # 任务状态, -1-pending, 0-failed, 1-succeed, 2-running, 3-pausing, new-新建,还没处理, cancelled--取消了
    # status = Column(Integer, default=-1, server_default='-1')
    # 任务状态改用字符串是为了直观, 避免前后端转换的麻烦
    status = Column(String(100), default='new', server_default='new')

    # 该任务最大执行次数（即成功的job次数）,比如刷分,可以指定最大刷多少次
    limit_counts = Column(Integer, default=1, server_default='1')

    # 该task成功、失败的次数（针对周期性任务）
    succeed_counts = Column(Integer, default=0, server_default='0')

    failed_counts = Column(Integer, default=0, server_default='0')

    # 第一次真正启动的时间
    start_time = Column(DateTime(3), default=None)

    # 实际结束时间
    end_time = Column(DateTime(3), default=None)


    # 该任务需要的账号数量
    accounts_num = Column(Integer, default=0, server_default='0')

    # 该任务实际使用的账号数量(会有账号不可用
    real_accounts_num = Column(Integer, default=0, server_default='0')

    result = Column(String(2048), default='', server_default='')

    # 这个是在APScheduler中调度时的任务id 用以暂停、恢复、取消任务# 这个是在APScheduler中调度时的任务id
    aps_id = Column(String(255), default='', server_default='')

    # 这里保存任务的额外信息,以json字符形式保存,如post内容, 点赞规则, ads_code, keep time, 目标站点等
    configure = Column(String(2048), default='', server_default='')

    # 最后一次更新的时间戳
    last_update = Column(DateTime(3), default=None)

    def accounts_list(self):
        return [acc.account for acc in self.accounts]

    def __repr__(self):
        return "id:{}, name:{}, category:{}, status:{}, creator:{}, scheduler:{}, accounts:{}, description:{}, " \
               "errors:{}. ".format(self.id, self.name, self.category, self.status, self.creator, self.scheduler,
                                    self.accounts_list(), self.configure, self.result)


class Job(Base):
    """
    每一个task都将被分解成多个job, 一个job才是真正的可执行单元
    """
    __tablename__ = 'job'
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 一个任务加一个唯一的account构成一个job
    task = Column(Integer, ForeignKey('task.id'))
    account = Column(Integer, ForeignKey('account.id'))

    # 这个任务被分配到了哪个地域上（即队列上）,用以计算地域的负载
    area = Column(Integer, ForeignKey('area.id'), default=None, comment=u'这个任务被分配到了哪个地域上（即队列上）,用以计算地域的负载')

    # -1-pending, 0-failed, 1-succeed, 2-running
    # status = Column(Integer, default=-1, server_default='-1')
    status = Column(String(100), default='pending', server_default='pending')

    # 这个job执行时被分配的id,用以在结果队列中跟踪job执行情况
    track_id = Column(String(255), default='', server_default='', unique=True)

    start_time = Column(DateTime(3))
    end_time = Column(DateTime(3))

    # job执行函数的返回值
    result = Column(String(2048), default='', server_default='')
    traceback = Column(String(2048), default='', server_default='')

    def dict2Job(self, job_dict):
        for k, v in job_dict.items():
            if hasattr(self, k):
                setattr(self, k, v)
        return self

    def __repr__(self):
        return "id:{}, task:{}, account:{}, start_time:{}, status:{}, result:{}. ".format(
            self.id, self.task, self.account, self.start_time, self.status, self.result)


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 该账号所属类别,该账号所属类别,1--facebook账号,2--twitter账号, 3--Ins账号
    category = Column(Integer, ForeignKey('account_category.category'))

    # 每个账号都应该隶属于某个人员,以方便权限管理
    owner = Column(Integer, ForeignKey('user.id'))
    account = Column(String(255))
    password = Column(String(255))
    # -----------------以上是必填项----------------

    email = Column(String(255), default='', server_default='')
    email_pwd = Column(String(255), default='', server_default='')
    phone_number = Column(String(100), default='', server_default='')

    # 0-女,1-男
    gender = Column(Integer, default=0, server_default='0')
    # 生日格式"1990-3-21"
    birthday = Column(String(100), default='', server_default='')
    national_id = Column(String(100), default='', server_default='')
    register_time = Column(String(100), default='', server_default='')
    name = Column(String(100), default='', server_default='')
    profile_id = Column(String(100), default='', server_default='')

    # 0-valid, 1-invalid, 2-verifying, 3-other
    status = Column(String(100), default='valid', server_default='valid')

    # 是否正在被某任务使用 0-未使用, 大于1代表正在被使用,数字代表并发使用数
    using = Column(Integer, default=0, server_default='0')

    # 记录该用户可以创建的[任务类型id]列表(TaskCategory.id), 以分号分割"1;2;3", 默认为空,代表可以创建所有类型的任务
    enable_tasks = Column(String(255), default='', server_default='')

    # 存放用户profile文件
    profile_path = Column(String(255), default='', server_default='')

    # last_login = Column(DateTime(3))
    # last_post = Column(DateTime(3))
    # last_chat = Column(DateTime(3))
    # last_farming = Column(DateTime(3))
    # last_comment = Column(DateTime(3))
    # last_edit = Column(DateTime(3))

    # active_ip = Column(String(255), default='', server_default='')
    # 活跃地域
    # active_area = Column(String(255), default='', server_default='')
    active_area = Column(Integer, ForeignKey('area.id'), default=None)
    # 常用浏览器指纹
    active_browser = Column(Integer, ForeignKey('finger_print.id'), default=None)
    # 一个账号有可能同是被多个任务占用,逻辑上是可以的, 但实际操作上应该尽量避免此种情况,以规避多IP同时登录带来的封号风险
    tasks = relationship("Task", secondary=task_account_group_table)  # ,back_populates='children')

    # 账号的其他非常规配置信息,json串
    configure = Column(String(4096), default='', server_default='')
    last_update = Column(DateTime(3), default=None)

    def __repr__(self):
        return "id:{}, account:{}, password:{}, email={}, email_pwd:{}, gender:{}, birthday:{}, national_id:{}, " \
               "register_time:{}, name:{}, profile_id:{}, status:{}, owner:{}, profile_path:{}. configure={}".format(
                   self.id, self.account, self.password, self.email, self.email_pwd, self.gender, self.birthday,
                   self.national_id, self.register_time, self.name, self.profile_id, self.status, self.owner, self.profile_path, self.configure)


class AccountCategory(Base):
    """
    账号类型表
    """
    __tablename__ = 'account_category'
    # 该账号所属类别,1--facebook账号,2--twitter账号, 3--Ins账号
    category = Column(Integer, primary_key=True)
    name = Column(String(255), default='', server_default='')


class Agent(Base):
    __tablename__ = 'agent'
    id = Column(Integer, primary_key=True, autoincrement=True)

    # # 该agent绑定的任务队列, job将根据与其最亲近的agent的queue名来被分发, 通常队列名与area相同
    # queue_name = Column(String(255), default='', server_default='')

    # 0-idle, 1-normal, 2-busy, 3-disable
    # -1--disable, 大于零代表其忙碌值（即当前待处理的任务量）
    # status = Column(String(20), default=0, server_default='0')
    # status = Column(Integer, default=0, server_default='0')   # 一个地域上可能有多个agent，无法确定每个agent上的任务数

    # 该agent所属区域
    active_area = Column(Integer, ForeignKey('area.id'), default=None)

    # 该agent的配置信息
    configure = Column(String(2048), default='', server_default='')


class FingerPrint(Base):
    __tablename__ = 'finger_print'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), default='', server_default='')
    value = Column(String(2048), default='', server_default='')


class Area(Base):
    __tablename__ = 'area'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    running_tasks = Column(Integer, default=0, server_default='0', comment=u'该地域正在运行的任务个数')  # 该地域正在运行的任务数
    description = Column(String(2048), default='', server_default='')


if __name__ == '__main__':
    while True:
        res = input("What do you want to do, create or drop? \n")
        if res == 'drop':
            res = input("Are you sure? \n")
            if res.lower().startswith('y'):
                Base.metadata.drop_all(engine)
            break
        elif res == 'create':
            Base.metadata.create_all(engine)
            break
        elif res == 'exit':
            break
        else:
            pass

    print("finished.")
