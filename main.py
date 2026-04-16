from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import random
import re

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Storage
source_files = [
    {"key": "questions", "filename": "questions.csv", "label": "Всички въпроси"},
    {"key": "part1", "filename": "part1.csv", "label": "Министерства"},
    {"key": "part2", "filename": "part2.csv", "label": "Общински обекти"},
    {"key": "part3", "filename": "part3.csv", "label": "Болнични заведения"},
    {"key": "part4", "filename": "part4.csv", "label": "Спортни зали и стадиони"},
    {"key": "part5", "filename": "part5.csv", "label": "Учебни заведения"},
    {"key": "part6", "filename": "part6.csv", "label": "Хотели"},
]
source_counts = {}
quiz_questions = []
user_answers = []
index = 0
all_questions = []  # Store all loaded questions for generating wrong options
quiz_mode = "final"  # "immediate" for instant feedback, "final" for results after test


def normalize(text):
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[.,№]", "", cleaned)
    return cleaned


def load_csv(file_path="questions.csv"):
    df = pd.read_csv(file_path, encoding="cp1251", sep=";")

    questions = []

    for _, row in df.iterrows():
        answers = str(row["Отговори"]).split(",")

        questions.append({
            "question": row["Въпроси"],
            "answers": [normalize(a) for a in answers],
            "raw_answers": [a.strip() for a in answers]  # Keep raw answers for display
        })

    return questions


def load_source_counts():
    counts = {}
    for source in source_files:
        try:
            counts[source["key"]] = len(load_csv(source["filename"]))
        except:
            counts[source["key"]] = 0
    return counts


@app.on_event("startup")
def startup():
    global source_counts
    source_counts = load_source_counts()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "sources": source_files,
        "counts": source_counts,
        "default_source": "questions",
        "default_count": 3
    })


@app.post("/start")
def start(selected_sources: str = Form("questions"), count: int = Form(3), mode: str = Form("final")):
    global quiz_questions, user_answers, index, all_questions, quiz_mode
    quiz_mode = mode

    # Parse the selected sources (comma-separated)
    source_keys = [s.strip() for s in selected_sources.split(",") if s.strip()]
    
    # Load questions from all selected sources
    all_loaded_questions = []
    for source_key in source_keys:
        selected_source = next((item for item in source_files if item["key"] == source_key), None)
        if selected_source:
            try:
                questions = load_csv(selected_source["filename"])
                all_loaded_questions.extend(questions)
            except:
                pass
    
    requested_count = max(1, count)
    sample_count = min(requested_count, len(all_loaded_questions))
    quiz_questions = random.sample(all_loaded_questions, sample_count) if all_loaded_questions else []
    all_questions = all_loaded_questions  # Store all questions for generating wrong options
    user_answers = []
    index = 0

    # Generate multiple choice options for each question
    for i, q in enumerate(quiz_questions):
        correct_answer = q["raw_answers"][0]  # First answer is the correct one
        other_questions = [question for question in all_questions if question["question"] != q["question"]]
        
        # Get 3 random wrong answers from other questions
        wrong_answers = []
        if len(other_questions) >= 3:
            wrong_options = random.sample(other_questions, 3)
            wrong_answers = [opt["raw_answers"][0] for opt in wrong_options]
        else:
            wrong_answers = [opt["raw_answers"][0] for opt in other_questions]
            # If we still don't have 3, use other answers from the same source
            while len(wrong_answers) < 3 and len(q["raw_answers"]) > 1:
                wrong_answers.append(q["raw_answers"][min(len(wrong_answers), len(q["raw_answers"]) - 1)])
        
        # Combine and shuffle options
        all_options = [correct_answer] + wrong_answers[:3]
        random.shuffle(all_options)
        
        quiz_questions[i]["options"] = all_options
        quiz_questions[i]["correct_display"] = correct_answer

    return RedirectResponse("/quiz", status_code=303)


@app.get("/quiz", response_class=HTMLResponse)
def quiz(request: Request):
    if index >= len(quiz_questions):
        return RedirectResponse("/result", status_code=303)

    q = quiz_questions[index]

    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "question": q["question"],
        "options": q["options"],
        "correct_answer": q["correct_display"],
        "q_index": index + 1,
        "total": len(quiz_questions),
        "mode": quiz_mode
    })


@app.post("/answer")
def answer(selected_option: str = Form(...)):
    global index

    cleaned_answer = normalize(selected_option)
    correct = quiz_questions[index]["answers"]
    correct_display = quiz_questions[index]["correct_display"]
    is_correct = cleaned_answer in correct
    
    user_answers.append({
        "question": quiz_questions[index]["question"],
        "user": selected_option,
        "user_normalized": cleaned_answer,
        "correct": correct_display,
        "correct_normalized": correct,
        "is_correct": is_correct
    })

    index += 1
    return RedirectResponse("/quiz", status_code=303)


@app.get("/result", response_class=HTMLResponse)
def result(request: Request):
    score = sum(1 for item in user_answers if item["is_correct"])

    return templates.TemplateResponse("result.html", {
        "request": request,
        "answers": user_answers,
        "score": score,
        "total": len(user_answers)
    })



