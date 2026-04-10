from .config import engine, Base
from .models import Book, Chapter

# 创建所有表结构
def init_db():
    Base.metadata.create_all(bind=engine)
    print("数据库表结构创建成功")

if __name__ == "__main__":
    init_db()
