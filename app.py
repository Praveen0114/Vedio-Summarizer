from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from yt_dlp import YoutubeDL
# from transcript import get_transcript
import re
import os

genai.configure(api_key=os.environ.get('API_KEY'))

app = Flask(__name__)
app.secret_key = os.environ.get('APP_KEY')
summary = None
transcript = None
Title = None
qa = []

def get_transcript(youtube_video_url):
    try:
        video_id = youtube_video_url.split("v=")[1]
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        transcript = " ".join([entry["text"] for entry in transcript_list])
        return transcript
    except Exception as e:
        return e

# def get_transcript(youtube_video_url):
#     try:
#         query = urlparse(youtube_video_url).query
#         video_id = parse_qs(query).get("v")
#         if video_id:
#             video_id = video_id[0]
#             transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
#             transcript = " ".join([entry["text"] for entry in transcript_list])
#             return transcript
#         else:
#             return None
#     except Exception as e:
#         print(f"Error fetching transcript: {e}")
#         return None

def get_Title(youtube_video_url):
    try:
        with YoutubeDL({'format': 'best', 'outtmpl': '%(title)s.%(ext)s'}) as ydl:
            info_dict = ydl.extract_info(youtube_video_url, download=False)
            return info_dict.get('title', 'Unknown Title')
    except Exception as e:
        return e

def generate_summary(transcript_text):
    structured_prompt = ("""You are a YouTube video summarizer. You will be taking the transcript text
                            and summarizing the entire video and providing the important summary in points
                            within 500 words. Please provide the summary of the text given here:  """
                         f"Here is the transcript:\n\n{transcript_text}")
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(structured_prompt)
        return response.text
    except Exception as e:
        return None


def answer_question(summary, question):
    structured_prompt = (f"You are an AI assistant that answers questions based on a provided summary.\n"
                         f"Here is the summary of the video:\n\n{summary}\n\n"
                         f"Answer the following question:\n{question}")

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(structured_prompt)
        return response.text
    except Exception as e:
        print(f"Error answering question: {e}")
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    global transcript, summary, qa, Title
    if request.method == 'POST':
        if 'youtube_video_url' in request.form:
            youtube_video_url = request.form['youtube_video_url']
            print(youtube_video_url)
            Title = get_Title(youtube_video_url)
            transcript = get_transcript(youtube_video_url)
            if transcript:
                summary = generate_summary(transcript)
                if summary == None:
                    flash("Error generating summary.", "danger")
            else:
                flash("Error fetching transcript.", "danger")
        elif 'question' in request.form and summary:
            question = request.form['question']
            summary = summary
            answer = answer_question(summary, question)
            if answer:
                qa.append({'question': question, 'answer': answer})
            else:
                flash("Error answering question.", "danger")

    return render_template('index.html', summary=summary, transcript=transcript, qa=qa)


@app.route('/download_summary')
def download_summary():
    if summary and transcript:
        summary_text = f"Video Summary:\n\n{summary}\n\nFull Transcript:\n\n{transcript}"
        filepath = f"{Title}_summary.txt"
        filepath = re.sub(r'[<>:"/\\|?*]', '', filepath)

        with open(filepath, 'w') as file:
            file.write(summary_text)
        
        return send_file(filepath, as_attachment=True)
    else:
        flash("No summary available to download.", "danger")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
