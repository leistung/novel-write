"""SkillLoader - 技能加载器，支持从外部目录动态加载题材技能"""
import os
import re
from typing import Dict, Any, Optional, List, Tuple
import json

class Skill:
    """技能对象"""
    def __init__(self, name: str, genre: str, content: str, 
                 metadata: Dict[str, Any], references: List[str]):
        self.name = name
        self.genre = genre
        self.content = content
        self.metadata = metadata
        self.references = references
    
    def get_identity(self) -> str:
        """提取身份卡部分"""
        match = re.search(r'## 身份卡\n\n(.*?)\n\n##', self.content, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def get_models(self, limit: int = 3) -> List[Tuple[str, str]]:
        """提取核心心智模型"""
        models = []
        matches = re.findall(r'### 模型\d+: (.*?)\n\*\*一句话\*\*：(.*?)\n', self.content)
        for model_name, model_desc in matches[:limit]:
            models.append((model_name.strip(), model_desc.strip()))
        return models
    
    def get_rules(self) -> List[str]:
        """提取写作规则"""
        match = re.search(r'## 规则清单\n\n(.*?)\n\n##', self.content, re.DOTALL)
        if match:
            rules = match.group(1).strip()
            return [r.strip() for r in rules.split('\n') if r.strip() and not r.strip().startswith('-')]
        return []
    
    def get_techniques(self) -> List[str]:
        """提取写作技巧"""
        match = re.search(r'## 技巧库\n\n(.*?)\n\n##', self.content, re.DOTALL)
        if match:
            techniques = match.group(1).strip()
            return [t.strip() for t in techniques.split('\n') if t.strip() and not t.strip().startswith('-')]
        return []

class SkillLoader:
    """技能加载器 - 从外部目录动态加载题材技能"""
    
    DEFAULT_SKILL_DIRS = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'skills'),
        os.path.join(os.path.expanduser('~'), '.novel-write', 'skills'),
    ]
    
    def __init__(self, skill_dirs: Optional[List[str]] = None):
        """初始化技能加载器
        
        Args:
            skill_dirs: 技能目录列表，默认为 DEFAULT_SKILL_DIRS
        """
        self._skill_dirs = skill_dirs or self.DEFAULT_SKILL_DIRS
        self._skills: Dict[str, Skill] = {}
        self._genre_map: Dict[str, List[str]] = {}
        self._load_skills()
    
    def _load_skills(self) -> None:
        """加载所有技能"""
        for skill_dir in self._skill_dirs:
            if not os.path.isdir(skill_dir):
                continue
            
            for item in os.listdir(skill_dir):
                item_path = os.path.join(skill_dir, item)
                if os.path.isdir(item_path):
                    self._load_skill_from_dir(item_path)
    
    def _load_skill_from_dir(self, skill_dir: str) -> None:
        """从目录加载技能"""
        skill_name = os.path.basename(skill_dir)
        skill_file = os.path.join(skill_dir, 'SKILL.md')
        
        if not os.path.exists(skill_file):
            return
        
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析元数据
            metadata = self._parse_metadata(content)
            genre = metadata.get('genre', '其他')
            
            # 加载参考资料
            references = self._load_references(skill_dir)
            
            # 创建技能对象
            skill = Skill(
                name=skill_name,
                genre=genre,
                content=content,
                metadata=metadata,
                references=references
            )
            
            # 注册技能
            self._skills[skill_name] = skill
            
            # 更新题材映射
            if genre not in self._genre_map:
                self._genre_map[genre] = []
            if skill_name not in self._genre_map[genre]:
                self._genre_map[genre].append(skill_name)
                
        except Exception as e:
            print(f"加载技能 {skill_name} 失败: {e}")
    
    def _parse_metadata(self, content: str) -> Dict[str, Any]:
        """解析技能元数据"""
        metadata = {}
        
        # 从内容开头提取元数据块
        match = re.search(r'---\n([\s\S]*?)\n---', content)
        if match:
            meta_str = match.group(1)
            for line in meta_str.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        
        return metadata
    
    def _load_references(self, skill_dir: str) -> List[str]:
        """加载参考资料"""
        references = []
        research_dir = os.path.join(skill_dir, 'research')
        
        if os.path.isdir(research_dir):
            for filename in os.listdir(research_dir):
                if filename.endswith('.md'):
                    file_path = os.path.join(research_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            references.append(f.read())
                    except Exception:
                        pass
        
        return references
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """根据名称获取技能"""
        return self._skills.get(name)
    
    def get_skill_by_genre(self, genre: str) -> Optional[Skill]:
        """根据题材获取技能
        
        Args:
            genre: 题材名称
            
        Returns:
            Skill: 匹配的技能对象，如果没有匹配则返回 None
        """
        # 精确匹配
        if genre in self._genre_map and self._genre_map[genre]:
            skill_name = self._genre_map[genre][0]
            return self._skills.get(skill_name)
        
        # 模糊匹配
        for g, skill_names in self._genre_map.items():
            if genre in g or g in genre:
                return self._skills.get(skill_names[0])
        
        return None
    
    def get_skills_by_keyword(self, keyword: str) -> List[Skill]:
        """根据关键词搜索技能"""
        results = []
        for skill in self._skills.values():
            if (keyword.lower() in skill.name.lower() or 
                keyword.lower() in skill.genre.lower() or 
                keyword.lower() in skill.content.lower()):
                results.append(skill)
        return results
    
    def list_skills(self) -> List[str]:
        """列出所有技能名称"""
        return list(self._skills.keys())
    
    def list_genres(self) -> List[str]:
        """列出所有可用题材"""
        return list(self._genre_map.keys())
    
    def generate_prompt_enhancement(self, genre: str) -> str:
        """根据题材生成提示词增强内容
        
        Args:
            genre: 题材名称
            
        Returns:
            str: 提示词增强内容，用于增强创作提示词
        """
        skill = self.get_skill_by_genre(genre)
        if not skill:
            return ""
        
        enhancement_parts = []
        
        # 提取身份卡部分
        identity = skill.get_identity()
        if identity:
            enhancement_parts.append(f"## 身份卡\n\n{identity}")
        
        # 提取核心心智模型
        models = skill.get_models(3)
        if models:
            model_lines = []
            for i, (model_name, model_desc) in enumerate(models, 1):
                model_lines.append(f"### 模型{i}: {model_name}")
                model_lines.append(f"**一句话**：{model_desc}")
            enhancement_parts.append("\n## 核心心智模型\n\n" + "\n\n".join(model_lines))
        
        # 提取写作规则
        rules = skill.get_rules()[:5]
        if rules:
            enhancement_parts.append("\n## 写作规则\n\n" + "\n".join([f"- {rule}" for rule in rules]))
        
        # 提取写作技巧
        techniques = skill.get_techniques()[:5]
        if techniques:
            enhancement_parts.append("\n## 写作技巧\n\n" + "\n".join([f"- {tech}" for tech in techniques]))
        
        # 添加参考资料
        if skill.references:
            enhancement_parts.append("\n## 参考资料\n\n" + "\n---\n".join(skill.references[:2]))
        
        return "\n".join(enhancement_parts).strip()
    
    def get_all_genre_enhancements(self) -> Dict[str, str]:
        """获取所有题材的提示词增强内容"""
        enhancements = {}
        for genre in self._genre_map:
            enhancements[genre] = self.generate_prompt_enhancement(genre)
        return enhancements

# 全局技能加载器实例
_skill_loader = None

def get_skill_loader() -> SkillLoader:
    """获取全局技能加载器实例"""
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader()
    return _skill_loader

def reload_skills() -> None:
    """重新加载所有技能"""
    global _skill_loader
    _skill_loader = SkillLoader()
    return _skill_loader.list_skills()