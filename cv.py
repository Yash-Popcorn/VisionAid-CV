# MODULES
import cv2 
import base64
from openai import OpenAI
import os
from threading import Thread
import anthropic
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import FunctionTool
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from openai import OpenAI
from groq import Groq
import resend
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)

## ENVIRONMENT
os.environ['OPENAI_API_KEY'] = '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'
YOUR_API_KEY = "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"
groqClient = Groq(
    api_key="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",
)
perplexityClient = OpenAI(api_key="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", base_url="https://api.perplexity.ai")
resend.api_key = "re_EGudJtAD_DjBw9YNiho2dxAwVYAsZ3LsE"

## NOTE DOCS
documents = SimpleDirectoryReader("notes").load_data()
index = VectorStoreIndex.from_documents(documents)
print(documents, index)
def suggest_music(query):
    client_id = 'be0073f20a864bd8a15187d329363ee0'
    client_secret = '92b27a0cd69c4ba6953503975bbb3128'
    
    # Set up client credentials flow
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Search for tracks based on the query
    results = sp.search(q=query, limit=5, type='track')
    data = []
    # Display the suggested tracks
    for track in results['tracks']['items']:
        title = track['name']
        artist = track['artists'][0]['name']
        preview_url = track['preview_url']
        print(f'Track: {title} - Artist: {artist}')
        if preview_url:
            data.append(preview_url)
            print(f'Preview URL: {preview_url}\n')
        else:
            print('Preview not available\n')
    return data

def suggest_youtube_videos(query):
    API_KEY = 'AIzaSyDo-1hDtAFqHGDK-aVCpjWhCB6VFiwh_N8'
    BASE_URL = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': API_KEY,
        'maxResults': 5  # Number of videos to suggest
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        videos = response.json()['items']
        suggestions = []
        for video in videos:
            title = video['snippet']['title']
            video_id = video['id']['videoId']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            suggestions.append(video_url)
        return suggestions
    else:
        print('Failed to fetch YouTube videos')
        return []
    


## TOOLS
def describe_image(prompt_for_describe_image: str) -> str:
    global the_frame

    """
    Describe the image that is in the person's view. A prompt/question will be asked and the tool will answer that.
    """
    print(prompt_for_describe_image, " description description", the_frame)
    return request_vision(prompt_for_describe_image, the_frame)

def search_tool(what_to_search: str) -> str:
    """
    Search something based on what the user wants to search
    """

    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user."
            ),
        },
        {
            "role": "user",
            "content": (
                what_to_search
            ),
        },
    ]
    response = perplexityClient.chat.completions.create(
        model="sonar-small-online",
        messages=messages,
    )

    return response.choices[0].message.content

def text_tool(phone_number: str, thing_to_text: str) -> str:
    """
    Text tool to message someone something based on what the user wants to tell the person. SMS message
    """

    resp = requests.post('https://textbelt.com/text', {
    'phone': phone_number,
    'message': thing_to_text,
    'key': 'dea481c2b31d1e325bbbe2f8bbc93bdc7382fec68TjOiZ1RIL66gGtmCIWC1YYRZ',
    })
    print(resp.json())

    return 'I have texted. You wanted to text: ' + str(thing_to_text)

def email_tool(email: str, thing_to_email: str) -> str:
    """
    Email tool to email someone something based on what the user wants to tell the person. Email Tool
    """

    params = {
        "from": "PeronsalAssitant <onboarding@resend.dev>",
        "to": [email],
        "subject": "Message through PA",
        "html": f"<strong>{thing_to_email}</strong>",
    }
    email = resend.Emails.send(params)

    return 'I have emailed.'

def answer_tool(prompt_question: str) -> str:
    """
    Answer tool is answering a prompt that does not require using a search tool and nothing has to be searched. The prompt is whatever the user asks for. Its for answering questions
    """

    chat_completion = groqClient.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_question,
            }
        ],
        model="mixtral-8x7b-32768",
    )

    return chat_completion.choices[0].message.content

def note_tool(notes_to_take: str) -> str:
    """
    Take notes tool. Based on what the person wants to take a note on it will add it to a database
    """
    with open('notes/notes.text', 'a') as file:
        file.write(notes_to_take + '\n')

    # update the documents incase they have more conversations
    refreshed_docs = index.refresh_ref_docs(
        documents=documents, update_kwargs={"delete_kwargs": {"delete_from_docstore": True}}
    )   

    return 'Took the notes. The notes you took: ' + notes_to_take

def retrieve_notes_tool(thing_retrieve: str) -> str:
    """
    Retrieve notes from a text file which has information that can be retrieved from past conversations. Imagine this is a notepad where people can view past information they had.
    """

    # RAG for asking the text file and answer questions extremely quickly
    query_engine = index.as_query_engine()
    response = query_engine.query(thing_retrieve)

    return 'From notes I got: ' + str(response)

def add_youtube_video(url: str, file_path: str):
    """
    Add a new YouTube video URL to the text file.
    """
    with open(file_path, 'a') as file:
        file.write(url + '\n')

