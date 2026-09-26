import os
from dotenv import load_dotenv
import argparse
import pathspec
from readme_ai.core.parser import extract_code_skeleton
from readme_ai.ai.router import generate_documentation
from readme_ai.core.builder import generate_badges

load_dotenv()

def load_ignore_patterns(repo_path: str) -> pathspec.PathSpec:
    ignore_path = os.path.join(repo_path, ".readmeignore")
    if not os.path.exists(ignore_path):
        ignore_path = os.path.join(repo_path, ".gitignore")
        
    patterns = []
    if os.path.exists(ignore_path):
        with open(ignore_path, "r", encoding="utf-8") as f:
            patterns = f.read().splitlines()
            
    patterns.extend([".git/", "__pycache__/", "node_modules/", ".venv/", "env/"])
    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)

def scan_repository(repo_path: str) -> list[dict]:
    spec = load_ignore_patterns(repo_path)
    skeletons = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            if spec.match_file(rel_path):
                continue
                
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                skeleton = extract_code_skeleton(rel_path, content)
                if "error" not in skeleton and (skeleton["functions"] or skeleton["classes_or_types"]):
                    skeletons.append(skeleton)
            except Exception:
                continue
                
    return skeletons


def get_project_metadata(repo_path: str) -> str:
    """Reads configuration files to understand dependencies and installation steps."""
    config_files = ["pyproject.toml", "package.json", "requirements.txt", "Cargo.toml", "go.mod"]
    metadata = ""
    
    for config in config_files:
        file_path = os.path.join(repo_path, config)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                metadata += f"\n--- {config} ---\n"
                # Read only the first 2000 chars to avoid overflowing the 3B model's context limit
                metadata += f.read()[:2000] 
    
    return metadata if metadata else "No configuration files found."

def main():
    parser = argparse.ArgumentParser(description="AI-powered README generator.")
    parser.add_argument("repo_path", type=str, nargs="?", default=".", help="Path to the repository.")
    parser.add_argument("--cloud", action="store_true", help="Use cloud Gemini model instead of local Qwen.")
    args = parser.parse_args()
    
    repo_path = os.path.abspath(args.repo_path)
    repo_name = os.path.basename(repo_path)
    
    print(f"🔍 Scanning repository: {repo_name}...")
    skeletons = scan_repository(repo_path)
    
    # --- Extract metadata ---
    print(f"📦 Extracting project metadata...")
    metadata = get_project_metadata(repo_path)
    
    if not skeletons:
        print("No supported code files found to parse!")
        return
        
    print(f"Extracted structure from {len(skeletons)} files. Generating documentation...")
    
    # --- UPDATED: Pass metadata to the router ---
    sections = generate_documentation(skeletons, metadata, repo_name, use_local=not args.cloud)
    
    print(f"Generating dynamic Shields.io badges...")
    badges = generate_badges(skeletons, metadata)
    
    readme_path = os.path.join(repo_path, "README-Generated.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# {repo_name}\n\n")
        
        # Inject badges directly below the title
        if badges:
            f.write(f"{badges}\n\n")
            
        for sec in sections:
            f.write(f"## {sec.title}\n{sec.content}\n\n")
            
    print(f"Success! Documentation saved to {readme_path}")

if __name__ == "__main__":
    main()