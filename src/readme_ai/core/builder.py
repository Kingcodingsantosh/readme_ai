# Markdown assembly and formatting
import re

def clean_scaffolding(text: str) -> str:
    """Removes bracketed model placeholders like '[[ Add ... ]]'."""
    return re.sub(r"\[\[.*?\]\]", "", text).strip()
def generate_badges(code_skeleton: str) -> str:
    """Generates markdown badges based on extensions found in the codebase string."""
    badges = []
    
    # Search the raw directory tree string for file extensions
    if ".py" in code_skeleton:
        badges.append("![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)")
    if ".js" in code_skeleton:
        badges.append("![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)")
    if ".go" in code_skeleton:
        badges.append("![Go](https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white)")
    if ".rs" in code_skeleton:
        badges.append("![Rust](https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white)")
        
    return " ".join(badges)