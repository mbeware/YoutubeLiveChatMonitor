import importlib.util
import sys
from pathlib import Path
from typing import List
import tomllib  # Python 3.11+

# This will need to be rewritten. Many special cases arent managed. 

def load_modules_from_config(context):
    config = context["config"]
    modules_list = config.get("general", {}).get("modules_list", [])
    if not modules_list:
        return []

    loaded_modules = {}

    for module_name in modules_list:
        module_info = config.get(module_name)
        print(f"loading module {module_name}",end="")
        if not module_info or "file_path" not in module_info:
            raise ValueError(f"Invalid config for '{module_name}'")

        # Get the absolute path of the script's directory
        script_dir = Path(__file__).resolve().parent
        

        file_path = script_dir / "modules" / module_info["file_path"]
        
        if not file_path.exists():
            raise FileNotFoundError(f"Module file for {module_name} not found: {file_path}")

        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Error loading module '{module_name}'")

        module = importlib.util.module_from_spec(spec)

        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        loaded_modules[module_name] = module
        print(" .....loaded")

    return loaded_modules