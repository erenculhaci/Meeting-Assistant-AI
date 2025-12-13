import os
from pathlib import Path


def load_env_file(env_path: str = None):
    if env_path is None:
        # Find project root (.env location)
        current_dir = Path(__file__).parent.parent
        env_path = current_dir / '.env'
    else:
        env_path = Path(env_path)
    
    if not env_path.exists():
        print(f"⚠️  .env file not found at {env_path}")
        return False
    
    # Load variables
    loaded_count = 0
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Set environment variable
                os.environ[key] = value
                loaded_count += 1
    
    print(f"Loaded {loaded_count} environment variables from .env")
    return True


# Auto-load when imported
if __name__ != "__main__":
    load_env_file()
