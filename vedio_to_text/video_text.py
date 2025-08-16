import speech_recognition as sr 
import moviepy.editor as mp
import google.generativeai as genai

vedio_file = input("Enter the path of the vedio : ")
clip = mp.VideoFileClip(vedio_file) 
 
clip.audio.write_audiofile(r"converted.wav")

r = sr.Recognizer()
audio = sr.AudioFile("converted.wav")

with audio as source:
  audio_file = r.record(source)
result = r.recognize_google(audio_file)

# exporting the result 
with open('recognized.txt',mode ='w') as file: 
   file.write("Recognized Speech:") 
   file.write("\n") 
   file.write(result) 
   print("ready!")


genai.configure(api_key='AIzaSyADTtPzT02KPjMj7vs9YvvWv1RSCoo2OVo')

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
        print(f"Error generating summary: {e}")
        return None

def answer_question(summary, question):
    structured_prompt = ("""You are an AI assistant that answers questions based on a provided summary. 
                            Here is the summary of the video:\n\n{summary}\n\n
                            Answer the following question:\n{question}""")
    
    prompt = structured_prompt.format(summary=summary, question=question)

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error answering question: {e}")
        return None

def save_to_file(transcript, summary):
    filename = f"summary.txt"
    with open(filename, 'w') as f:
        f.write(f"Transcript of th video:\n\n{transcript}\n\n")
        f.write("Summary of the video:\n\n")
        f.write(summary)
    print(f"Transcript and summary saved to {filename}")


with open('recognized.txt', 'r') as file:
    transcript = file.read()
summary = generate_summary(transcript)
print(summary)
if summary:
    save_to_file(transcript, summary)
    while True:
        question = input("What question would you like to ask about the summary? (type 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        
        answer = answer_question(summary, question)
        if answer:
            print("Answer:", answer)