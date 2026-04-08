import streamlit as st
import os
import sys
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

def init_db():
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre TEXT NOT NULL,
        platform TEXT NOT NULL,
        chapter_words INTEGER NOT NULL,
        target_chapters INTEGER NOT NULL,
        status TEXT NOT NULL,
        language TEXT DEFAULT 'zh',
        parent_book_id INTEGER,
        fanfic_mode TEXT,
        brief TEXT,
        outline TEXT,
        writing_style TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )''')
    
    try:
        c.execute("ALTER TABLE books ADD COLUMN language TEXT DEFAULT 'zh'")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE books ADD COLUMN parent_book_id INTEGER")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE books ADD COLUMN fanfic_mode TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE books ADD COLUMN outline TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE books ADD COLUMN writing_style TEXT")
    except:
        pass
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        chapter_num INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        word_count INTEGER NOT NULL,
        status TEXT NOT NULL,
        summary TEXT,
        audit_score REAL,
        audit_issues TEXT,
        review_note TEXT,
        detection_score REAL,
        detection_provider TEXT,
        detected_at TEXT,
        token_usage TEXT,
        revisions INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (book_id) REFERENCES books (id)
    )''')
    
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN audit_issues TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN review_note TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN detection_score REAL")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN detection_provider TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN detected_at TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN token_usage TEXT")
    except:
        pass
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS book_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        story_bible TEXT,
        volume_outline TEXT,
        book_rules TEXT,
        current_state TEXT NOT NULL,
        particle_ledger TEXT,
        pending_hooks TEXT,
        chapter_summaries TEXT,
        subplot_board TEXT,
        emotional_arcs TEXT,
        character_matrix TEXT,
        style_guide TEXT,
        style_profile TEXT,
        parent_canon TEXT,
        fanfic_canon TEXT,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (book_id) REFERENCES books (id)
    )''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )''')
    
    conn.commit()
    conn.close()

init_db()

st.set_page_config(
    page_title="novel-write - AI 小说写作助手",
    page_icon="📚",
    layout="wide"
)

from src.llm.provider import llm_client
from src.pipeline.runner import PipelineRunner, PipelineConfig
from src.utils.file_manager import FileManager
from src.utils.log_manager import LogManager

file_manager = FileManager('data')
log_manager = LogManager('data')

def get_books():
    conn = sqlite3.connect('novel-write.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM books ORDER BY updated_at DESC')
    books = [dict(row) for row in c.fetchall()]
    conn.close()
    return books

def get_book_chapters(book_id):
    conn = sqlite3.connect('novel-write.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM chapters WHERE book_id = ? ORDER BY chapter_num', (book_id,))
    chapters = [dict(row) for row in c.fetchall()]
    conn.close()
    return chapters

def get_book_by_id(book_id):
    conn = sqlite3.connect('novel-write.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    row = c.fetchone()
    book = dict(row) if row else None
    conn.close()
    return book

def get_chapter_by_id(chapter_id):
    conn = sqlite3.connect('novel-write.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM chapters WHERE id = ?', (chapter_id,))
    row = c.fetchone()
    chapter = dict(row) if row else None
    conn.close()
    return chapter

def create_book(title, genre, platform, chapter_words, target_chapters, brief, outline='', writing_style='', language='zh', parent_book_id=None, fanfic_mode=None):
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
    INSERT INTO books (title, genre, platform, chapter_words, target_chapters, status, language, parent_book_id, fanfic_mode, brief, outline, writing_style, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, genre, platform, chapter_words, target_chapters, 'incubating', language, parent_book_id, fanfic_mode, brief, outline, writing_style, now, now))
    book_id = c.lastrowid
    
    c.execute('''
    INSERT INTO book_state (book_id, current_state, updated_at)
    VALUES (?, ?, ?)
    ''', (book_id, '初始状态', now))
    
    conn.commit()
    conn.close()
    
    log_manager.log_book_creation(book_id, title)
    
    return book_id

def create_chapter(book_id, chapter_num, title, content, word_count, status='drafted', summary=None, audit_score=None, audit_issues=None, review_note=None, detection_score=None, detection_provider=None, detected_at=None, token_usage=None, revisions=0):
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
    INSERT INTO chapters (book_id, chapter_num, title, content, word_count, status, summary, audit_score, audit_issues, review_note, detection_score, detection_provider, detected_at, token_usage, revisions, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (book_id, chapter_num, title, content, word_count, status, summary, audit_score, audit_issues, review_note, detection_score, detection_provider, detected_at, token_usage, revisions, now, now))
    
    c.execute('UPDATE books SET status = ?, updated_at = ? WHERE id = ?', ('active', now, book_id))
    
    conn.commit()
    conn.close()

def update_chapter(chapter_id, title=None, content=None, word_count=None, status=None, summary=None, audit_score=None, audit_issues=None, review_note=None, revisions=None):
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    updates = ['updated_at = ?']
    params = [now]
    
    if title is not None:
        updates.append('title = ?')
        params.append(title)
    if content is not None:
        updates.append('content = ?')
        params.append(content)
    if word_count is not None:
        updates.append('word_count = ?')
        params.append(word_count)
    if status is not None:
        updates.append('status = ?')
        params.append(status)
    if summary is not None:
        updates.append('summary = ?')
        params.append(summary)
    if audit_score is not None:
        updates.append('audit_score = ?')
        params.append(audit_score)
    if audit_issues is not None:
        updates.append('audit_issues = ?')
        params.append(audit_issues)
    if review_note is not None:
        updates.append('review_note = ?')
        params.append(review_note)
    if revisions is not None:
        updates.append('revisions = ?')
        params.append(revisions)
    
    params.append(chapter_id)
    
    c.execute(f'UPDATE chapters SET {", ".join(updates)} WHERE id = ?', params)
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    c.execute('DELETE FROM chapters WHERE book_id = ?', (book_id,))
    c.execute('DELETE FROM book_state WHERE book_id = ?', (book_id,))
    c.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()

def export_book(book_id, format='txt'):
    book = get_book_by_id(book_id)
    if not book:
        return None
    
    chapters = get_book_chapters(book_id)
    if not chapters:
        return None
    
    content = f"# {book['title']}\n\n"
    content += f"题材：{book['genre']}\n"
    content += f"平台：{book['platform']}\n"
    content += f"每章字数：{book['chapter_words']}\n"
    content += f"目标章节数：{book['target_chapters']}\n"
    content += f"已完成章节：{len(chapters)}\n\n"
    
    for chapter in chapters:
        if format == 'md':
            content += f"## 第{chapter['chapter_num']}章：{chapter['title']}\n\n"
        else:
            content += f"第{chapter['chapter_num']}章：{chapter['title']}\n\n"
        content += f"{chapter['content']}\n\n"
    
    filename = f"{book['title']}.{format}"
    
    if not os.path.exists('exports'):
        os.makedirs('exports')
    
    filepath = os.path.join('exports', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def export_chapter(chapter_id, format='txt'):
    chapter = get_chapter_by_id(chapter_id)
    if not chapter:
        return None
    
    book = get_book_by_id(chapter['book_id'])
    if not book:
        return None
    
    content = f"# 第{chapter['chapter_num']}章：{chapter['title']}\n\n"
    content += f"书籍：{book['title']}\n"
    content += f"字数：{chapter['word_count']}字\n"
    content += f"状态：{chapter['status']}\n\n"
    content += f"{chapter['content']}\n"
    
    filename = f"{book['title']}_第{chapter['chapter_num']}章.{format}"
    
    if not os.path.exists('exports'):
        os.makedirs('exports')
    
    filepath = os.path.join('exports', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def get_setting(key, default=None):
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
    INSERT OR REPLACE INTO settings (key, value, updated_at)
    VALUES (?, ?, ?)
    ''', (key, value, now))
    conn.commit()
    conn.close()

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'books'

