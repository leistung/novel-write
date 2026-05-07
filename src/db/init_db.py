from .config import engine, Base
from .models import Book, Chapter
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

# 创建所有表结构
def init_db():
    # 检查是否已经存在表结构
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 检查是否需要创建表
    if not existing_tables:
        Base.metadata.create_all(bind=engine)
        print("数据库表结构创建成功")
    else:
        Base.metadata.create_all(bind=engine)
        _ensure_chapter_unique_index()


def _ensure_chapter_unique_index():
    index_name = "uq_chapters_book_chapter_number"
    inspector = inspect(engine)
    if "chapters" not in inspector.get_table_names():
        return

    indexes = inspector.get_indexes("chapters")
    if any(index.get("name") == index_name for index in indexes):
        return

    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
                "ON chapters (book_id, chapter_number)"
            )
    except SQLAlchemyError as exc:
        print(f"章节唯一索引创建失败，可能已有重复章节，请清理后重试: {exc}")

if __name__ == "__main__":
    init_db()
