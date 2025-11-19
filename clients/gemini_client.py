# gemini_client.py - Direct API client for Gemini 3.0 Pro

import os
import uuid
import google.generativeai as genai

def gemini_propose(task_description: str, files: list[str]) -> str:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-pro-exp-0827")  # or 3.0 when live
    file_contents = "\n\n".join([f"--- {f} ---\n{open(f).read()}" for f in files if os.path.exists(f)])
    prompt = f"""You are Gemini agent in AI Factory OS.
Task: {task_description}
Output ONLY code proposals in this format:
```python:shared/proposals/gemini_{uuid.uuid4().hex[:8]}.py
# full code
```
"""
    response = model.generate_content(prompt + "\n\n" + file_contents)
    return response.text

def call_gemini_api(prompt: str, temperature: float = 0.2) -> str:
    """Direct call to Gemini 3.0 Pro API"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-3.0-pro-latest")

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=32768,
        )
    )
    return response.text

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gemini_client.py 'your prompt here'")
        sys.exit(1)
    prompt = sys.argv[1]
    result = call_gemini_api(prompt)
    print(result)