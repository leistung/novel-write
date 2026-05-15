"""Celery应用配置"""
from celery import Celery
from config.settings import settings

# 创建Celery应用
celery_app = Celery(
    "novel_write",
    include=[
        "tasks.workflow_tasks",
    ]
)

# 配置Celery
celery_app.conf.update(
    broker_url=settings.CELERY_CONFIG["broker_url"],
    result_backend=settings.CELERY_CONFIG["result_backend"],
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务追踪
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3300,  # 55分钟软超时
    
    # Worker配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # 结果配置
    result_expires=3600 * 24 * 7,  # 结果保留7天
    result_extended=True,
    
    # 重试配置
    task_default_retry_delay=60,  # 默认60秒后重试
    task_max_retries=3,
    
    # 队列配置
    task_default_queue="default",
    task_routes={
        "tasks.workflow_tasks.*": {"queue": "workflow"},
    },
    
    #  beat配置（定时任务）
    beat_schedule={
        "cleanup-old-workflows": {
            "task": "tasks.workflow_tasks.cleanup_old_workflows",
            "schedule": 3600 * 24,  # 每天执行
        },
    },
)


@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    print(f"Request: {self.request!r}")
    return {"status": "ok"}
