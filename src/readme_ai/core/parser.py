# py-tree-sitter AST parsing and repository skeleton logic
import os
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_go as tsgo
import tree_sitter_rust as tsrust

# 1. Traversal filters
DEFAULT_IGNORES = {
    "venv", "myvenv", ".venv", "env", ".git", 
    "__pycache__", "node_modules", "dist", "build"
}
SUPPORTED_EXTENSIONS = {".py", ".js", ".go", ".rs", ".json", ".html", ".css", ".md", ".txt"}

# 2. Map file extensions to their respective Tree-sitter language instances
LANGUAGE_MAP = {
    ".py": Language(tspython.language()),
    ".js": Language(tsjavascript.language()),
    ".go": Language(tsgo.language()),
    ".rs": Language(tsrust.language()),
}

# 3. Define structural queries for each language
QUERY_MAP = {
    ".py": """
        (function_definition name: (identifier) @function.name)
        (class_definition name: (identifier) @class.name)
    """,
    ".js": """
        (function_declaration name: (identifier) @function.name)
        (variable_declarator name: (identifier) @function.name value: [(arrow_function) (function_expression)])
        (method_definition name: (property_identifier) @function.name)
        (class_declaration name: (identifier) @class.name)
    """,
    ".go": """
        (function_declaration name: (identifier) @function.name)
        (method_declaration name: (field_identifier) @function.name)
        (type_declaration (type_spec name: (type_identifier) @class.name))
    """,
    ".rs": """
        (function_item name: (identifier) @function.name)
        (struct_item name: (type_identifier) @class.name)
    """
}

def extract_code_skeleton(file_path: str, file_content: bytes) -> dict:
    """
    Parses code files using Tree-sitter or extracts key metadata from config/asset files.
    """
    _, ext = os.path.splitext(file_path)
    filename = os.path.basename(file_path)

    # For non-code assets (e.g., manifest.json, requirements.txt, HTML/CSS)
    if ext not in LANGUAGE_MAP:
        if ext in SUPPORTED_EXTENSIONS:
            content_snippet = ""
            # Inspect high-signal configuration files for context
            if filename in {"manifest.json", "package.json", "requirements.txt", ".env.example"}:
                content_snippet = file_content[:1000].decode("utf-8", errors="ignore").strip()
            return {
                "file": file_path,
                "type": "configuration_or_asset",
                "details": content_snippet or f"{ext} source file"
            }
        return {"error": f"Unsupported file extension: {ext}"}

    # Initialize Tree-sitter language and parser
    language = LANGUAGE_MAP[ext]
    parser = Parser(language)
    tree = parser.parse(file_content)

    query_string = QUERY_MAP.get(ext)
    query = Query(language, query_string)
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    extracted_data = {
        "file": file_path,
        "functions": [],
        "classes_or_types": []
    }

    if "function.name" in captures:
        for node in captures["function.name"]:
            extracted_data["functions"].append(node.text.decode("utf-8"))

    if "class.name" in captures:
        for node in captures["class.name"]:
            extracted_data["classes_or_types"].append(node.text.decode("utf-8"))

    return extracted_data


def generate_repo_skeleton(repo_path: str) -> str:
    """
    Walks the repository, applies exclusion rules, builds an ASCII file tree,
    and returns a combined structural summary for LLM context.
    """
    tree_lines = []
    structural_summaries = []

    for root, dirs, files in os.walk(repo_path):
        # Prune ignored directories in-place to stop os.walk from recursing into them
        dirs[:] = [
            d for d in dirs 
            if d not in DEFAULT_IGNORES and not d.endswith(".egg-info")
        ]

        rel_dir = os.path.relpath(root, repo_path)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        indent = "    " * depth

        if rel_dir != ".":
            tree_lines.append(f"{indent[:-4]}└── {os.path.basename(root)}/")

        for f in sorted(files):
            _, ext = os.path.splitext(f)
            if ext in SUPPORTED_EXTENSIONS:
                tree_lines.append(f"{indent}├── {f}")
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, repo_path)

                try:
                    with open(full_path, "rb") as file_obj:
                        content = file_obj.read()
                    summary = extract_code_skeleton(rel_path, content)
                    if "error" not in summary:
                        structural_summaries.append(str(summary))
                except Exception:
                    continue

    full_tree = "\n".join(tree_lines)
    full_ast = "\n".join(structural_summaries)

    return f"DIRECTORY STRUCTURE:\n{full_tree}\n\nEXTRACTED CODE/FILE DETAILS:\n{full_ast}"


if __name__ == "__main__":
    # Test directory walk and skeleton generation on current folder
    print(generate_repo_skeleton("."))