if 'selected_book_id' not in st.session_state:
    st.session_state.selected_book_id = None

if 'selected_chapter_id' not in st.session_state:
    st.session_state.selected_chapter_id = None

def show_books_list():
    st.title("📚 我的书籍")
    
    books = get_books()
    
    if not books:
        st.info("还没有创建任何书籍，点击右上角的'创建新书'开始创作吧！")
        return
    
    cols = st.columns(3)
    for idx, book in enumerate(books):
        col = cols[idx % 3]
        with col:
            with st.container(border=True):
                st.markdown(f"### {book['title']}")
                st.markdown(f"**题材**: {book['genre']}")
                st.markdown(f"**平台**: {book['platform']}")
                
                chapters = get_book_chapters(book['id'])
                progress = len(chapters) / book['target_chapters'] * 100 if book['target_chapters'] > 0 else 0
                st.progress(int(progress))
                st.markdown(f"**进度**: {len(chapters)}/{book['target_chapters']}章 ({progress:.1f}%)")
                
                st.markdown(f"**状态**: {book['status']}")
                
                if st.button("查看详情", key=f"view_book_{book['id']}"):
                    st.session_state.selected_book_id = book['id']
                    st.session_state.current_page = 'book_detail'
                    st.rerun()

def show_create_book():
    st.title("📝 创建新书")
    
    with st.form(key="create_book_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("小说标题 *", placeholder="请输入小说标题")
            genre = st.selectbox("小说类型", ["玄幻", "仙侠", "都市", "科幻", "恐怖", "悬疑", "言情", "历史", "军事", "游戏"])
            platform = st.selectbox("小说平台", ["起点中文网", "番茄小说", "晋江文学城", "纵横中文网", "17K小说网", "其他"])
        
        with col2:
            chapter_words = st.number_input("每章字数", min_value=1000, max_value=50000, value=3000, step=500)
            target_chapters = st.number_input("总章节", min_value=1, max_value=1000, value=300, step=10)
            language = st.selectbox("语言", ["zh", "en"], index=0)
        
        outline = st.text_area("小说大纲", placeholder="请输入小说大纲（可选）", height=100)
        writing_style = st.text_area("作者文笔参考", placeholder="请输入作者文笔参考（可选）", height=100)
        brief = st.text_area("创作简报", placeholder="可以输入你的脑洞、世界观设定、人设文档等", height=150)
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            submit_button = st.form_submit_button(label="创建", type="primary", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button(label="取消", use_container_width=True)
        
        if submit_button:
            if title:
                book_id = create_book(title, genre, platform, chapter_words, target_chapters, brief, outline=outline, writing_style=writing_style, language=language)
                st.success(f"书籍创建成功！")
                st.session_state.selected_book_id = book_id
                st.session_state.current_page = 'book_detail'
                st.rerun()
            else:
                st.error("请输入小说标题")
        
        if cancel_button:
            st.session_state.current_page = 'books'
            st.rerun()

def show_book_detail():
    book_id = st.session_state.selected_book_id
    if not book_id:
        st.error("未选择书籍")
        return
    
    book = get_book_by_id(book_id)
    if not book:
        st.error("书籍不存在")
        return
    
    if st.button("← 返回书籍列表"):
        st.session_state.current_page = 'books'
        st.session_state.selected_book_id = None
        st.rerun()
    
    st.title(f"📖 {book['title']}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["书籍信息", "基础设定", "章节列表", "续写章节", "导出"])
    
    with tab1:
        show_book_info(book)
    
    with tab2:
        show_book_settings(book)
    
    with tab3:
        show_chapters_list(book)
    
    with tab4:
        show_write_chapters(book)
    
    with tab5:
        show_export(book)

def show_book_info(book):
    st.markdown("### 书籍信息")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**题材**: {book['genre']}")
        st.markdown(f"**平台**: {book['platform']}")
        st.markdown(f"**语言**: {book.get('language', 'zh')}")
    
    with col2:
        st.markdown(f"**每章字数**: {book['chapter_words']}")
        st.markdown(f"**目标章节**: {book['target_chapters']}")
        st.markdown(f"**状态**: {book['status']}")
    
    chapters = get_book_chapters(book['id'])
    progress = len(chapters) / book['target_chapters'] * 100 if book['target_chapters'] > 0 else 0
    st.progress(int(progress))
    st.markdown(f"**创作进度**: {len(chapters)}/{book['target_chapters']}章 ({progress:.1f}%)")
    
    if book.get('outline'):
        with st.expander("小说大纲"):
            st.markdown(book['outline'])
    
    if book.get('writing_style'):
        with st.expander("文笔参考"):
            st.markdown(book['writing_style'])
    
    if book.get('brief'):
        with st.expander("创作简报"):
            st.markdown(book['brief'])
    
    st.markdown(f"**创建时间**: {book['created_at']}")
    st.markdown(f"**更新时间**: {book['updated_at']}")
    
    if st.button("删除书籍", type="secondary"):
        delete_book(book['id'])
        st.session_state.current_page = 'books'
        st.session_state.selected_book_id = None
        st.rerun()

def backup_book_data(book_id):
    """备份书籍数据"""
    import shutil
    import os
    from datetime import datetime
    
    book_dir = file_manager.get_book_dir(book_id)
    if not os.path.exists(book_dir):
        return False
    
    backup_dir = os.path.join('data', f'backup_{book_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    shutil.copytree(book_dir, backup_dir)
    return True

def show_book_settings(book):
    st.markdown("### 基础设定")
    
    story_bible = file_manager.load_story_bible(book['id'])
    volume_outline = file_manager.load_volume_outline(book['id'])
    book_rules = file_manager.load_book_rules(book['id'])
    current_state = file_manager.load_current_state(book['id'])
    pending_hooks = file_manager.load_pending_hooks(book['id'])
    particle_ledger = file_manager.load_particle_ledger(book['id'])
    chapter_summaries = file_manager.load_chapter_summaries(book['id'])
    subplot_board = file_manager.load_subplot_board(book['id'])
    emotional_arcs = file_manager.load_emotional_arcs(book['id'])
    character_matrix = file_manager.load_character_matrix(book['id'])
    
    has_settings = story_bible or volume_outline or book_rules
    
    # 添加大纲修改功能
    st.markdown("### 修改故事大纲")
    new_outline = st.text_area("新的故事大纲", value=book.get('outline', ''), height=200)
    outline_context = st.text_area("修改指导", placeholder="请输入如何修改大纲的指导（可选）", height=100)
    
    if st.button("更新大纲", type="primary"):
        if new_outline != book.get('outline', ''):
            with st.spinner("正在分析大纲变化..."):
                try:
                    # 使用流水线运行器分析大纲变化
                    pipeline = PipelineRunner(llm_client)
                    analysis_result = pipeline.update_story_outline(
                        book=book,
                        new_outline=new_outline,
                        outline_context=outline_context,
                        book_dir=file_manager.get_book_dir(book['id'])
                    )
                    
                    # 显示分析结果
                    st.info(f"大纲变化分析：{analysis_result['recommendation']}")
                    st.expander("详细分析").markdown(analysis_result['impact_analysis']['analysis'])
                    
                    # 更新书籍大纲
                    conn = sqlite3.connect('novel-write.db')
                    c = conn.cursor()
                    now = datetime.now().isoformat()
                    c.execute('UPDATE books SET outline = ?, updated_at = ? WHERE id = ?', (new_outline, now, book['id']))
                    conn.commit()
                    conn.close()
                    
                    # 根据分析结果给出建议
                    if analysis_result['recommendation'].startswith("大纲变化较大"):
                        if st.button("从第一章开始重写"):
                            delete_chapters_after(book['id'], 0)
                            st.success("已删除所有章节，准备从第一章开始重写")
                            st.rerun()
                    elif analysis_result['recommendation'].startswith("大纲变化对现有章节有重大影响"):
                        if st.button("从受影响章节开始重写"):
                            affected_chapter = analysis_result['impact_analysis'].get('affected_chapters', [1])[0]
                            delete_chapters_after(book['id'], affected_chapter - 1)
                            st.success(f"已删除第{affected_chapter}章之后的所有章节")
                            st.rerun()
                    
                    st.success("大纲更新成功！")
                    st.rerun()
                except Exception as e:
                    log_manager.log_error("更新大纲", e, {"书籍ID": book['id'], "标题": book['title']})
                    st.error(f"更新失败: {str(e)}")
    
    if not has_settings:
        st.info("还没有生成基础设定，点击下方按钮开始生成")
        
        external_context = st.text_area("外部指令（可选）", placeholder="可以输入你的创作思路、世界观设定等", height=100)
        
        if st.button("生成基础设定", type="primary"):
            with st.spinner("正在生成基础设定，请稍候..."):
                try:
                    book_dict = {
                        'id': book['id'],
                        'title': book['title'],
                        'genre': book['genre'],
                        'platform': book['platform'],
                        'target_chapters': book['target_chapters'],
                        'chapter_words': book['chapter_words'],
                        'language': book.get('language', 'zh'),
                        'outline': book.get('outline', ''),
                        'writing_style': book.get('writing_style', '')
                    }
                    
                    # 使用流水线运行器生成基础设定
                    pipeline = PipelineRunner(llm_client)
                    output = pipeline.create_book_foundation(book_dict, external_context)
                    
                    file_manager.save_story_bible(book['id'], output['story_bible'])
                    file_manager.save_volume_outline(book['id'], output['volume_outline'])
                    file_manager.save_book_rules(book['id'], output['book_rules'])
                    file_manager.save_current_state(book['id'], output['current_state'])
                    file_manager.save_pending_hooks(book['id'], output['pending_hooks'])
                    
                    log_manager.log_settings_generation(book['id'], book['title'])
                    
                    st.success("基础设定生成成功！")
                    st.rerun()
                except Exception as e:
                    log_manager.log_error("生成基础设定", e, {"书籍ID": book['id'], "标题": book['title']})
                    st.error(f"生成失败: {str(e)}")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("重新生成", type="secondary"):
                external_context = st.text_area("外部指令（可选）", placeholder="可以输入你的创作思路、世界观设定等", height=100, key="regen_context")
                if st.button("确认重新生成", type="primary"):
                    with st.spinner("正在重新生成基础设定，请稍候..."):
                        try:
                            book_dict = {
                                'id': book['id'],
                                'title': book['title'],
                                'genre': book['genre'],
                                'platform': book['platform'],
                                'target_chapters': book['target_chapters'],
                                'chapter_words': book['chapter_words'],
                                'language': book.get('language', 'zh'),
                                'outline': book.get('outline', ''),
                                'writing_style': book.get('writing_style', '')
                            }
                            
                            # 使用流水线运行器重新生成基础设定
                            pipeline = PipelineRunner(llm_client)
                            output = pipeline.create_book_foundation(book_dict, external_context)
                            
                            file_manager.save_story_bible(book['id'], output['story_bible'])
                            file_manager.save_volume_outline(book['id'], output['volume_outline'])
                            file_manager.save_book_rules(book['id'], output['book_rules'])
                            file_manager.save_current_state(book['id'], output['current_state'])
                            file_manager.save_pending_hooks(book['id'], output['pending_hooks'])
                            
                            st.success("基础设定重新生成成功！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"生成失败: {str(e)}")
        
        if story_bible:
            with st.expander("📖 故事圣经", expanded=False):
                st.markdown(story_bible)
        
        if volume_outline:
            with st.expander("📋 卷纲", expanded=False):
                st.markdown(volume_outline)
        
        if book_rules:
            with st.expander("📜 书籍规则", expanded=False):
                st.markdown(book_rules)
        
        if current_state:
            with st.expander("📊 当前状态", expanded=False):
                st.markdown(current_state)
        
        if pending_hooks:
            with st.expander("🎣 伏笔池", expanded=False):
                st.markdown(pending_hooks)
        
        if particle_ledger:
            with st.expander("📊 粒子账本", expanded=False):
                st.markdown(particle_ledger)
        
        if chapter_summaries:
            with st.expander("📝 章节摘要", expanded=False):
                st.markdown(chapter_summaries)
        
        if subplot_board:
            with st.expander("🎭 支线进度板", expanded=False):
                st.markdown(subplot_board)
        
        if emotional_arcs:
            with st.expander("❤️ 情感弧线", expanded=False):
                st.markdown(emotional_arcs)
        
        if character_matrix:
            with st.expander("👥 角色交互矩阵", expanded=False):
                st.markdown(character_matrix)

def delete_chapters_after(book_id, chapter_num):
    """删除指定章节之后的所有章节"""
    conn = sqlite3.connect('novel-write.db')
    c = conn.cursor()
    c.execute('DELETE FROM chapters WHERE book_id = ? AND chapter_num > ?', (book_id, chapter_num))
    conn.commit()
    conn.close()

def show_chapters_list(book):
    st.markdown("### 章节列表")
    
    chapters = get_book_chapters(book['id'])
    
    if not chapters:
        st.info("还没有任何章节，请切换到'续写章节'标签开始创作")
        return
    
    total_words = sum(chapter['word_count'] for chapter in chapters)
    st.markdown(f"**总字数**: {total_words:,}字")
    
    # 添加从指定章节重写功能
    st.markdown("### 从指定章节重写")
    col1, col2 = st.columns([2, 1])
    with col1:
        rewrite_from_chapter = st.number_input("从第N章开始重写", min_value=1, max_value=len(chapters), value=1)
    
    if st.button("确认重写", type="primary"):
        # 使用会话状态来跟踪确认状态
        if 'rewrite_confirmed' not in st.session_state:
            st.session_state.rewrite_confirmed = False
        
        if not st.session_state.rewrite_confirmed:
            st.warning(f"确定要从第{rewrite_from_chapter}章开始重写吗？这将删除第{rewrite_from_chapter}章之后的所有章节。")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("确认删除并重写"):
                    st.session_state.rewrite_confirmed = True
                    st.rerun()
            with col_cancel:
                if st.button("取消"):
                    st.session_state.rewrite_confirmed = False
        else:
            # 删除后续章节
            delete_chapters_after(book['id'], rewrite_from_chapter - 1)
            st.success(f"已删除第{rewrite_from_chapter}章之后的所有章节")
            st.session_state.rewrite_confirmed = False
            st.rerun()
    
    for chapter in chapters:
        with st.expander(f"第{chapter['chapter_num']}章：{chapter['title']} ({chapter['word_count']}字)", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                st.markdown(f"**状态**: {chapter['status']}")
                st.markdown(f"**字数**: {chapter['word_count']}")
            
            with col2:
                if chapter.get('audit_score'):
                    st.markdown(f"**审核分数**: {chapter['audit_score']:.2f}")
                if chapter.get('detection_score'):
                    st.markdown(f"**AI检测分数**: {chapter['detection_score']:.2f}")
            
            with col3:
                col3_1, col3_2 = st.columns(2)
                with col3_1:
                    if st.button("查看", key=f"view_ch_{chapter['id']}"):
                        st.session_state.selected_chapter_id = chapter['id']
                        st.session_state.current_page = 'chapter_detail'
                        st.rerun()
                with col3_2:
                    if st.button("重写", key=f"rewrite_ch_{chapter['id']}"):
                        st.session_state.selected_chapter_id = chapter['id']
                        st.session_state.current_page = 'chapter_detail'
                        st.session_state.show_rewrite_form = True
                        st.rerun()
            
            if chapter.get('summary'):
                st.markdown(f"**摘要**: {chapter['summary']}")
            
            st.markdown("---")
            st.markdown(chapter['content'])

def show_write_chapters(book):
    st.markdown("### 续写章节")
    
    chapters = get_book_chapters(book['id'])
    next_chapter_num = len(chapters) + 1
    
    story_bible = file_manager.load_story_bible(book['id'])
    if not story_bible:
        st.warning("请先生成基础设定！")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**下一章节**: 第{next_chapter_num}章")
        st.markdown(f"**目标字数**: {book['chapter_words']}字")
    
    with col2:
        num_chapters = st.number_input("续写章节数", min_value=1, max_value=10, value=1, help="一次续写的章节数量")
    
    context = st.text_area("创作指导", placeholder="可以输入本章重点、场景描述等（可选）", height=100)
    
    words_override = st.number_input("本章字数（可选）", min_value=0, max_value=50000, value=0, help="留空则使用默认字数")
    
    if st.button("开始写作", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(num_chapters):
            current_chapter_num = next_chapter_num + i
            status_text.markdown(f"正在生成第 {current_chapter_num} 章...")
            
            try:
                book_dict = {
                    'id': book['id'],
                    'title': book['title'],
                    'genre': book['genre'],
                    'platform': book['platform'],
                    'chapter_words': book['chapter_words'],
                    'target_chapters': book['target_chapters'],
                    'language': book.get('language', 'zh'),
                    'outline': book.get('outline', ''),
                    'writing_style': book.get('writing_style', '')
                }
                
                # 使用流水线运行器续写下一章
                pipeline = PipelineRunner(llm_client)
                result = pipeline.continue_next_chapter(
                    book=book_dict,
                    chapter_num=current_chapter_num,
                    external_context=context,
                    word_count_override=words_override if words_override > 0 else None,
                    book_dir=file_manager.get_book_dir(book['id'])
                )
                
                # 简化处理，暂时不使用detector_agent
                detection_result = {'score': 0, 'provider': 'none'}
                
                create_chapter(
                    book_id=book['id'],
                    chapter_num=current_chapter_num,
                    title=result['title'],
                    content=result['content'],
                    word_count=result['word_count'],
                    status="已完成",
                    summary=result['chapter_summary'],
                    audit_score=result['audit_score'],
                    audit_issues=json.dumps([]),  # 简化处理
                    detection_score=detection_result.get('score'),
                    detection_provider=detection_result.get('provider')
                )
                
                file_manager.save_chapter_content(book['id'], current_chapter_num, result['content'])

                
                # 更新所有状态文件
                if result['updated_state']:
                    file_manager.save_current_state(book['id'], result['updated_state'])
                if result['updated_ledger']:
                    file_manager.save_particle_ledger(book['id'], result['updated_ledger'])
                if result['updated_hooks']:
                    file_manager.save_pending_hooks(book['id'], result['updated_hooks'])
                if result['chapter_summary']:
                    # 追加章节摘要到章节摘要文件
                    existing_summaries = file_manager.load_chapter_summaries(book['id']) or ""
                    new_summary = f"\n## 第{current_chapter_num}章\n{result['chapter_summary']}\n"
                    file_manager.save_chapter_summaries(book['id'], existing_summaries + new_summary)
                if result.get('updated_subplots'):
                    file_manager.save_subplot_board(book['id'], result['updated_subplots'])
                if result.get('updated_emotional_arcs'):
                    file_manager.save_emotional_arcs(book['id'], result['updated_emotional_arcs'])
                if result.get('updated_character_matrix'):
                    file_manager.save_character_matrix(book['id'], result['updated_character_matrix'])
                
                log_manager.log_chapter_generation(book['id'], current_chapter_num, result['title'], result['word_count'])
                log_manager.log_state_update(book['id'], current_chapter_num)
                
                progress_bar.progress((i + 1) / num_chapters)
                
            except Exception as e:
                log_manager.log_error("生成章节", e, {"书籍ID": book['id'], "章节": current_chapter_num})
                st.error(f"第 {current_chapter_num} 章生成失败: {str(e)}")
                break
        
        status_text.markdown(f"完成！共生成 {num_chapters} 章")
        st.success("章节生成完成！")
        st.rerun()

def show_export(book):
    st.markdown("### 导出")
    
    chapters = get_book_chapters(book['id'])
    
    if not chapters:
        st.info("还没有任何章节可以导出")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 导出整本书")
        format_all = st.selectbox("格式", ["txt", "md"], key="export_format_all")
        
        if st.button("导出整本书", type="primary"):
            with st.spinner("正在导出..."):
                filepath = export_book(book['id'], format_all)
                if filepath:
                    st.success(f"导出成功！文件保存在: {filepath}")
                    with open(filepath, 'r', encoding='utf-8') as f:
                        st.download_button(
                            label="下载文件",
                            data=f,
                            file_name=os.path.basename(filepath),
                            mime="text/plain"
                        )
                else:
                    st.error("导出失败")
    
    with col2:
        st.markdown("#### 导出单章")
        chapter_nums = [f"第{ch['chapter_num']}章：{ch['title']}" for ch in chapters]
        selected_chapter = st.selectbox("选择章节", chapter_nums, key="export_chapter_select")
        format_single = st.selectbox("格式", ["txt", "md"], key="export_format_single")
        
        if st.button("导出章节", type="primary"):
            chapter_idx = chapter_nums.index(selected_chapter)
            chapter_id = chapters[chapter_idx]['id']
            
            with st.spinner("正在导出..."):
                filepath = export_chapter(chapter_id, format_single)
                if filepath:
                    st.success(f"导出成功！文件保存在: {filepath}")
                    with open(filepath, 'r', encoding='utf-8') as f:
                        st.download_button(
                            label="下载文件",
                            data=f,
                            file_name=os.path.basename(filepath),
                            mime="text/plain"
                        )
                else:
                    st.error("导出失败")

def show_chapter_detail():
    chapter_id = st.session_state.selected_chapter_id
    if not chapter_id:
        st.error("未选择章节")
        return
    
    chapter = get_chapter_by_id(chapter_id)
    if not chapter:
        st.error("章节不存在")
        return
    
    book = get_book_by_id(chapter['book_id'])
    if not book:
        st.error("书籍不存在")
        return
    
    if st.button("← 返回书籍详情"):
        st.session_state.current_page = 'book_detail'
        st.session_state.selected_chapter_id = None
        st.rerun()
    
    st.title(f"📖 {book['title']} - 第{chapter['chapter_num']}章")
    st.markdown(f"### {chapter['title']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**字数**: {chapter['word_count']}")
        st.markdown(f"**状态**: {chapter['status']}")
    
    with col2:
        if chapter.get('audit_score'):
            st.markdown(f"**审核分数**: {chapter['audit_score']:.2f}")
        if chapter.get('detection_score'):
            st.markdown(f"**AI检测分数**: {chapter['detection_score']:.2f}")
    
    with col3:
        st.markdown(f"**修订次数**: {chapter.get('revisions', 0)}")
        st.markdown(f"**创建时间**: {chapter['created_at'][:10]}")
    
    if chapter.get('summary'):
        st.markdown(f"**摘要**: {chapter['summary']}")
    
    st.markdown("---")
    st.markdown(chapter['content'])
    
    st.markdown("---")
    st.markdown("### 章节操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("导出章节", type="primary"):
            filepath = export_chapter(chapter_id, 'txt')
            if filepath:
                st.success(f"导出成功！文件保存在: {filepath}")
                with open(filepath, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="下载文件",
                        data=f,
                        file_name=os.path.basename(filepath),
                        mime="text/plain"
                    )
    
    with col2:
        if st.button("重新审核"):
            with st.spinner("正在审核..."):
                try:
                    book_dict = {
                        'id': book['id'],
                        'title': book['title'],
                        'genre': book['genre'],
                        'platform': book['platform'],
                        'chapter_words': book['chapter_words'],
                        'target_chapters': book['target_chapters'],
                        'language': book.get('language', 'zh')
                    }
                    
                    # 使用流水线运行器进行审核
                    pipeline = PipelineRunner(llm_client)
                    audit_result = pipeline.audit_chapter(
                        content=chapter['content'],
                        book=book_dict,
                        chapter_num=chapter['chapter_num']
                    )
                    
                    update_chapter(
                        chapter_id,
                        audit_score=audit_result.get('score'),
                        audit_issues=json.dumps(audit_result.get('issues', []))
                    )
                    
                    st.success(f"审核完成！分数: {audit_result.get('score'):.2f}")
                    st.rerun()
                except Exception as e:
                    st.error(f"审核失败: {str(e)}")
    
    with col3:
        if st.button("重写章节"):
            st.session_state.show_rewrite_form = True
    
    if st.session_state.get('show_rewrite_form', False):
        context = st.text_area("重写指导", placeholder="请输入重写指导", height=100)
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("确认重写", type="primary"):
                with st.spinner("正在重写..."):
                    try:
                        book_dict = {
                            'id': book['id'],
                            'title': book['title'],
                            'genre': book['genre'],
                            'platform': book['platform'],
                            'chapter_words': book['chapter_words'],
                            'target_chapters': book['target_chapters'],
                            'language': book.get('language', 'zh'),
                            'outline': book.get('outline', ''),
                            'writing_style': book.get('writing_style', '')
                        }
                        
                        # 使用新的流水线运行器进行重写
                        pipeline = PipelineRunner(llm_client)
                        result = pipeline.run(
                            book=book_dict,
                            chapter_num=chapter['chapter_num'],
                            external_context=context,
                            book_dir=file_manager.get_book_dir(book['id'])
                        )
                        
                        update_chapter(
                            chapter_id,
                            title=result['title'],
                            content=result['content'],
                            word_count=result['word_count'],
                            summary=result['chapter_summary'],
                            revisions=chapter.get('revisions', 0) + 1
                        )
                        
                        # 更新所有状态文件
                        if result['updated_state']:
                            file_manager.save_current_state(book['id'], result['updated_state'])
                        if result['updated_ledger']:
                            file_manager.save_particle_ledger(book['id'], result['updated_ledger'])
                        if result['updated_hooks']:
                            file_manager.save_pending_hooks(book['id'], result['updated_hooks'])
                        if result['chapter_summary']:
                            # 追加章节摘要到章节摘要文件
                            existing_summaries = file_manager.load_chapter_summaries(book['id']) or ""
                            new_summary = f"\n## 第{chapter['chapter_num']}章（重写）\n{result['chapter_summary']}\n"
                            file_manager.save_chapter_summaries(book['id'], existing_summaries + new_summary)
                        if result.get('updated_subplots'):
                            file_manager.save_subplot_board(book['id'], result['updated_subplots'])
                        if result.get('updated_emotional_arcs'):
                            file_manager.save_emotional_arcs(book['id'], result['updated_emotional_arcs'])
                        if result.get('updated_character_matrix'):
                            file_manager.save_character_matrix(book['id'], result['updated_character_matrix'])
                        
                        log_manager.log_chapter_rewrite(book['id'], chapter['chapter_num'], result['title'])
                        log_manager.log_state_update(book['id'], chapter['chapter_num'])
                        
                        st.session_state.show_rewrite_form = False
                        st.success("重写完成！")
                        st.rerun()
                    except Exception as e:
                        log_manager.log_error("重写章节", e, {"书籍ID": book['id'], "章节": chapter['chapter_num']})
                        st.error(f"重写失败: {str(e)}")
        with col_cancel:
            if st.button("取消"):
                st.session_state.show_rewrite_form = False
                st.rerun()

def show_settings():
    st.title("⚙️ 设置")
    
    tab1, tab2, tab3, tab4 = st.tabs(["LLM设置", "检测设置", "其他设置", "操作日志"])
    
    with tab1:
        st.markdown("### LLM 设置")
        
        llm_model = st.text_input("LLM 模型", value=get_setting('llm_model', os.getenv('INKOS_LLM_MODEL', 'gpt-4')))
        llm_base_url = st.text_input("LLM Base URL", value=get_setting('llm_base_url', os.getenv('INKOS_LLM_BASE_URL', '')))
        llm_api_key = st.text_input("LLM API Key", value=get_setting('llm_api_key', os.getenv('INKOS_LLM_API_KEY', '')), type="password")
        
        if st.button("保存 LLM 设置", type="primary"):
            set_setting('llm_model', llm_model)
            set_setting('llm_base_url', llm_base_url)
            set_setting('llm_api_key', llm_api_key)
            st.success("LLM 设置已保存")
    
    with tab2:
        st.markdown("### AI 内容检测设置")
        
        detection_provider = st.selectbox("检测提供商", ["gptzero", "originality", "custom"], index=0)
        detection_api_key = st.text_input("检测 API Key", value=get_setting('detection_api_key', ''), type="password")
        detection_api_url = st.text_input("检测 API URL", value=get_setting('detection_api_url', ''))
        
        if st.button("保存检测设置", type="primary"):
            set_setting('detection_provider', detection_provider)
            set_setting('detection_api_key', detection_api_key)
            set_setting('detection_api_url', detection_api_url)
            st.success("检测设置已保存")
    
    with tab3:
        st.markdown("### 其他设置")
        
        default_chapter_words = st.number_input("默认每章字数", min_value=1000, max_value=50000, value=int(get_setting('default_chapter_words', '3000')))
        default_target_chapters = st.number_input("默认目标章节", min_value=1, max_value=1000, value=int(get_setting('default_target_chapters', '300')))
        
        if st.button("保存其他设置", type="primary"):
            set_setting('default_chapter_words', str(default_chapter_words))
            set_setting('default_target_chapters', str(default_target_chapters))
            st.success("其他设置已保存")
    
    with tab4:
        st.markdown("### 📋 操作日志")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            log_limit = st.slider("显示最近操作数", min_value=5, max_value=100, value=20)
        with col2:
            if st.button("刷新日志"):
                st.rerun()
        
        st.markdown("---")
        
        operations_log = log_manager.get_recent_operations(log_limit)
        st.text_area("操作记录", operations_log, height=500)

st.sidebar.title("📚 InkOS")
st.sidebar.markdown("---")

if st.session_state.current_page == 'books':
    if st.sidebar.button("📖 我的书籍", use_container_width=True, type="primary"):
        st.session_state.current_page = 'books'
        st.session_state.selected_book_id = None
        st.session_state.selected_chapter_id = None
else:
    if st.sidebar.button("📖 我的书籍", use_container_width=True):
        st.session_state.current_page = 'books'
        st.session_state.selected_book_id = None
        st.session_state.selected_chapter_id = None

if st.session_state.current_page == 'create_book':
    if st.sidebar.button("📝 创建新书", use_container_width=True, type="primary"):
        st.session_state.current_page = 'create_book'
else:
    if st.sidebar.button("📝 创建新书", use_container_width=True):
        st.session_state.current_page = 'create_book'

if st.session_state.current_page == 'settings':
    if st.sidebar.button("⚙️ 设置", use_container_width=True, type="primary"):
        st.session_state.current_page = 'settings'
else:
    if st.sidebar.button("⚙️ 设置", use_container_width=True):
        st.session_state.current_page = 'settings'

st.sidebar.markdown("---")
st.sidebar.markdown("### 快捷操作")

if st.sidebar.button("🔄 刷新页面", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"当前版本: v1.0.0")

if st.session_state.current_page == 'books':
    show_books_list()
elif st.session_state.current_page == 'create_book':
    show_create_book()
elif st.session_state.current_page == 'book_detail':
    show_book_detail()
elif st.session_state.current_page == 'chapter_detail':
    show_chapter_detail()
elif st.session_state.current_page == 'settings':
    show_settings()
