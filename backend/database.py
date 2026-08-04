"""
数据库连接和操作工具

优化记录：
- datetime.utcnow → datetime.now(timezone.utc)，修复 Python 3.12+ 弃用
- get_db() 移除无意义的 finally: pass
- status_map 提取为 HistoryManager 类级常量
- 数据库连接配置代码增加结构化注释
"""

from sqlalchemy import create_engine, and_, or_, text
from sqlalchemy.orm import sessionmaker, Session
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
# Load environment variables from backend/.env (if present) so DATABASE_URL set in .env is available
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
import logging

from models import Base, User, History

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量获取数据库URL
DATABASE_URL = os.getenv("DATABASE_URL")

# 支持备用数据库URL（当主数据库不可用时使用）
DATABASE_URL_BACKUP = os.getenv("DATABASE_URL_BACKUP")

# 如果 DATABASE_URL 未设置，尝试从 Railway 的独立 MYSQL 环境变量构建
if not DATABASE_URL:
    mysql_host = os.getenv("MYSQLHOST")
    mysql_port = os.getenv("MYSQLPORT", "3306")
    mysql_user = os.getenv("MYSQLUSER", "root")
    mysql_password = os.getenv("MYSQLPASSWORD", "")
    mysql_database = os.getenv("MYSQLDATABASE", "railway")
    
    if mysql_host and mysql_password:
        DATABASE_URL = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        logger.info(f"从独立环境变量构建 MySQL DSN: {mysql_host}:{mysql_port}/{mysql_database}")
    else:
        logger.warning("DATABASE_URL 环境变量未设置，使用SQLite作为备用")
        DATABASE_URL = "sqlite:///terrainav.db"
else:
    # 隐藏密码信息，只显示主机和端口
    if '@' in DATABASE_URL:
        parts = DATABASE_URL.split('@')
        host_part = parts[1] if len(parts) > 1 else parts[0]
        logger.info(f"主数据库: {host_part}")
    else:
        logger.info(f"主数据库: {DATABASE_URL}")

# 处理MySQL连接URL（如果使用mysql://，替换为mysql+pymysql://）
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    logger.info("检测到MySQL数据库，使用pymysql驱动")

# 处理PostgreSQL连接URL（如果使用postgres://，替换为postgresql://）
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("检测到PostgreSQL数据库，使用postgresql驱动")

# 处理备用数据库URL
if DATABASE_URL_BACKUP:
    if DATABASE_URL_BACKUP.startswith("mysql://"):
        DATABASE_URL_BACKUP = DATABASE_URL_BACKUP.replace("mysql://", "mysql+pymysql://", 1)
    
    if '@' in DATABASE_URL_BACKUP:
        parts = DATABASE_URL_BACKUP.split('@')
        host_part = parts[1] if len(parts) > 1 else parts[0]
        logger.info(f"备用数据库: {host_part}")

# 创建数据库引擎
from sqlalchemy.exc import OperationalError

def create_database_engine(url):
    """创建数据库引擎"""
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)

def test_database_connection(engine):
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

# 尝试连接主数据库
engine = None
connection_successful = False

if DATABASE_URL and not DATABASE_URL.startswith("sqlite://"):
    engine = create_database_engine(DATABASE_URL)
    
    if test_database_connection(engine):
        logger.info("主数据库连接成功")
        connection_successful = True
    else:
        logger.warning("主数据库连接失败")
        
        # 尝试备用数据库
        if DATABASE_URL_BACKUP:
            logger.info("尝试连接备用数据库...")
            engine = create_database_engine(DATABASE_URL_BACKUP)
            
            if test_database_connection(engine):
                logger.info("备用数据库连接成功")
                connection_successful = True
                DATABASE_URL = DATABASE_URL_BACKUP
            else:
                logger.error("备用数据库连接也失败")

# 如果所有远程数据库都失败，降级到SQLite
if not connection_successful:
    logger.warning("无法连接到远程数据库，降级使用本地SQLite数据库")
    DATABASE_URL = "sqlite:///terrainav.db"
    engine = create_database_engine(DATABASE_URL)
    logger.warning("已切换到SQLite数据库")

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise


