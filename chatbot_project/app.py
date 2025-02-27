import openai
import os
import requests
import fitz  # PyMuPDF for PDF processing
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Corrected OpenAI initialization

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template("index.html")  # Loads a frontend HTML page

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
        base_url,
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
            extracted_data[url] = soup.get_text(" ", strip=True)
        else:
            extracted_data[url] = "Error: Failed to fetch content."

    return extracted_data

# Function to generate AI response based on extracted data
def generate_response(question):
    resume_data = extract_resume_text("JobResume.pdf")
    website_data = scrape_website()

    website_content = " ".join([content for url, content in website_data.items()])
    combined_data = f"Resume Information: {resume_data} Website Information: {website_content}"

    prompt = f"""
    You are a chatbot assisting visitors on Zhizhen Yang's portfolio website. Your role is to answer questions about him. 
    When responding, provide a smooth, well-written paragraph that directly answers the user's question.

    Question: {question}
    Context: {combined_data}
    """

    response = openai_client.chat.completions.create(  # ✅ Corrected OpenAI v1.0+ Syntax
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI chatbot for Zhizhen Yang's portfolio, providing professional but friendly answers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question", "").strip()
    
    if not question:
        return jsonify({"answer": "Hi there! 👋 I'm here to answer any questions you have about Zhizhen Yang. Feel free to ask about his background, experience, or anything else!"})

    answer = generate_response(question)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

