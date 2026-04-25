"""Configuration management for JARVIS Agent"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM configuration settings"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty
        }


class Config:
    """Configuration settings for the agent"""
    
    def __init__(self):
        # API Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Agent Configuration
        self.agent_name = os.getenv("AGENT_NAME", "JARVIS Assistant")
        self.conversation_timeout = int(os.getenv("CONVERSATION_TIMEOUT", "300"))  # seconds
        
        # LLM Configuration
        self.llm = LLMConfig(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            top_p=float(os.getenv("LLM_TOP_P", "1.0")),
            frequency_penalty=float(os.getenv("LLM_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.getenv("LLM_PRESENCE_PENALTY", "0.0")),
            timeout=int(os.getenv("LLM_TIMEOUT", "60"))
        )
        
        # Memory Configuration
        self.max_conversation_history = int(os.getenv("MAX_CONVERSATION_HISTORY", "100"))
        self.context_window_size = int(os.getenv("CONTEXT_WINDOW_SIZE", "20"))
        
        # Safety Configuration
        self.enable_guardrails = os.getenv("ENABLE_GUARDRAILS", "true").lower() == "true"
        self.default_permission_level = os.getenv("DEFAULT_PERMISSION_LEVEL", "read")
        
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Validate LLM settings
        if not 0 <= self.llm.temperature <= 2:
            raise ValueError("LLM temperature must be between 0 and 2")
        if not 0 <= self.llm.top_p <= 1:
            raise ValueError("LLM top_p must be between 0 and 1")
        if self.llm.max_tokens <= 0:
            raise ValueError("LLM max_tokens must be positive")
        
        return True
    
    def update_llm_config(self, **kwargs) -> None:
        """Update LLM configuration"""
        for key, value in kwargs.items():
            if hasattr(self.llm, key):
                setattr(self.llm, key, value)
        
        # Re-validate after update
        self.validate()
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration"""
        return self.llm
    
    def to_env_vars(self) -> Dict[str, str]:
        """Export configuration to environment variables"""
        return {
            "OPENAI_API_KEY": self.openai_api_key or "",
            "OPENAI_BASE_URL": self.openai_base_url,
            "AGENT_NAME": self.agent_name,
            "LLM_MODEL": self.llm.model,
            "LLM_TEMPERATURE": str(self.llm.temperature),
            "LLM_MAX_TOKENS": str(self.llm.max_tokens),
            "LLM_TOP_P": str(self.llm.top_p),
            "LLM_FREQUENCY_PENALTY": str(self.llm.frequency_penalty),
            "LLM_PRESENCE_PENALTY": str(self.llm.presence_penalty),
            "LLM_TIMEOUT": str(self.llm.timeout),
            "MAX_CONVERSATION_HISTORY": str(self.max_conversation_history),
            "CONTEXT_WINDOW_SIZE": str(self.context_window_size),
            "ENABLE_GUARDRAILS": str(self.enable_guardrails).lower(),
            "DEFAULT_PERMISSION_LEVEL": self.default_permission_level
        }


# Global config instance
config = Config()
