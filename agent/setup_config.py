#!/usr/bin/env python3
"""
JARVIS Agent Configuration Setup Script

This script helps you set up all required API keys and configurations
for the JARVIS agent in one place.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json


class JARVISConfigurator:
    """Configuration setup helper for JARVIS Agent"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.env_file = self.config_dir / ".env"
        self.config_file = self.config_dir / "config.json"
        
    def print_header(self):
        """Print setup header"""
        print("=" * 60)
        print("🤖 JARVIS Agent Configuration Setup")
        print("=" * 60)
        print("This script will help you configure all required API keys")
        print("and settings for your JARVIS agent.")
        print()
    
    def get_input_with_default(self, prompt: str, default: str = "", is_secret: bool = False) -> str:
        """Get user input with default value"""
        if default:
            prompt += f" [{default}]: "
        else:
            prompt += ": "
        
        if is_secret:
            import getpass
            value = getpass.getpass(prompt)
        else:
            value = input(prompt)
        
        return value.strip() or default
    
    def setup_openai_config(self) -> Dict[str, str]:
        """Setup OpenAI configuration"""
        print("🔑 OpenAI Configuration")
        print("-" * 30)
        
        api_key = self.get_input_with_default(
            "Enter your OpenAI API Key", 
            os.getenv("OPENAI_API_KEY", ""),
            is_secret=True
        )
        
        model = self.get_input_with_default(
            "Enter OpenAI Model", 
            os.getenv("LLM_MODEL", "gpt-4o-mini")
        )
        
        temperature = self.get_input_with_default(
            "Enter Temperature (0.0-2.0)", 
            os.getenv("LLM_TEMPERATURE", "0.7")
        )
        
        max_tokens = self.get_input_with_default(
            "Enter Max Tokens", 
            os.getenv("LLM_MAX_TOKENS", "2000")
        )
        
        return {
            "OPENAI_API_KEY": api_key,
            "LLM_MODEL": model,
            "LLM_TEMPERATURE": temperature,
            "LLM_MAX_TOKENS": max_tokens
        }
    
    def setup_google_nest_config(self) -> Dict[str, str]:
        """Setup Google Nest configuration"""
        print("\n🏠 Google Nest Configuration")
        print("-" * 35)
        print("Auto-discovery finds ALL thermostats automatically!")
        print("No device ID needed - works with unlimited thermostats!")
        print("See GOOGLE_NEST_SETUP.md for detailed instructions")
        print()
        
        access_token = self.get_input_with_default(
            "Enter Google Nest Access Token", 
            os.getenv("GOOGLE_NEST_ACCESS_TOKEN", ""),
            is_secret=True
        )
        
        project_id = self.get_input_with_default(
            "Enter Google Project ID", 
            os.getenv("GOOGLE_NEST_PROJECT_ID", "")
        )
        
        client_id = self.get_input_with_default(
            "Enter Google Client ID", 
            os.getenv("GOOGLE_NEST_CLIENT_ID", ""),
            is_secret=True
        )
        
        client_secret = self.get_input_with_default(
            "Enter Google Client Secret", 
            os.getenv("GOOGLE_NEST_CLIENT_SECRET", ""),
            is_secret=True
        )
        
        return {
            "GOOGLE_NEST_ACCESS_TOKEN": access_token,
            "GOOGLE_NEST_PROJECT_ID": project_id,
            "GOOGLE_NEST_CLIENT_ID": client_id,
            "GOOGLE_NEST_CLIENT_SECRET": client_secret
        }
    
    def setup_server_config(self) -> Dict[str, str]:
        """Setup server configuration"""
        print("\n🌐 Server Configuration")
        print("-" * 25)
        
        host = self.get_input_with_default(
            "Enter Server Host", 
            os.getenv("SERVER_HOST", "0.0.0.0")
        )
        
        port = self.get_input_with_default(
            "Enter Server Port", 
            os.getenv("SERVER_PORT", "8000")
        )
        
        debug = self.get_input_with_default(
            "Enable Debug Mode (true/false)", 
            os.getenv("DEBUG", "false")
        )
        
        return {
            "SERVER_HOST": host,
            "SERVER_PORT": port,
            "DEBUG": debug
        }
    
    def setup_memory_config(self) -> Dict[str, str]:
        """Setup memory configuration"""
        print("\n🧠 Memory Configuration")
        print("-" * 26)
        
        max_history = self.get_input_with_default(
            "Enter Max Conversation History", 
            os.getenv("MAX_CONVERSATION_HISTORY", "100")
        )
        
        context_window = self.get_input_with_default(
            "Enter Context Window Size", 
            os.getenv("CONTEXT_WINDOW_SIZE", "4000")
        )
        
        timeout = self.get_input_with_default(
            "Enter Conversation Timeout (seconds)", 
            os.getenv("CONVERSATION_TIMEOUT", "300")
        )
        
        return {
            "MAX_CONVERSATION_HISTORY": max_history,
            "CONTEXT_WINDOW_SIZE": context_window,
            "CONVERSATION_TIMEOUT": timeout
        }
    
    def create_env_file(self, config: Dict[str, str]):
        """Create .env file with configuration"""
        print(f"\n📝 Creating .env file at {self.env_file}")
        
        with open(self.env_file, 'w') as f:
            f.write("# JARVIS Agent Configuration\n")
            f.write("# Generated by setup_config.py\n")
            f.write("# DO NOT COMMIT TO VERSION CONTROL\n\n")
            
            # OpenAI Configuration
            f.write("# OpenAI Configuration\n")
            for key, value in config.items():
                if key.startswith("OPENAI_") or key.startswith("LLM_"):
                    f.write(f"{key}={value}\n")
            
            f.write("\n# Google Nest Configuration\n")
            f.write("# Auto-discovery finds all thermostats automatically\n")
            for key, value in config.items():
                if key.startswith("GOOGLE_NEST_"):
                    f.write(f"{key}={value}\n")
            
            f.write("\n# Server Configuration\n")
            for key, value in config.items():
                if key in ["SERVER_HOST", "SERVER_PORT", "DEBUG"]:
                    f.write(f"{key}={value}\n")
            
            f.write("\n# Memory Configuration\n")
            for key, value in config.items():
                if key in ["MAX_CONVERSATION_HISTORY", "CONTEXT_WINDOW_SIZE", "CONVERSATION_TIMEOUT"]:
                    f.write(f"{key}={value}\n")
        
        print(f"✅ .env file created successfully!")
    
    def create_config_json(self, config: Dict[str, str]):
        """Create config.json for easy access"""
        config_data = {
            "openai": {
                "api_key": config.get("OPENAI_API_KEY", ""),
                "model": config.get("LLM_MODEL", "gpt-4o-mini"),
                "temperature": float(config.get("LLM_TEMPERATURE", "0.7")),
                "max_tokens": int(config.get("LLM_MAX_TOKENS", "2000"))
            },
            "google_nest": {
                "access_token": config.get("GOOGLE_NEST_ACCESS_TOKEN", ""),
                "project_id": config.get("GOOGLE_NEST_PROJECT_ID", ""),
                "client_id": config.get("GOOGLE_NEST_CLIENT_ID", ""),
                "client_secret": config.get("GOOGLE_NEST_CLIENT_SECRET", ""),
                "auto_discovery": True
            },
            "server": {
                "host": config.get("SERVER_HOST", "0.0.0.0"),
                "port": int(config.get("SERVER_PORT", "8000")),
                "debug": config.get("DEBUG", "false").lower() == "true"
            },
            "memory": {
                "max_conversation_history": int(config.get("MAX_CONVERSATION_HISTORY", "100")),
                "context_window_size": int(config.get("CONTEXT_WINDOW_SIZE", "4000")),
                "conversation_timeout": int(config.get("CONVERSATION_TIMEOUT", "300"))
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"✅ config.json created successfully!")
    
    def validate_config(self, config: Dict[str, str]) -> bool:
        """Validate required configuration"""
        print("\n🔍 Validating Configuration")
        print("-" * 30)
        
        errors = []
        
        # Check OpenAI API Key
        if not config.get("OPENAI_API_KEY"):
            errors.append("❌ OpenAI API Key is required")
        else:
            print("✅ OpenAI API Key configured")
        
        # Check Google Nest (optional)
        if config.get("GOOGLE_NEST_ACCESS_TOKEN"):
            if not config.get("GOOGLE_NEST_PROJECT_ID"):
                errors.append("❌ Google Nest Project ID required when Access Token is provided")
            else:
                print("✅ Google Nest configuration looks good")
        else:
            print("⚠️  Google Nest not configured (optional)")
        
        # Check server config
        try:
            int(config.get("SERVER_PORT", "8000"))
            print("✅ Server configuration valid")
        except ValueError:
            errors.append("❌ Invalid server port")
        
        if errors:
            print("\n❌ Configuration Errors:")
            for error in errors:
                print(f"  {error}")
            return False
        else:
            print("\n✅ Configuration is valid!")
            return True
    
    def show_next_steps(self):
        """Show next steps to user"""
        print("\n🚀 Next Steps")
        print("-" * 20)
        print("1. Start the JARVIS agent server:")
        print("   python3 server_main.py")
        print()
        print("2. Open your web browser:")
        print("   http://localhost:8000")
        print()
        print("3. Or use the API:")
        print("   curl -X POST http://localhost:8000/chat \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"message\": \"Hello JARVIS!\", \"session_id\": \"test\"}'")
        print()
        print("4. For Google Nest setup, see: GOOGLE_NEST_SETUP.md")
        print()
        print("🔒 Your secrets are stored in .env file (already gitignored)")
        print("📄 Configuration summary saved in config.json")
    
    def run_setup(self):
        """Run the complete setup process"""
        self.print_header()
        
        # Collect all configuration
        config = {}
        config.update(self.setup_openai_config())
        config.update(self.setup_google_nest_config())
        config.update(self.setup_server_config())
        config.update(self.setup_memory_config())
        
        # Validate configuration
        if not self.validate_config(config):
            print("\n❌ Setup failed due to configuration errors.")
            return False
        
        # Create configuration files
        self.create_env_file(config)
        self.create_config_json(config)
        
        # Show next steps
        self.show_next_steps()
        
        return True


def main():
    """Main setup function"""
    configurator = JARVISConfigurator()
    
    try:
        success = configurator.run_setup()
        if success:
            print("\n🎉 JARVIS Agent setup completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Setup failed. Please fix the errors and try again.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
