import os

from APP.functions import get_db_uri

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

templates_dir = os.path.join(BASE_DIR, 'templates')

static_dir = os.path.join(BASE_DIR, 'static')

upload_dir = os.path.join(static_dir, 'media/ava')

DATABASE = {
    # 用户
    'USER': 'root',
    # 主机
    'HOST': '127.0.0.1',
    # 密码
    'PASSWORD': 'admin123',
    # 端口
    'PORT': '3306',
    # 数据库类型
    'DB': 'mysql',
    # 数据库驱动
    'DRIVER': 'pymysql',
    # 使用的数据库
    'NAME': 'csms',
}

SQLALCHEMY_DATABASE_URI = get_db_uri(DATABASE)
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_POOL_TIMEOUT = 20
SQLALCHEMY_POOL_RECYCLE = 60
SQLALCHEMY_MAX_OVERFLOW = 5

redisInfo = {
    'host': '127.0.0.1',
    'password': 'admin123',
    'port': 6379,
    'db': 0
}


