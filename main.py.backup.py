from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Storage
all_questions = []
quiz_questions = []
user_answers = []
index = 0


def normalize(text):
    return text.strip().lower()


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


@app.on_event("startup")
def startup():
    global all_questions
    try:
        all_questions = load_csv()
    except:
        all_questions = []


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "count": len(all_questions)
    })


@app.get("/start")
def start():
    global quiz_questions, user_answers, index

    quiz_questions = random.sample(all_questions, min(3, len(all_questions)))
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

    correct = quiz_questions[index]["answers"]
    user_answers.append({
        "question": quiz_questions[index]["question"],
        "user": user_answer,
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
