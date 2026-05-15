#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NovelWrite SSE 流式测试脚本

功能：
1. 创建书籍《魔法世界，我能抽卡SSR神技》
2. 生成大纲（SSE流式输出）
3. 续写3章小说（SSE流式输出）

使用方法：
    python test_novel_workflow.py [--base-url BASE_URL]

示例：
    python test_novel_workflow.py
    python test_novel_workflow.py --base-url http://localhost:8000
"""

import argparse
import json
import time
import requests
from typing import Dict, Any, Iterator, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError


class SSEClient:
    """SSE 客户端"""
    
    def __init__(self, url: str):
        self.url = url
        self._event_buffer = ""
    
    def events(self) -> Iterator[Dict[str, Any]]:
        """接收 SSE 事件流"""
        request = Request(self.url)
        request.add_header('Accept', 'text/event-stream')
        request.add_header('Cache-Control', 'no-cache')
        
        with urlopen(request, timeout=300) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                
                if line.startswith('data:'):
                    data = line[5:].strip()
                    if data:
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError:
                            yield {"type": "error", "message": f"JSON解析失败: {data}"}
                
                # 空行表示事件结束
                elif line == '':
                    continue


class NovelWriteClient:
    """NovelWrite API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/api/v1"

    def _url(self, path: str) -> str:
        """构建完整URL"""
        return f"{self.base_url}{self.api_prefix}{path}"

    def create_book(
        self,
        title: str,
        genre: str,
        platform: str = "通用",
        chapter_words: int = 3000,
        target_chapters: int = 100,
        outline: str = ""
    ) -> Dict[str, Any]:
        """创建书籍"""
        response = requests.post(
            self._url("/books"),
            json={
                "title": title,
                "genre": genre,
                "platform": platform,
                "chapter_words": chapter_words,
                "target_chapters": target_chapters,
                "outline": outline
            }
        )
        response.raise_for_status()
        return response.json()

    def get_book(self, book_id: int) -> Dict[str, Any]:
        """获取书籍详情"""
        response = requests.get(self._url(f"/books/{book_id}"))
        response.raise_for_status()
        return response.json()

    def generate_outline_stream(self, book_id: int) -> Iterator[Dict[str, Any]]:
        """生成大纲（SSE流式）"""
        url = f"{self._url('/stream/generate-outline')}?book_id={book_id}"
        return SSEClient(url).events()

    def continue_chapters_stream(
        self,
        book_id: int,
        start_chapter: int,
        count: int = 1
    ) -> Iterator[Dict[str, Any]]:
        """续写章节（SSE流式）"""
        url = f"{self._url('/stream/continue-chapters')}?book_id={book_id}&start_chapter={start_chapter}&count={count}"
        return SSEClient(url).events()


