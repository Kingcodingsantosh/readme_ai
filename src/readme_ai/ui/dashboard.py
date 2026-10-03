# Streamlit web interface
import os
from dotenv import load_dotenv
import streamlit as st


from readme_ai.__main__ import scan_repository, get_project_metadata
from readme_ai.ai.router import generate_documentation
from readme_ai.core.builder import generate_badges
from readme_ai.core.parser import generate_repo_skeleton


load_dotenv()
st.set_page_config(page_title="README AI", page_icon="📝", layout="wide")

@st.cache_data(show_spinner=False)
def cached_scan(path: str):
    return generate_repo_skeleton(path)

st.title("📝 README Auto-Generator")
st.markdown("Instantly generate professional documentation for your codebases.")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Configuration")
    repo_path = st.text_input("Local Repository Path", value=".")
    
    st.markdown("---")
    st.subheader("AI Engine")
    # Toggle between local Qwen model and Gemini
    use_cloud = st.toggle("Use Cloud API (Gemini)", value=False)
    
    generate_btn = st.button("Generate README", type="primary", use_container_width=True)

# --- Main Execution Logic ---
if generate_btn:
    repo_path = os.path.abspath(repo_path.strip('"').strip("'"))
    repo_name = os.path.basename(repo_path)
    
    if not os.path.exists(repo_path):
        st.error("Invalid path. Please enter a valid directory on your machine.")
    else:
        # 1. Scan the codebase
        with st.spinner(f"🔍 Scanning {repo_name}..."):
            skeletons = cached_scan(repo_path)
            
            
        if not skeletons:
            st.warning("No supported code files found to parse in this directory.")
        else:
            # 2. Extract configuration data
            with st.spinner("Extracting metadata..."):
                metadata = get_project_metadata(repo_path)
            
            # 3. Generate documentation via AI
            model_name = "gemini-3.5-flash-lite" if use_cloud else "Local Qwen 3B"
            with st.spinner(f"⚙️ Generating docs using {model_name}..."):
                try:
                    sections = generate_documentation(skeletons, metadata, repo_name, use_local=not use_cloud)
                    
                    badges = generate_badges(skeletons)
                    
                    # 4. Assemble the Markdown
                    final_md = f"# {repo_name}\n\n"
                    if badges:
                        final_md += f"{badges}\n\n"
                    for sec in sections:
                        final_md += f"## {sec.title}\n{sec.content}\n\n"
                        
                    st.success("Documentation generated successfully!")
                    
                    # 5. Display Live Preview and Download Button
                    st.download_button(
                        label="📥 Download README.md",
                        data=final_md,
                        file_name="README-Generated.md",
                        mime="text/markdown"
                    )
                    
                    st.markdown("---")
                    st.subheader("Live Preview")
                    st.markdown(final_md, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Generation failed: {e}")