import os
from flask import Flask, request, render_template, redirect, url_for
import speech_recognition as sr
import moviepy.editor as mp
import google.generativeai as genai

transcript = None
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv'}  # Allowed video formats

genai.configure(api_key='AIzaSyADTtPzT02KPjMj7vs9YvvWv1RSCoo2OVo')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_video(file_path):
    global transcript
    clip = mp.VideoFileClip(file_path)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], "converted.wav")
    clip.audio.write_audiofile(audio_path)

    # Transcribe audio to text
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        transcript = recognizer.recognize_google(audio_data)

    return transcript

def generate_summary(transcript_text):
    structured_prompt = ("""You are a YouTube video summarizer. Summarize the video in points
                            within 500 words based on the given transcript:\n\n""" + transcript_text)

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(structured_prompt)
        return response.text
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def answer_question(summary, question):
    prompt = (f"You are an AI assistant that answers questions based on the provided summary:\n\n{summary}\n\n"
              f"Question: {question}")

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error answering question: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'video' not in request.files:
            return "No video file found", 400

        file = request.files['video']
        if file.filename == '':
            return "No selected file", 400

        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            transcript = process_video(file_path)
            summary = generate_summary(transcript)

            if summary:
                return render_template("summary.html", transcript=transcript, summary=summary)
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_question():
    summary = request.form['summary']
    question = request.form['question']
    answer = answer_question(summary, question)
    return render_template("summary.html",transcript=transcript, summary=summary, answer=answer, question=question)

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