def stream_events(
    client: NovelWriteClient,
    event_generator: Iterator[Dict[str, Any]],
    task_name: str
) -> bool:
    """
    处理 SSE 事件流，打印到控制台
    
    Returns:
        True: 成功完成
        False: 出错
    """
    node_contents: Dict[str, str] = {}
    current_node: Optional[str] = None
    success = False
    
    try:
        for event in event_generator:
            event_type = event.get("type", "unknown")
            
            if event_type == "start":
                node = event.get("node", "未知节点")
                current_node = node
                node_contents[node] = ""
                print(f"\n{'='*60}")
                print(f"▶ 开始: {node}")
                print(f"{'='*60}")
            
            elif event_type == "token":
                text = event.get("text", "")
                node = event.get("node")
                if node:
                    node_contents[node] = node_contents.get(node, "") + text
                # 实时打印 token
                print(text, end="", flush=True)
            
            elif event_type == "node_end":
                node = event.get("node", "未知节点")
                ok = event.get("ok", False)
                print(f"\n{'='*60}")
                if ok:
                    print(f"✓ 完成: {node}")
                else:
                    error = event.get("error", "未知错误")
                    print(f"✗ 失败: {node} - {error}")
                print(f"{'='*60}\n")
            
            elif event_type == "progress":
                value = event.get("value", 0)
                print(f"\r进度: {value}%", end="", flush=True)
            
            elif event_type == "done":
                print(f"\n{'='*60}")
                print(f"🎉 {task_name}完成!")
                print(f"{'='*60}\n")
                success = True
            
            elif event_type == "error":
                message = event.get("message", "未知错误")
                print(f"\n{'='*60}")
                print(f"❌ 错误: {message}")
                print(f"{'='*60}\n")
                success = False
        
    except URLError as e:
        print(f"\n连接错误: {e}")
        success = False
    except Exception as e:
        print(f"\n异常: {e}")
        success = False
    
    return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NovelWrite SSE 流式测试脚本")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API基础URL (默认: http://localhost:8000)"
    )
    args = parser.parse_args()

    # 初始化客户端
    client = NovelWriteClient(args.base_url)

    # 书籍信息
    book_title = "魔法世界，我能抽卡SSR神技"
    book_genre = "奇幻"
    book_outline = """魔法师，战士体系，主角是魔法师里的召唤师。
世界存在:光，暗，金，木，水，火，土，风，雷，冰，石，生命，12种能量，可以进行汲取修炼，强大自身。
魔能大陆有4个人类国家:
①圣灵帝国:光明教会，光魔法为主，其他为辅，还有圣战士，利用光能修炼身体。
②元素帝国:以金木水火土为核心，有五大教派，使用五种能量，共同治国。
③自然帝国:风，雷，冰，石，四种核心，有四大教派。
④黑暗帝国:以暗和生命为主，生命主要靠汲取生物的活体能量，是反派。
每个人主修一种，召唤师是一个独特的职业，独立于魔法师，战士之外，将能量集中在精神力上，然后构建法阵，献祭祭品，召唤生物作战。
话说，几百年前，圣灵帝国，出了一个号称可以与神比肩，一个强大的光明魔法师，将黑暗帝国驱赶到星夜岭之外的蛮荒之地，其余几个国家霸占整个魔能大陆最富饶的土地。
主角是当代光明教会高层神职人员的私生子，母亲被杀，一心想覆灭教会，踏上了寻找黑暗帝国的旅途，希望借助暗元素的强大力量报仇。
后面发现有其他种族带来的危机，在魔能大陆之外，还有另一片魔兽大陆，生存着一群可以与神比肩的怪物，正在渗透，带来危机。"""

    print("=" * 70)
    print("🚀 NovelWrite SSE 流式测试脚本")
    print("=" * 70)
    print(f"📡 API地址: {args.base_url}")
    print(f"📖 测试书籍: {book_title}")
    print(f"🎭 题材: {book_genre}")
    print("=" * 70)
    print()

    # ========== 步骤1: 创建书籍 ==========
    print("📚 步骤1: 创建书籍")
    print("-" * 40)

    try:
        book = client.create_book(
            title=book_title,
            genre=book_genre,
            platform="起点",
            chapter_words=3000,
            target_chapters=100,
            outline=book_outline
        )
        book_id = book["id"]
        print(f"✅ 书籍创建成功!")
        print(f"   书籍ID: {book_id}")
        print(f"   书名: {book['title']}")
        print(f"   题材: {book['genre']}")
    except Exception as e:
        print(f"❌ 创建书籍失败: {e}")
        return

    print()
    print("⏳ 3秒后自动开始生成大纲... (按 Ctrl+C 取消)")
    time.sleep(3)

    # ========== 步骤2: 生成大纲（SSE流式） ==========
    print()
    print("📝 步骤2: 生成大纲（SSE流式输出）")
    print("-" * 40)
    print("提示: LLM 输出将实时显示在下方...\n")

    try:
        success = stream_events(
            client,
            client.generate_outline_stream(book_id),
            "大纲生成"
        )
        
        if not success:
            print("❌ 大纲生成失败")
            return
            
    except Exception as e:
        print(f"❌ 生成大纲失败: {e}")
        return

    # 显示书籍大纲
    print("📖 生成的大纲内容预览:")
    print("-" * 40)
    try:
        book_detail = client.get_book(book_id)
        story_bible = book_detail.get("story_bible", "")
        if story_bible:
            print(story_bible[:500] + "..." if len(story_bible) > 500 else story_bible)
        else:
            print("(未保存大纲内容)")
    except Exception as e:
        print(f"获取大纲失败: {e}")

    print()
    print("⏳ 3秒后自动开始续写章节... (按 Ctrl+C 取消)")
    time.sleep(3)

    # ========== 步骤3: 续写3章（SSE流式） ==========
    print()
    print("✍️ 步骤3: 续写3章小说（SSE流式输出）")
    print("-" * 40)
    print("提示: LLM 输出将实时显示在下方...\n")

    try:
        success = stream_events(
            client,
            client.continue_chapters_stream(book_id, start_chapter=1, count=3),
            "章节续写"
        )
        
        if not success:
            print("❌ 章节续写失败")
            return
            
    except Exception as e:
        print(f"❌ 续写章节失败: {e}")
        return

    # 显示章节列表
    print("📚 生成的章节:")
    print("-" * 40)
    try:
        book_detail = client.get_book(book_id)
        chapters_url = f"{args.base_url}/api/v1/books/{book_id}/chapters"
        chapters_resp = requests.get(chapters_url)
        if chapters_resp.status_code == 200:
            chapters = chapters_resp.json()
            if isinstance(chapters, dict):
                chapters = chapters.get("chapters", [])
            for ch in chapters[:5]:  # 只显示前5章
                print(f"  第{ch.get('chapter_number', '?')}章: {ch.get('title', '无标题')}")
                print(f"    字数: {ch.get('word_count', 0)}")
    except Exception as e:
        print(f"获取章节列表失败: {e}")

    print()

    # ========== 完成 ==========
    print("=" * 70)
    print("🎉 测试完成!")
    print("=" * 70)
    print(f"📖 书籍ID: {book_id}")
    print(f"📚 书名: {book_title}")
    print(f"🎭 题材: {book_genre}")
    print("📝 已生成: 大纲 + 3章正文")
    print()
    print(f"🔗 查看书籍详情: {args.base_url}/api/v1/books/{book_id}")
    print("=" * 70)


if __name__ == "__main__":
    main()