def get_db() -> Session:
    """【优化】获取数据库会话，调用方负责关闭"""
    return SessionLocal()


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.db = get_db()

    def close(self):
        """关闭数据库连接"""
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class UserManager:
    """用户管理器"""

    @staticmethod
    def create_user(username: str, email: str, password: str, usertype: str = "user") -> Optional[User]:
        """创建新用户"""
        db = get_db()
        try:
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()
            
            if existing_user:
                logger.warning(f"用户名或邮箱已存在: {username}/{email}")
                return None

            # 创建新用户
            password_hash = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                usertype=usertype
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"用户创建成功: {username}")
            return new_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建用户失败: {e}")
            return None
        finally:
            db.close()

    # 【测试用】硬编码管理员账户 — 无需数据库即可登录
    # 用户名: admin  密码: 123456
    # 部署到生产环境前请删除或注释此配置
    HARDCODED_ADMIN = {
        "username": "admin",
        "password": "123456",
        "usertype": "admin",
        "email": "admin@terrainav.local",
    }

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """验证用户登录

        优先检查硬编码的测试管理员账户（无需数据库），
        数据库不可用时 admin 仍可登录。
        """
        # 【测试快捷通道】硬编码管理员 — 不依赖数据库
        admin_cfg = UserManager.HARDCODED_ADMIN
        if username == admin_cfg["username"] and password == admin_cfg["password"]:
            logger.info(f"[硬编码管理员] 登录成功: {username}")
            # 构造一个不绑定数据库 session 的 User 对象
            admin_user = User(
                id=-1,  # 特殊 ID 标识这是离线管理员
                username=admin_cfg["username"],
                email=admin_cfg["email"],
                password_hash="__hardcoded__",
                usertype=admin_cfg["usertype"],
            )
            return admin_user

        # 正常数据库验证
        db = get_db()
        try:
            user = db.query(User).filter(User.username == username).first()

            if user and check_password_hash(user.password_hash, password):
                logger.info(f"用户登录成功: {username}")
                return user
            else:
                logger.warning(f"用户登录失败: {username}")
                return None

        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            # 数据库不可用时，非 admin 用户无法登录
            return None
        finally:
            db.close()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        db = get_db()
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """根据用户名获取用户"""
        db = get_db()
        try:
            return db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def update_user(user_id: int, **kwargs) -> Optional[User]:
        """更新用户信息"""
        db = get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                db.commit()
                db.refresh(user)
                logger.info(f"用户信息更新成功: {user_id}")
                return user
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"更新用户失败: {e}")
            return None
        finally:
            db.close()


class HistoryManager:
    """历史记录管理器"""

    # 【优化】状态映射提取为类级常量，避免每次调用时重新创建
    STATUS_MAP = {
        "completed": ("success", "完成"),
        "processing": ("processing", "处理中"),
        "failed": ("failed", "失败"),
        "pending": ("pending", "待处理"),
    }

    @staticmethod
    def create_history(
        user_id: int,
        task_name: str,
        description: str = "",
        input_image_url: str = "",
        heatmap_url: str = "",
        route_url: str = "",
        report_url: str = "",
        task_status: str = "completed",
        task_time: Optional[datetime] = None
    ) -> Optional[History]:
        """创建历史记录"""
        db = get_db()
        try:
            new_history = History(
                user_id=user_id,
                task_name=task_name,
                description=description,
                input_image_url=input_image_url,
                heatmap_url=heatmap_url,
                route_url=route_url,
                report_url=report_url,
                task_status=task_status,
                task_time=task_time or datetime.now(timezone.utc)  # 【优化】timezone-aware
            )
            
            db.add(new_history)
            db.commit()
            db.refresh(new_history)
            
            logger.info(f"历史记录创建成功: {task_name}")
            return new_history
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建历史记录失败: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_user_histories(user_id: int, limit: int = 20) -> List[History]:
        """获取用户的历史记录"""
        db = get_db()
        try:
            histories = db.query(History).filter(
                History.user_id == user_id
            ).order_by(History.created_at.desc()).limit(limit).all()
            
            return histories
            
        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def get_history_by_id(history_id: int) -> Optional[History]:
        """根据ID获取历史记录"""
        db = get_db()
        try:
            return db.query(History).filter(History.id == history_id).first()
        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def delete_history(history_id: int) -> bool:
        """删除历史记录"""
        db = get_db()
        try:
            history = db.query(History).filter(History.id == history_id).first()
            if history:
                db.delete(history)
                db.commit()
                logger.info(f"历史记录删除成功: {history_id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"删除历史记录失败: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_recent_histories(user_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        """获取最近的历史记录（用于首页展示）"""
        db = get_db()
        try:
            histories = db.query(History).filter(
                History.user_id == user_id
            ).order_by(History.created_at.desc()).limit(limit).all()
            
            result = []
            for h in histories:
                actual_status = h.task_status or "completed"
                status_key, status_text = HistoryManager.STATUS_MAP.get(
                    actual_status, ("success", "完成")
                )  # 【优化】使用类级常量，避免每次循环都创建字典
                result.append({
                    "id": h.id,
                    "name": h.task_name,
                    "time": h.created_at.strftime("%Y-%m-%d %H:%M") if h.created_at else "",
                    "image": h.input_image_url or "/pictures/background1.jpg",
                    "status": status_key,
                    "statusText": status_text,
                    "thumbnail": h.input_image_url or "/pictures/background1.jpg",
                    "description": h.description or "巡逻路线分析任务",
                    "heatmap_url": h.heatmap_url,
                    "route_url": h.route_url
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取最近历史记录失败: {e}")
            return []
        finally:
            db.close()