def recommend_youtube_videos(query: str) -> str:
    """
    Recommend YouTube videos based on the query the user wants to search. 
    Will provide URLs of YouTube videos.
    """
    response_arr = suggest_youtube_videos(query)

    # Assuming suggest_youtube_videos() returns a list of video URLs in response_arr

    # Path to the YouTube video text file
    file_path = 'videos.txt'

    # Iterating through the list of video URLs and adding each to the text file
    for url in response_arr:
        add_youtube_video(url, file_path)

    return str(response_arr)

def add_spotify_track(url: str, file_path: str):
    """
    Add a new Spotify track URL to the text file.
    """
    with open(file_path, 'a') as file:
        file.write(url + '\n')

def recommend_music(query: str) -> str:
    """
    Recommend Spotify tracks based on the query the user wants to search. 
    Will provide URLs of Spotify tracks.
    """
    response_arr = suggest_music(query)

    # Assuming suggest_spotify_tracks() returns a list of track URLs in response_arr

    # Path to the Spotify track text file
    file_path = 'videos.txt'

    # Iterating through the list of track URLs and adding each to the text file
    for url in response_arr:
        add_spotify_track(url, file_path)

    return str(response_arr)



## init all the tools
function_tool = FunctionTool.from_defaults(fn=describe_image)
function_tool1 = FunctionTool.from_defaults(fn=search_tool)
function_tool2 = FunctionTool.from_defaults(fn=text_tool)
function_tool3 = FunctionTool.from_defaults(fn=email_tool)
function_tool4 = FunctionTool.from_defaults(fn=answer_tool)
function_tool5 = FunctionTool.from_defaults(fn=note_tool)
function_tool6 = FunctionTool.from_defaults(fn=retrieve_notes_tool)
function_tool7 = FunctionTool.from_defaults(fn=recommend_youtube_videos)
function_tool8 = FunctionTool.from_defaults(fn=recommend_music)

# put tools in a list and create an agent
tools = [function_tool, function_tool1, function_tool2, function_tool3, function_tool4, function_tool5, function_tool6, function_tool7, function_tool8]
agent = OpenAIAgent.from_tools(tools, verbose=True)

the_frame = None
client = anthropic.Anthropic(
    api_key='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'
)

# LIVE STREAM
vid = cv2.VideoCapture(0) 

# FUNCTIONS
def request_vision(prompt: str, frame):
    print(frame)
    message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1024,
    messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": 'image/jpeg',
                            "data": encode_image(frame),
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    return message.content[0].text

# ENCODE THE IMAGE
def encode_image(image):
    cv2.imwrite("./screen1.jpg", image)
    print('image image image', image)
    _, buffer = cv2.imencode(".jpg", image)
    return base64.b64encode(buffer).decode('utf-8')

# record audio YE
def record_audio(filename, duration=10, samplerate=44100, channels=1):
    try:
        print("Recording...")
        recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=channels, dtype='int16')
        sd.wait()
        sf.write(filename, recording, samplerate)
        print("Recording saved as", filename)
    except Exception as e:
        print("Record Passed", e)

# transcribe the text
def transcribe_audio(filename):
    try:
        recognizer = sr.Recognizer()

        with sr.AudioFile(filename) as source:
            audio_data = recognizer.record(source)  

        text = recognizer.recognize_google(audio_data)
        response = agent.chat(text)
        #os.system(f'say "{response}"')

        print("Transcription:", text, " Response: ", response)
        with open("chat.txt", 'a') as file:
            file.write("Transcription: " + text + "\n")
            file.write("Response: " + str(response) + "\n\n")
            #print("Transcription:", text, " Response: ", response)  # Print transcription and response
    except Exception as e:
        print("Listened but did not do anything", e)

    return False  # No exit command found

def start_recording_loop():
    audio_filename = "output.wav"
    
    while True:
        record_audio(audio_filename)
        if transcribe_audio(audio_filename):
            break  # Exit the loop if exit command found

Thread(target=start_recording_loop).start()

def video_gen():
    global the_frame

    while(True): 
        success, frame = vid.read() 
        if not success: break
        else:
            the_frame = frame
            ret, buffer = cv2.imencode('.jpeg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index1():
    with open('chat.txt', 'r') as file:
        lines = file.readlines()
    return render_template('chats.html', lines=lines)

@app.route('/note')
def notepad():
    with open('notes/notes.text', 'r') as file:
        # Read the entire contents of the file
        lines = file.readlines()
    return render_template('notepad.html', lines=lines)

@app.route('/music')
def video_music():
    with open('videos.txt', 'r') as file:
        # Read the entire contents of the file
        lines = file.readlines()
    # with open('music.txt', 'r') as file:
    #     lines2 = file.readline()
    return render_template('video_music.html', lines=lines)

@app.route('/video_feed')
def video_feed():
    return Response(video_gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/retrieve', methods = ['POST'])
def retrieve():
    with open('chat.txt', 'r') as file:
        lines = file.readlines()

    return jsonify({
        'lines': lines
    })

#def run_app():

if __name__ == '__main__':
    app.run(debug=False)
#Thread(target=run_app).start()
  

