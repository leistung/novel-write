from typing import Dict, Any, Optional, List
from src.agents.architect import ArchitectAgent
from src.agents.writer import WriterAgent
from src.agents.continuity import ContinuityAuditor
from src.agents.reviser import ReviserAgent
from src.agents.radar import RadarAgent
from src.llm.provider import LLMClient

class PipelineConfig:
    def __init__(self, radar_enabled: bool = False, max_revisions: int = 3):
        self.radar_enabled = radar_enabled
        self.max_revisions = max_revisions

class ChapterPipelineResult:
    def __init__(self, chapter_num: int, content: str, word_count: int, audit_score: float, revisions: int):
        self.chapter_num = chapter_num
        self.content = content
        self.word_count = word_count
        self.audit_score = audit_score
        self.revisions = revisions

class PipelineRunner:
    def __init__(self, llm_client: LLMClient, config: PipelineConfig = PipelineConfig()):
        self.llm_client = llm_client
        self.config = config
        self.architect = ArchitectAgent(llm_client)
        self.writer = WriterAgent(llm_client)
        self.auditor = ContinuityAuditor(llm_client)
        self.reviser = ReviserAgent(llm_client)
        self.radar = RadarAgent(llm_client)

    def run(self, book_id: str, chapter_num: int, book_title: str, genre: str, previous_summary: str = "", current_state: str = "") -> Dict[str, Any]:
        # 1. 雷达扫描（可选）
        if self.config.radar_enabled:
            radar_result = self.radar.run(None)
            # 这里可以使用雷达结果指导创作

        # 2. 建筑师规划章节结构
        architect_context = type('obj', (object,), {
            'book_id': book_id,
            'chapter_num': chapter_num,
            'kwargs': {
                'book_title': book_title,
                'genre': genre,
                'previous_summary': previous_summary
            }
        })
        architect_result = self.architect.run(architect_context)

        # 3. 写手生成正文
        writer_context = type('obj', (object,), {
            'book_id': book_id,
            'chapter_num': chapter_num,
            'kwargs': {
                'book_title': book_title,
                'genre': genre,
                'outline': architect_result['outline'],
                'word_count': 10000
            }
        })
        writer_result = self.writer.run(writer_context)

        # 4. 审计员检查连续性
        auditor_context = type('obj', (object,), {
            'book_id': book_id,
            'chapter_num': chapter_num,
            'kwargs': {
                'book_title': book_title,
                'chapter_content': writer_result['content'],
                'previous_summary': previous_summary,
                'current_state': current_state
            }
        })
        audit_result = self.auditor.run(auditor_context)

        # 5. 修订循环
        revisions = 0
        content = writer_result['content']
        while not audit_result['passed'] and revisions < self.config.max_revisions:
            reviser_context = type('obj', (object,), {
                'book_id': book_id,
                'chapter_num': chapter_num,
                'kwargs': {
                    'book_title': book_title,
                    'chapter_content': content,
                    'audit_result': audit_result
                }
            })
            revise_result = self.reviser.run(reviser_context)
            content = revise_result['content']
            
            # 重新审计
            auditor_context.kwargs['chapter_content'] = content
            audit_result = self.auditor.run(auditor_context)
            revisions += 1

        return {
            'chapter_num': chapter_num,
            'content': content,
            'word_count': len(content),
            'audit_score': audit_result['score'],
            'revisions': revisions
        }
