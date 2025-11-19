# gemini_client.py - Optional direct API client for Gemini 3.0 Pro

import os
import google.generativeai as genai

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