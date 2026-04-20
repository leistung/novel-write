from .config import engine, Base
from .models import Book, Chapter
from sqlalchemy import inspect

# 创建所有表结构
def init_db():
    # 检查是否已经存在表结构
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 检查是否需要创建表
    if not existing_tables:
        Base.metadata.create_all(bind=engine)
        print("数据库表结构创建成功")

if __name__ == "__main__":
    init_db()
