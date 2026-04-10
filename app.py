import streamlit as st
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.crud import get_books, get_book, get_chapters_by_book, get_chapter_by_number
from src.db.init_db import init_db
from src.db.config import get_db
from src.workflow.workflow import NovelWriteWorkflow

# 初始化数据库
init_db()

# 初始化工作流
workflow = NovelWriteWorkflow()

# 设置页面配置
st.set_page_config(
    page_title="Novel Write",
    page_icon="📚",
    layout="wide"
)

# 侧边栏
st.sidebar.title("Novel Write")
st.sidebar.markdown("### AI小说写作系统")
st.sidebar.markdown("使用AI辅助创作网络小说")

if st.sidebar.button("我的书籍", type="primary"):
    st.session_state.page = "books"

if st.sidebar.button("创建新书"):
    st.session_state.page = "create_book"

# 主页面逻辑
if 'page' not in st.session_state:
    st.session_state.page = "books"

if st.session_state.page == "books":
    st.title("我的书籍")
    
    # 获取所有书籍
    books = get_books(next(get_db()))
    
    if not books:
        st.warning("还没有创建书籍，点击侧边栏的'创建新书'按钮开始创建")
    else:
        for book in books:
            with st.expander(f"{book.title} - {book.genre}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**平台**: {book.platform}")
                    st.markdown(f"**目标章节**: {book.target_chapters}章")
                    st.markdown(f"**每章字数**: {book.chapter_words}字")
                    st.markdown(f"**创建时间**: {book.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                with col2:
                    if st.button(f"查看详情", key=f"view_{book.id}"):
                        st.session_state.page = "book_detail"
                        st.session_state.book_id = book.id

elif st.session_state.page == "create_book":
    st.title("创建新书")
    
    with st.form("create_book_form"):
        title = st.text_input("书名")
        genre = st.selectbox("类型", ["玄幻", "仙侠", "都市", "科幻", "恐怖", "悬疑", "言情"])
        platform = st.selectbox("平台", ["起点中文网", "番茄小说", "纵横中文网", "创世中文网"])
        chapter_words = st.number_input("每章字数", min_value=1000, max_value=10000, value=3000)
        target_chapters = st.number_input("目标章节", min_value=10, max_value=1000, value=100)
        outline = st.text_area("小说大纲", height=200)
        writing_style = st.text_area("写作风格参考", height=100)
        external_context = st.text_area("外部指令", height=100)
        
        if st.form_submit_button("创建"):
            if not title:
                st.error("请输入书名")
            else:
                # 构建书籍数据
                book_data = {
                    'title': title,
                    'genre': genre,
                    'platform': platform,
                    'chapter_words': chapter_words,
                    'target_chapters': target_chapters,
                    'outline': outline
                }
                
                # 调用工作流创建书籍
                with st.spinner("正在生成基础设定..."):
                    result = workflow.create_book(book_data, external_context)
                
                if 'error' in result:
                    st.error(f"创建失败: {result['error']}")
                else:
                    st.success("书籍创建成功！")
                    st.session_state.page = "books"
                    st.rerun()

elif st.session_state.page == "book_detail":
    book_id = st.session_state.book_id
    book = get_book(next(get_db()), book_id)
    
    if not book:
        st.error("书籍不存在")
    else:
        st.title(book.title)
        
        # 标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["基本信息", "章节管理", "大纲管理", "状态管理", "MD文件管理"])
        
        with tab1:
            st.markdown(f"**类型**: {book.genre}")
            st.markdown(f"**平台**: {book.platform}")
            st.markdown(f"**目标章节**: {book.target_chapters}章")
            st.markdown(f"**每章字数**: {book.chapter_words}字")
            st.markdown(f"**创建时间**: {book.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**最后更新**: {book.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
        with tab2:
            st.markdown("### 章节管理")
            
            # 获取所有章节
            chapters = get_chapters_by_book(next(get_db()), book_id)
            
            if not chapters:
                st.warning("还没有章节，点击下方按钮开始续写第一章")
            else:
                for chapter in chapters:
                    with st.expander(f"第{chapter.chapter_number}章 - {chapter.title}"):
                        st.markdown(f"**字数**: {chapter.word_count}字")
                        st.markdown(f"**审核分数**: {chapter.audit_score or 0:.2f}")
                        st.markdown(f"**连续性分数**: {chapter.continuity_score or 0:.2f}")
                        st.markdown(f"**创建时间**: {chapter.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        if st.button(f"修改章节", key=f"edit_chapter_{chapter.id}"):
                            st.session_state.page = "edit_chapter"
                            st.session_state.book_id = book_id
                            st.session_state.chapter_num = chapter.chapter_number
            
            # 续写下一章
            next_chapter = len(chapters) + 1
            
            # 初始化session state
            if '续写中' not in st.session_state:
                st.session_state['续写中'] = False
            
            if not st.session_state['续写中']:
                if st.button(f"续写下一章（第{next_chapter}章）", type="primary"):
                    st.session_state['续写中'] = True
                    st.session_state['next_chapter'] = next_chapter
                    st.rerun()
            else:
                next_chapter = st.session_state['next_chapter']
                external_context = st.text_input("外部指令（可选）")
                if st.button("确认续写"):
                    with st.spinner(f"正在续写第{next_chapter}章..."):
                        result = workflow.continue_chapter(book_id, next_chapter, external_context)
                    
                    if 'error' in result:
                        st.error(f"续写失败: {result['error']}")
                    else:
                        st.success(f"第{next_chapter}章续写成功！")
                    
                    # 重置状态
                    st.session_state['续写中'] = False
                    st.rerun()
        
        with tab3:
            st.markdown("### 大纲管理")
            
            current_outline = book.outline
            new_outline = st.text_area("修改大纲", value=current_outline, height=300)
            
            if st.button("保存大纲", type="primary"):
                result = workflow.update_outline(book_id, new_outline)
                if 'error' in result:
                    st.error(f"修改失败: {result['error']}")
                else:
                    st.success("大纲修改成功！")
                    st.rerun()
        
        with tab4:
            st.markdown("### 状态管理")
            
            if book.current_state:
                st.markdown("**当前状态**")
                st.markdown(book.current_state)
            else:
                st.info("当前状态未设置")
            
            if book.pending_hooks:
                st.markdown("**伏笔池**")
                st.markdown(book.pending_hooks)
            else:
                st.info("伏笔池未设置")
        
        with tab5:
            st.markdown("### MD文件管理")
            
            # 显示设定文件
            st.markdown("#### 设定文件")
            
            if book.story_bible:
                with st.expander("故事圣经"):
                    st.markdown(book.story_bible)
            else:
                st.info("故事圣经未设置")
            
            if book.volume_outline:
                with st.expander("卷纲"):
                    st.markdown(book.volume_outline)
            else:
                st.info("卷纲未设置")
            
            if book.book_rules:
                with st.expander("书籍规则"):
                    st.markdown(book.book_rules)
            else:
                st.info("书籍规则未设置")
            
            # 显示状态文件
            st.markdown("#### 状态文件")
            
            if book.subplot_board:
                with st.expander("支线进度板"):
                    st.markdown(book.subplot_board)
            else:
                st.info("支线进度板未设置")
            
            if book.emotional_arcs:
                with st.expander("情感弧线"):
                    st.markdown(book.emotional_arcs)
            else:
                st.info("情感弧线未设置")
            
            if book.character_matrix:
                with st.expander("角色交互矩阵"):
                    st.markdown(book.character_matrix)
            else:
                st.info("角色交互矩阵未设置")

elif st.session_state.page == "edit_chapter":
    book_id = st.session_state.book_id
    chapter_num = st.session_state.chapter_num
    
    book = get_book(next(get_db()), book_id)
    chapter = get_chapter_by_number(next(get_db()), book_id, chapter_num)
    
    if not chapter:
        st.error("章节不存在")
    else:
        st.title(f"修改第{chapter_num}章")
        
        new_content = st.text_area("章节内容", value=chapter.content, height=500)
        
        if st.button("保存修改", type="primary"):
            result = workflow.update_chapter(book_id, chapter_num, new_content)
            if 'error' in result:
                st.error(f"修改失败: {result['error']}")
            else:
                st.success("章节修改成功！")
                st.session_state.page = "book_detail"
                st.rerun()

# 导入get_db函数
from src.db.config import get_db

# 日志输出台
def show_logs():
    """显示日志输出台"""
    st.markdown("## 日志输出台")
    
    # 获取今天的日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 日志目录
    log_dir = "logs"
    
    if os.path.exists(log_dir):
        # 显示Agent日志
        agent_log_file = os.path.join(log_dir, f"agent_{today}.log")
        if os.path.exists(agent_log_file):
            with st.expander("Agent日志"):
                with open(agent_log_file, 'r', encoding='utf-8') as f:
                    logs = f.read()
                st.text_area("Agent日志", value=logs, height=300)
        else:
            st.info("今天还没有Agent日志")
        
        # 显示Workflow日志
        workflow_log_file = os.path.join(log_dir, f"workflow_{today}.log")
        if os.path.exists(workflow_log_file):
            with st.expander("工作流日志"):
                with open(workflow_log_file, 'r', encoding='utf-8') as f:
                    logs = f.read()
                st.text_area("工作流日志", value=logs, height=300)
        else:
            st.info("今天还没有工作流日志")
    else:
        st.info("日志目录不存在")

# 显示日志输出台
show_logs()
