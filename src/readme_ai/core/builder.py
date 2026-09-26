# Markdown assembly and formatting
import re

def clean_scaffolding(text: str) -> str:
    """Removes bracketed model placeholders like '[[ Add ... ]]'."""
    return re.sub(r"\[\[.*?\]\]", "", text).strip()
def generate_badges(skeletons: list[dict], metadata: str) -> str:
    """Analyzes extracted skeletons and metadata to generate Shields.io badges."""
    badges = []
    
    # 1. Detect Languages from file extensions
    extensions = {skel['file'].split('.')[-1] for skel in skeletons}
    if 'py' in extensions:
        badges.append("![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)")
    if 'js' in extensions or 'jsx' in extensions:
        badges.append("![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)")
    if 'go' in extensions:
        badges.append("![Go](https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white)")
    if 'rs' in extensions:
        badges.append("![Rust](https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white)")
        
    # 2. Detect Frameworks & Tools from metadata
    metadata_lower = metadata.lower()
    if 'fastapi' in metadata_lower:
        badges.append("![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)")
    if 'streamlit' in metadata_lower:
        badges.append("![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)")
    if 'dspy' in metadata_lower:
        badges.append("![DSPy](https://img.shields.io/badge/Powered_by-DSPy-8E75B2?style=for-the-badge)")
    if 'tree-sitter' in metadata_lower:
        badges.append("![Tree-Sitter](https://img.shields.io/badge/AST_Parsing-Tree--Sitter-4CAF50?style=for-the-badge)")
        
    return " ".join(badges)