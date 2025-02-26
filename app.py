import openai
import os
import requests
import fitz  # PyMuPDF for PDF processing
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Function to extract structured text from the resume PDF
def extract_resume_text(pdf_path):
    if not os.path.exists(pdf_path):
        return "Error: Resume file not found."
    
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
    except Exception as e:
        return f"Error reading the resume: {str(e)}"
    
    return text.strip()

# Function to scrape structured content from multiple sections of the website
def scrape_website():
    base_url = "https://www.zhizhenyang.com"
    sections = [
        base_url,  # Main page
        f"{base_url}/my-mindsets",
        f"{base_url}/mays-competencies",
        f"{base_url}/myers-briggs-assessment",
        f"{base_url}/strengthfinders",
        f"{base_url}/about-me"
    ]
    
    extracted_data = {}
    
    for url in sections:
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            extracted_data[url] = soup.get_text(" ", strip=True)  # Store text from each page
        else:
            extracted_data[url] = "Error: Failed to fetch content."
    
    return extracted_data

# Function to generate AI response based on extracted data
def generate_response(question):
    resume_data = extract_resume_text("JobResume.pdf")
    website_data = scrape_website()
    
    website_content = " ".join([f"{content}" for url, content in website_data.items()])
    
    combined_data = f"Resume Information: {resume_data} Website Information: {website_content}"
    
    prompt = f"Based on the following structured information about Zhizhen Yang, provide a smooth, well-written paragraph without special formatting that directly answers the user's question: {question} {combined_data}" 
    
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant that provides accurate, smoothly written responses based on Zhizhen Yang's resume and website, ensuring clarity and coherence."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "No question provided."})
    
    answer = generate_response(question)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True)
