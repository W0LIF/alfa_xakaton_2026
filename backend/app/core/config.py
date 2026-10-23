from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_base_url: str = "https://api.alfahack-gateway26.ru/v1"
    llm_base_url_fallback: str | None = "https://changellenge.up.railway.app/v1"
    llm_api_key: str = "changeme"
    llm_mode: str = "real"

    llm_model_cheap: str = "google/gemma-4-26b-a4b-it"
    llm_model_universal: str = "qwen/qwen3.6-35b-a3b"
    llm_model_reasoning: str = "z-ai/glm-5.3-flash"
    llm_model_research: str = "deepseek/deepseek-v4.1-flash"
    llm_model_vision: str = "qwen/qwen3-vl-30b-a3b-instruct"
    llm_model_text: str = "moonshotai/kimi-k2.6"

    llm_daily_token_limit: int = 120_000
    llm_max_retries: int = 2

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"


settings = Settings()