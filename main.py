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
            "answers": [normalize(a) for a in answers]
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
def start(source: str = Form("questions"), count: int = Form(3)):
    global quiz_questions, user_answers, index

    selected_source = next((item for item in source_files if item["key"] == source), source_files[0])
    try:
        questions = load_csv(selected_source["filename"])
    except:
        questions = []

    requested_count = max(1, count)
    sample_count = min(requested_count, len(questions))
    quiz_questions = random.sample(questions, sample_count) if questions else []
    user_answers = []
    index = 0

    return RedirectResponse("/quiz", status_code=303)


@app.get("/quiz", response_class=HTMLResponse)
def quiz(request: Request):
    if index >= len(quiz_questions):
        return RedirectResponse("/result", status_code=303)

    q = quiz_questions[index]

    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "question": q["question"],
        "q_index": index + 1,
        "total": len(quiz_questions)
    })


@app.post("/answer")
def answer(user_answer: str = Form(...)):
    global index

    cleaned_answer = normalize(user_answer)
    correct = quiz_questions[index]["answers"]
    user_answers.append({
        "question": quiz_questions[index]["question"],
        "user": cleaned_answer,
        "correct": correct
    })

    index += 1
    return RedirectResponse("/quiz", status_code=303)


@app.get("/result", response_class=HTMLResponse)
def result(request: Request):
    score = 0

    for item in user_answers:
        if normalize(item["user"]) in item["correct"]:
            score += 1

    return templates.TemplateResponse("result.html", {
        "request": request,
        "answers": user_answers,
        "score": score,
        "total": len(user_answers)
    })


# ---------------- HTML ----------------

# templates/home.html
"""

"""

# templates/quiz.html
"""

"""

# templates/result.html
"""

"""
