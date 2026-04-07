from typing import Dict, Any
import requests

class DetectionResult:
    def __init__(self, score: float, provider: str, detected_at: str, raw: Dict[str, Any] = None):
        self.score = score  # 0-1, higher = more likely AI
        self.provider = provider
        self.detected_at = detected_at
        self.raw = raw

class DetectorAgent:
    def __init__(self):
        pass

    async def detect_ai_content(self, config: Dict[str, Any], content: str) -> DetectionResult:
        """检测 AI 生成的内容"""
        import os
        from datetime import datetime

        api_key = os.environ.get(config.get('apiKeyEnv'))
        if not api_key:
            raise Exception(f"检测 API 密钥未找到。请在环境变量中设置 {config.get('apiKeyEnv')}。")

        detected_at = datetime.now().isoformat()

        provider = config.get('provider')
        api_url = config.get('apiUrl')

        if provider == 'gptzero':
            return await self._detect_gptzero(api_url, api_key, content, detected_at)
        elif provider == 'originality':
            return await self._detect_originality(api_url, api_key, content, detected_at)
        elif provider == 'custom':
            return await self._detect_custom(api_url, api_key, content, detected_at)
        else:
            raise Exception(f"不支持的检测提供商: {provider}")

    async def _detect_gptzero(self, api_url: str, api_key: str, content: str, detected_at: str) -> DetectionResult:
        """使用 GPTZero 检测"""
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": api_key
            },
            json={"document": content}
        )

        if not response.ok:
            raise Exception(f"GPTZero API 失败: {response.status_code} {response.text}")

        data = response.json()
        documents = data.get('documents', [])
        score = documents[0].get('completely_generated_prob', 0) if documents else 0

        return DetectionResult(score, "gptzero", detected_at, data)

    async def _detect_originality(self, api_url: str, api_key: str, content: str, detected_at: str) -> DetectionResult:
        """使用 Originality 检测"""
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={"content": content}
        )

        if not response.ok:
            raise Exception(f"Originality API 失败: {response.status_code} {response.text}")

        data = response.json()
        score = data.get('score', {}).get('ai', 0)

        return DetectionResult(score, "originality", detected_at, data)

    async def _detect_custom(self, api_url: str, api_key: str, content: str, detected_at: str) -> DetectionResult:
        """使用自定义检测 API"""
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={"content": content}
        )

        if not response.ok:
            raise Exception(f"检测 API 失败: {response.status_code} {response.text}")

        data = response.json()
        score = data.get('score', 0) if isinstance(data.get('score'), (int, float)) else 0

        return DetectionResult(score, "custom", detected_at, data)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """运行检测器 Agent"""
        content = context.get('content', '')
        config = context.get('detection_config', {
            'provider': 'custom',
            'apiUrl': 'https://api.example.com/detect',
            'apiKeyEnv': 'DETECTION_API_KEY'
        })

        try:
            import asyncio
            result = asyncio.run(self.detect_ai_content(config, content))
            return {
                'score': result.score,
                'provider': result.provider,
                'detected_at': result.detected_at,
                'raw': result.raw
            }
        except Exception as e:
            return {
                'score': 0.5,  # 默认值
                'provider': 'error',
                'detected_at': '',
                'error': str(e)
            }
