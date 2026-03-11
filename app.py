import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, send_file
import pdfplumber, docx, os, pandas as pd, re

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

skills_df = pd.read_csv("skills.csv")
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z ]", " ", text)
    return " ".join(text.split())
def extract_text(path):
    text = ""
    if path.endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    text += t
    else:
        doc = docx.Document(path)
        for p in doc.paragraphs:
            text += p.text
    return clean_text(text)
def extract_skills(text):
    return list({s for s in skills_df["skill"] if s in text})
def recommend_role(skills):
    scores = {}
    for _, r in skills_df.iterrows():
        if r["skill"] in skills:
            scores[r["role"]] = scores.get(r["role"], 0) + 1
    return max(scores, key=scores.get) if scores else "IT Professional"
def career_level(skills):
    if "deep learning" in skills or "nlp" in skills:
        return "Advanced"
    if "python" in skills and "sql" in skills:
        return "Intermediate"
    return "Beginner"
def ats_score(skills):
    return round((len(skills) / len(skills_df)) * 100, 2)
advanced_skills = [
    "machine learning", "deep learning", "nlp",
    "cloud computing", "docker", "kubernetes",
    "power bi", "tableau"
]

def improvement_plan(skills):
    return [s for s in advanced_skills if s not in skills][:6]
def generate_chart(score):
    plt.figure()
    plt.bar(["Career Readiness"], [score])
    plt.ylim(0, 100)
    plt.title("Career Readiness Score")
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path
def generate_pdf(data, chart):

    file = "report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "title", parent=styles["Title"],
        alignment=TA_CENTER, fontSize=22
    )

    subtitle = ParagraphStyle(
        "subtitle", parent=styles["BodyText"],
        alignment=TA_CENTER, fontSize=12
    )

    section = ParagraphStyle(
        "section", parent=styles["Heading2"]
    )

    body = styles["BodyText"]

    content = []

    content.append(Paragraph("HireSense AI", title))
    content.append(Paragraph(
        "Professional Resume & Career Intelligence Report",
        subtitle
    ))
    content.append(Spacer(1, 20))

    content.append(Paragraph("EXECUTIVE SUMMARY", section))
    content.append(Paragraph(
        f"<b>Recommended Role:</b> {data['role']}<br/>"
        f"<b>Career Level:</b> {data['level']}<br/>"
        f"<b>Career Readiness Score:</b> {data['ats']}%",
        body
    ))
    content.append(Spacer(1, 15))

    content.append(Image(chart, width=320, height=220))
    content.append(Spacer(1, 15))

    content.append(Paragraph("SKILL PROFILE", section))
    content.append(ListFlowable(
        [ListItem(Paragraph(s, body)) for s in data["skills"]]
    ))
    content.append(Spacer(1, 12))

    content.append(Paragraph("SKILL GAP ANALYSIS", section))
    content.append(ListFlowable(
        [ListItem(Paragraph(s, body)) for s in data["improve"]]
    ))
    content.append(Spacer(1, 12))

    content.append(Paragraph("CAREER IMPROVEMENT ROADMAP", section))
    content.append(Paragraph(
        "1. Learn missing technical skills using certified courses.<br/>"
        "2. Build 2–3 real-world projects.<br/>"
        "3. Gain internship or industry experience.<br/>"
        "4. Apply for higher-level roles.",
        body
    ))

    doc.build(content)
    return file
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        file = request.files["resume"]
        path = os.path.join("uploads", file.filename)
        file.save(path)

        text = extract_text(path)
        skills = extract_skills(text)

        data = {
            "role": recommend_role(skills),
            "level": career_level(skills),
            "skills": skills,
            "improve": improvement_plan(skills),
            "ats": ats_score(skills)
        }

        chart = generate_chart(data["ats"])
        generate_pdf(data, chart)

        return render_template("index.html", data=data)

    return render_template("index.html")

@app.route("/download")
def download():
    return send_file("report.pdf", as_attachment=True)

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
