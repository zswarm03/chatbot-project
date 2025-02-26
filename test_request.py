import requests

url = "http://127.0.0.1:5000/chat"
data = {"question": "What is Zhizhen Yang's experience?"}
response = requests.post(url, json=data)

print(response.status_code, response.json())

