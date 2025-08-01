from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

# 🧠 Sample Excel interview questions and ideal answers
excel_questions = [
    {
        "id": 0,
        "question": "What is the difference between VLOOKUP and INDEX-MATCH in Excel?",
        "ideal_answer": "VLOOKUP searches for a value in the first column of a range and returns a value in the same row. INDEX-MATCH is more flexible, allowing lookups both vertically and horizontally, and does not require the lookup column to be first."
    },
    {
        "id": 1,
        "question": "How would you find duplicate values in an Excel column?",
        "ideal_answer": "Use Conditional Formatting → Highlight Cells Rules → Duplicate Values or use COUNTIF to filter values that occur more than once."
    },
    {
        "id": 2,
        "question": "Explain how to use a Pivot Table in Excel.",
        "ideal_answer": "A Pivot Table allows you to summarize large datasets. You can drag fields into rows, columns, values, and filters to calculate sums, counts, averages, etc."
    }
]

# ✅ Save evaluation to a JSON file
def save_evaluation_to_file(question_id, user_answer, evaluation):
    log_entry = {
        "question_id": question_id,
        "user_answer": user_answer,
        "evaluation": evaluation
    }
    filename = "interview_logs.json"

    if os.path.exists(filename):
        with open(filename, "r+") as file:
            data = json.load(file)
            data.append(log_entry)
            file.seek(0)
            json.dump(data, file, indent=2)
    else:
        with open(filename, "w") as file:
            json.dump([log_entry], file, indent=2)

# ✅ Call Ollama's local API running 'phi'
def call_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "phi",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            return f"❌ Ollama error: {response.status_code} - {response.text}"
        result = response.json()
        return result.get("response", "").strip()

    except Exception as e:
        return f"❌ Exception while calling Ollama: {str(e)}"

# ✅ Serve the first question
@app.route("/start", methods=["GET"])
def start_interview():
    first_question = excel_questions[0]
    return jsonify({
        "question_id": first_question["id"],
        "question": first_question["question"]
    })

# ✅ Serve all questions (admin/testing)
@app.route("/questions", methods=["GET"])
def get_questions():
    return jsonify(excel_questions)

# ✅ Evaluate user's answer and return next question
@app.route("/answer", methods=["POST"])
def evaluate_answer():
    data = request.get_json()
    question_id = data.get("question_id")
    user_answer = data.get("answer", "")

    question = next((q for q in excel_questions if q["id"] == question_id), None)
    if not question:
        return jsonify({"error": "Invalid question ID"}), 400

    prompt = f"""
You are acting as a technical Excel interviewer.
Below is a candidate's response to a question, along with the ideal answer.
Your task is to **formally evaluate** the candidate's answer and provide:
1. **2 to 3 specific and constructive feedback points** that highlight strengths and areas for improvement.
2. A **final score out of 10** reflecting the answer's accuracy, completeness, and clarity.

Please follow this format:
Feedback for the previous question:
- Point 1
- Point 2
- Point 3 (optional)
Score: X/10

---
Question: {question['question']}
Ideal Answer: {question['ideal_answer']}
Candidate Answer: {user_answer}
"""

    evaluation = call_ollama(prompt)

    # Save the evaluation
    save_evaluation_to_file(question_id, user_answer, evaluation)

    current_index = excel_questions.index(question)
    if current_index + 1 < len(excel_questions):
        next_q = excel_questions[current_index + 1]
        return jsonify({
            "evaluation": evaluation,
            "next_question": next_q["question"],
            "next_qid": next_q["id"]
        })
    else:
        return jsonify({
            "evaluation": evaluation,
            "next_question": None,
            "next_qid": None
        })

if __name__ == "__main__":
    app.run(debug=True)
