from pydantic_settings import BaseSettings

class WorkflowConfig(BaseSettings):
    max_retries: int = 3
    timeout: int = 300
    
    class Config:
        env_file = ".env"
        env_prefix = "novel_write_workflow_"
        case_sensitive = False
