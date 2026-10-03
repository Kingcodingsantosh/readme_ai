# LiteLLM routing (Local vs Cloud)
import os
import dspy
from pydantic import BaseModel, Field

# 1. Define the Structured Output Schema
# DSPy automatically enforces this Pydantic schema when generating the response.
class ReadmeSection(BaseModel):
    title: str = Field(description="The heading of the README section (e.g., 'Overview', 'Architecture').")
    content: str = Field(description="The markdown content for this section, based on the codebase analysis.")

# 2. Define the DSPy Signature
class GenerateReadmeModule(dspy.Signature):
    """
    Generate professional README sections based on the extracted codebase skeleton.
    
    STRICT RULES:
    1. Do NOT output placeholder tags like '[[ ... ]]' or '[Insert X]'.
    2. Write final, production-ready markdown only.
    3. Determine the package installer strictly from pyproject.toml (e.g., pip for setuptools).
    4. Formatting: You MUST provide the actual terminal commands inside markdown code blocks (```bash) for the Installation and Usage sections.
    CRITICAL INSTRUCTIONS:
    1. Perspective: Write for an end-user using the software, not a developer modifying its source code.
    2. Installation: Do NOT instruct the user to manually create configuration files or copy dependencies (e.g., pyproject.toml). Only provide the basic install command (e.g., pip install readme-ai).
    3. Usage: Explain how to execute the main commands or launch the UI. Do not instruct the user to edit the source code.
    4. Always include a brief License section at the end referencing the MIT License.
    5. Full Stack Scope: Analyze the entire provided file tree. If frontend files are present alongside a backend, you MUST document the full stack, not just the backend.
    6. Environment Setup: If python-dotenv, .env.example, or external APIs are detected, you MUST include a dedicated "Environment Setup" step instructing the user to create a .env file and add their keys before running the app.
    7. Pathing Consistency: Maintain a strict, consistent working directory in all terminal commands. Do not duplicate path navigation (e.g., if you instruct the user to `cd backend`, subsequent commands must be relative to that folder, like `python app.py`).
    8. Structure Accuracy: Base the "Project Structure" exactly on the provided skeleton. Do not omit crucial files like requirements.txt, .env, or frontend directories. Do not include virtual environments like 'myvenv'.
    9. Perspective: Write for an end-user using the software. Do NOT instruct the user to manually create configuration files like pyproject.toml.
    10. Formatting: You MUST provide the actual terminal commands inside markdown code blocks (```bash) for the Installation and Usage sections.
    """
    code_skeleton = dspy.InputField(desc="Parsed AST skeleton of the target repository")
    project_metadata = dspy.InputField(desc="Metadata like package name and core dependencies")
    repository_name = dspy.InputField()
    
    sections: list[ReadmeSection] = dspy.OutputField(desc="The final, production-ready Markdown sections without placeholder text")

# 3. Configure the Model Router
def setup_llm_router(use_local: bool = True):
    """
    Configures the underlying language model for DSPy.
    Routes to a local Ollama model for privacy, or a cloud Gemini model for complex generation.
    """
    if use_local:
        lm = dspy.LM(
            model="openai/qwen2.5-coder:3b",
            api_base="http://localhost:11434/v1",
            api_key="ollama",
            max_tokens=2048
        )
    else:
        lm = dspy.LM(
            model="gemini/gemini-3.5-flash-lite", 
            api_key=os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY"),
            max_tokens=4096
        )
    
    return lm

# 4. Pipeline Execution
def generate_documentation(skeleton_data: dict, metadata: str, repo_name: str, use_local: bool = True) -> list[ReadmeSection]:
    """
    Executes the DSPy ChainOfThought pipeline to generate structured README sections.
    """
    # 1. Get the LLM instance without setting it globally
    lm = setup_llm_router(use_local=use_local)
    
    # 2. Use a context manager to safely apply the LLM to this specific thread
    with dspy.context(lm=lm):
        generator = dspy.ChainOfThought(GenerateReadmeModule)
        
        skeleton_str = str(skeleton_data)
        
        # Simple heuristic: 1 token is roughly 4 characters
        estimated_tokens = len(skeleton_str) / 4
        
        if use_local and estimated_tokens > 2000:
            raise ValueError("Codebase is too large for the local model's context window. Please toggle 'Use Cloud API'.")
            
        # Execute the generator inside the context
        response = generator(code_skeleton=skeleton_str, project_metadata=metadata, repository_name=repo_name)
        
        return response.sections


if __name__ == "__main__":
    sample_skeleton = {
        'file': 'test.py', 
        'functions': ['generate_readme'], 
        'classes_or_types': ['CodeChunker']
    }
    
    print("Initializing DSPy pipeline...")
    try:
        generated_sections = generate_documentation(sample_skeleton, "readme-ai", use_local=True)
        
        print("\n--- GENERATED README ---")
        for sec in generated_sections:
            print(f"\n## {sec.title}\n{sec.content}")
            
    except Exception as e:
        print(f"\nGeneration failed. Ensure Ollama is running and the model is pulled.")
        print(f"Error details: {e}")