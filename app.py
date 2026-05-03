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
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    /* 全局样式 */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #3498db;
        --accent-color: #9b59b6;
        --background-color: #f8f9fa;
        --card-background: #ffffff;
        --text-color: #333333;
        --border-color: #e0e0e0;
        --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        --shadow-hover: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    
    body {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* 卡片样式 */
    .card {
        background-color: var(--card-background);
        border-radius: 10px;
        box-shadow: var(--shadow);
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        box-shadow: var(--shadow-hover);
        transform: translateY(-5px);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background-color: var(--secondary-color);
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-color);
        transform: translateY(-2px);
        box-shadow: var(--shadow);
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3, .css-1d391kg p {
        color: white !important;
    }
    
    /* 标题样式 */
    h1, h2, h3, h4 {
        color: var(--primary-color);
        font-weight: bold;
    }
    
    /* 标签页样式 */
    .css-1h90xlt {
        border-bottom: 2px solid var(--border-color);
    }
    
    .css-1y4p8pa {
        color: var(--primary-color) !important;
        font-weight: bold;
    }
    
    /* 表单样式 */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid var(--border-color);
        padding: 8px 12px;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--secondary-color);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-color);
    }
    
    /* 分隔线样式 */
    hr {
        border: 1px solid var(--border-color);
        margin: 20px 0;
    }
    
    /* 提示框样式 */
    .stAlert {
        border-radius: 8px;
        box-shadow: var(--shadow);
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.title("📚 Novel Write")
    st.markdown("### AI小说写作系统")
    st.markdown("使用AI辅助创作网络小说")
    st.markdown("---")
    
    # 导航按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 我的书籍", use_container_width=True, type="primary"):
            st.session_state.page = "books"
            st.rerun()
    with col2:
        if st.button("✏️ 创建新书", use_container_width=True):
            st.session_state.page = "create_book"
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 快速访问")
    if st.button("📋 日志输出", use_container_width=True):
        st.session_state.page = "logs"
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 关于")
    st.markdown("版本: 1.0.0")
    st.markdown("© 2026 Novel Write")

# 主页面逻辑
if 'page' not in st.session_state:
    st.session_state.page = "books"

if st.session_state.page == "books":
    st.title("我的书籍")
    st.markdown("---")
    
    # 获取所有书籍
    books = get_books(next(get_db()))
    
    if not books:
        with st.container():
            st.info("还没有创建书籍，点击侧边栏的'创建新书'按钮开始创建")
    else:
        # 使用网格布局显示书籍
        cols = st.columns(3)
        for i, book in enumerate(books):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"### {book.title}")
                    st.markdown(f"**类型**: {book.genre}")
                    st.markdown(f"**平台**: {book.platform}")
                    st.markdown(f"**目标章节**: {book.target_chapters}章")
                    st.markdown(f"**每章字数**: {book.chapter_words}字")
                    st.markdown(f"**创建时间**: {book.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    if st.button(f"进入详情", key=f"view_{book.id}", use_container_width=True, type="primary"):
                        st.session_state.page = "book_detail"
                        st.session_state.book_id = book.id
                        st.rerun()
                st.markdown("---")

elif st.session_state.page == "create_book":
    st.title("创建新书")
    st.markdown("---")
    
    with st.container():
        with st.form("create_book_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("书名", placeholder="请输入书名")
                genre = st.selectbox("类型", ["玄幻", "仙侠", "都市", "科幻", "恐怖", "悬疑", "言情"])
                platform = st.selectbox("平台", ["起点中文网", "番茄小说", "纵横中文网", "创世中文网"])
            with col2:
                chapter_words = st.number_input("每章字数", min_value=1000, max_value=10000, value=3000)
                target_chapters = st.number_input("目标章节", min_value=10, max_value=1000, value=100)
            
            outline = st.text_area("小说大纲", height=200, placeholder="请输入小说大纲")
            writing_style = st.text_area("写作风格参考", height=100, placeholder="请输入写作风格参考")
            external_context = st.text_area("外部指令", height=100, placeholder="请输入外部指令")
            
            if st.form_submit_button("创建", use_container_width=True, type="primary"):
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
        # 书籍标题和基本信息
        st.title(book.title)
        st.markdown(f"**类型**: {book.genre} | **平台**: {book.platform}")
        st.markdown(f"**目标章节**: {book.target_chapters}章 | **每章字数**: {book.chapter_words}字")
        st.markdown(f"**创建时间**: {book.created_at.strftime('%Y-%m-%d %H:%M:%S')} | **最后更新**: {book.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown("---")
        
        # 标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 基本信息", "📖 章节管理", "📝 大纲管理", "⚙️ 设定管理", "📊 状态管理"])
        
        with tab1:
            st.markdown("### 基本信息")
            with st.container():
                st.markdown(f"**书名**: {book.title}")
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
                st.info("还没有章节，点击下方按钮开始续写第一章")
            else:
                for chapter in chapters:
                    with st.expander(f"第{chapter.chapter_number}章 - {chapter.title}"):
                        st.markdown(f"**字数**: {chapter.word_count}字")
                        st.markdown(f"**审核分数**: {chapter.audit_score or 0:.2f}")
                        st.markdown(f"**连续性分数**: {chapter.continuity_score or 0:.2f}")
                        st.markdown(f"**创建时间**: {chapter.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"查看章节", key=f"view_chapter_{chapter.id}", use_container_width=True):
                                st.session_state.page = "view_chapter"
                                st.session_state.book_id = book_id
                                st.session_state.chapter_num = chapter.chapter_number
                                st.rerun()
                        with col2:
                            if st.button(f"修改章节", key=f"edit_chapter_{chapter.id}", type="primary", use_container_width=True):
                                st.session_state.page = "edit_chapter"
                                st.session_state.book_id = book_id
                                st.session_state.chapter_num = chapter.chapter_number
                                st.rerun()
            
            # 续写下一章
            next_chapter = len(chapters) + 1
            
            # 初始化session state
            if '续写中' not in st.session_state:
                st.session_state['续写中'] = False
            if '连续续写中' not in st.session_state:
                st.session_state['连续续写中'] = False
            
            if not st.session_state['续写中'] and not st.session_state['连续续写中']:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"续写下一章（第{next_chapter}章）", use_container_width=True, type="primary"):
                        st.session_state['续写中'] = True
                        st.session_state['next_chapter'] = next_chapter
                        st.rerun()
                with col2:
                    chapter_count = st.number_input("连续续写章节数", min_value=2, max_value=10, value=3, key="continue_count")
                    if st.button(f"连续续写 {chapter_count} 章", use_container_width=True):
                        st.session_state['连续续写中'] = True
                        st.session_state['连续续写数量'] = chapter_count
                        st.rerun()
            elif st.session_state['续写中']:
                next_chapter = st.session_state['next_chapter']
                external_context = st.text_input("外部指令（可选）", placeholder="请输入外部指令")
                if st.button("确认续写", use_container_width=True, type="primary"):
                    with st.spinner(f"正在续写第{next_chapter}章..."):
                        result = workflow.continue_chapter(book_id, next_chapter, external_context)
                    
                    if 'error' in result:
                        st.error(f"续写失败: {result['error']}")
                    else:
                        st.success(f"第{next_chapter}章续写成功！")
                    
                    # 重置状态
                    st.session_state['续写中'] = False
                    st.rerun()
                if st.button("取消", use_container_width=True):
                    st.session_state['续写中'] = False
                    st.rerun()
            elif st.session_state['连续续写中']:
                chapter_count = st.session_state['连续续写数量']
                external_context = st.text_input("外部指令（可选）", placeholder="请输入外部指令")
                st.info(f"将连续续写从第{next_chapter}章开始，共{chapter_count}章")
                
                if st.button("确认连续续写", use_container_width=True, type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i in range(chapter_count):
                        current_ch = next_chapter + i
                        status_text.text(f"正在续写第{current_ch}章（{i+1}/{chapter_count}）...")
                        progress_bar.progress((i + 1) / chapter_count)
                        
                        result = workflow.continue_chapter(book_id, current_ch, external_context)
                        
                        if 'error' in result:
                            st.error(f"第{current_ch}章续写失败: {result['error']}")
                            st.session_state['连续续写中'] = False
                            st.rerun()
                            break
                    
                    status_text.text("连续续写完成！")
                    st.success(f"成功连续续写{chapter_count}章！")
                    st.session_state['连续续写中'] = False
                    st.rerun()
                
                if st.button("取消", use_container_width=True):
                    st.session_state['连续续写中'] = False
                    st.rerun()
        
        with tab3:
            st.markdown("### 大纲管理")
            
            current_outline = book.outline
            new_outline = st.text_area("修改大纲", value=current_outline, height=300)
            
            if st.button("保存大纲", use_container_width=True, type="primary"):
                result = workflow.update_outline(book_id, new_outline)
                if 'error' in result:
                    st.error(f"修改失败: {result['error']}")
                else:
                    st.success("大纲修改成功！")
                    st.rerun()
        
        with tab4:
            st.markdown("### 设定管理")
            
            # 显示设定文件
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
        
        with tab5:
            st.markdown("### 状态管理")
            
            # 显示当前状态和伏笔池
            if book.current_state:
                with st.expander("当前状态"):
                    st.markdown(book.current_state)
            else:
                st.info("当前状态未设置")
            
            if book.pending_hooks:
                with st.expander("伏笔池"):
                    st.markdown(book.pending_hooks)
            else:
                st.info("伏笔池未设置")
            
            # 显示动态状态文件
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
        
        if st.button("保存修改", use_container_width=True, type="primary"):
            result = workflow.update_chapter(book_id, chapter_num, new_content)
            if 'error' in result:
                st.error(f"修改失败: {result['error']}")
            else:
                st.success("章节修改成功！")
                st.session_state.page = "book_detail"
                st.rerun()

elif st.session_state.page == "view_chapter":
    book_id = st.session_state.book_id
    chapter_num = st.session_state.chapter_num
    
    book = get_book(next(get_db()), book_id)
    chapter = get_chapter_by_number(next(get_db()), book_id, chapter_num)
    
    if not chapter:
        st.error("章节不存在")
    else:
        st.title(f"第{chapter_num}章 - {chapter.title}")
        st.markdown(f"**字数**: {chapter.word_count}字")
        st.markdown(f"**审核分数**: {chapter.audit_score or 0:.2f}")
        st.markdown(f"**连续性分数**: {chapter.continuity_score or 0:.2f}")
        st.markdown(f"**创建时间**: {chapter.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown("---")
        st.markdown(chapter.content)
        
        if st.button("返回章节管理", use_container_width=True, type="primary"):
            st.session_state.page = "book_detail"
            st.rerun()

elif st.session_state.page == "logs":
    st.title("日志输出台")
    st.markdown("---")
    
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

# 页脚
st.markdown("---")
st.markdown("<div style='text-align: center;'>© 2026 Novel Write - AI小说写作系统</div>", unsafe_allow_html=True)
