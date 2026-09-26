# py-tree-sitter AST parsing logicimport os
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_go as tsgo
import tree_sitter_rust as tsrust
from tree_sitter import Language, Parser, Query, QueryCursor
import os

# 1. Map file extensions to their respective Tree-sitter language instances
LANGUAGE_MAP = {
    ".py": Language(tspython.language()),
    ".js": Language(tsjavascript.language()),
    ".go": Language(tsgo.language()),
    ".rs": Language(tsrust.language()),
}

# 2. Define structural queries for each language
# We use Tree-sitter's S-expression syntax to target functions, arrow functions, and methods
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
    Parses source code based on its extension and extracts top-level structural definitions.
    """
    _, ext = os.path.splitext(file_path)
    
    if ext not in LANGUAGE_MAP:
        return {"error": f"Unsupported file extension: {ext}"}

    # Initialize language and parser
    language = LANGUAGE_MAP[ext]
    parser = Parser(language)
    
    # Parse the code bytes into a syntax tree
    tree = parser.parse(file_content)
    
    # Initialize the query using the language-specific mapping
    query_string = QUERY_MAP.get(ext)
    query = Query(language, query_string)
    
    # Execute the query against the root node
    # Tree-sitter >= 0.22 returns a dictionary of lists for captures
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)
    
    extracted_data = {
        "file": file_path,
        "functions": [],
        "classes_or_types": []
    }
    
    # Process function names
    if "function.name" in captures:
        for node in captures["function.name"]:
            extracted_data["functions"].append(node.text.decode('utf8'))
            
    # Process class or struct names
    if "class.name" in captures:
        for node in captures["class.name"]:
            extracted_data["classes_or_types"].append(node.text.decode('utf8'))
            
    return extracted_data

# --- Quick Test ---
if __name__ == "__main__":
    # Test Python parsing
    py_code = b"""
    class CodeChunker:
        pass
    def generate_readme(repo_path: str):
        pass
    """
    print("Python Results:")
    print(extract_code_skeleton("test.py", py_code))
    
    # Test JS parsing
    js_code = b"""
    const buildAST = (code) => { return null; }
    function parseCode() {}
    class NodeProcessor {}
    """
    print("\nJavaScript Results:")
    print(extract_code_skeleton("test.js", js_code))