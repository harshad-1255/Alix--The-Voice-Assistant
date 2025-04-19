import customtkinter as ctk
import tkinter as tk
import cv2
from PIL import Image, ImageTk
import threading
import time
import queue
import requests
from functions.online_ops import (
    find_my_ip, get_latest_news, get_random_advice, get_random_joke, 
    get_trending_movies, get_weather_report, play_on_youtube, 
    search_on_google, search_on_wikipedia, send_email, send_whatsapp_message
)
import pyttsx3
from decouple import config
from datetime import datetime
from functions.os_ops import (
    open_calculator, open_camera, open_cmd, open_notepad, open_discord
)
from random import choice
from utils import opening_text
from pprint import pprint
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import numpy as np

KEYWORDS = ["alex", "hey alex", "okay alex", "can you hear me alex" , "alex are you here" , "alex you up"]

def detect_keyword(text):
    return any(keyword in text.lower() for keyword in KEYWORDS)

USERNAME = config('USER')
BOTNAME = config('BOTNAME')

engine = pyttsx3.init('sapi5')
engine.setProperty('rate', 190)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

class VideoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Alex")
        self.geometry("800x600")
        
        self.configure(fg_color="black")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.video_canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.video_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.terminal = ctk.CTkTextbox(self, height=100, state="normal", fg_color="black", text_color="white")
        self.terminal.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.video = cv2.VideoCapture(r".\Assets\video.mp4")

        self.video_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.command_queue = queue.Queue()

        self.video_thread = threading.Thread(target=self.play_video)
        self.video_thread.daemon = True
        self.video_thread.start()

        self.alex_thread = threading.Thread(target=self.run_alex)
        self.alex_thread.daemon = True
        self.alex_thread.start()

        self.bind("<Configure>", self.on_resize)
        self.after(100, self.process_command_queue)

    def play_video(self):
        while True:
            ret, frame = self.video.read()
            if not ret:
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = self.resize_frame(frame)
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame))

            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            x = (canvas_width - photo.width()) // 2
            y = (canvas_height - photo.height()) // 2

            self.video_canvas.delete("all")
            self.video_canvas.create_image(x, y, image=photo, anchor=tk.NW)
            self.video_canvas.image = photo

            time.sleep(0.03)

    def resize_frame(self, frame):
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()
        
        scale_width = canvas_width / self.video_width
        scale_height = canvas_height / self.video_height
        scale = min(scale_width, scale_height)

        new_width = int(self.video_width * scale)
        new_height = int(self.video_height * scale)

        return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    def on_resize(self, event):
        self.video_canvas.config(width=event.width-20, height=event.height-120)

    def speak(self, text):
        self.terminal.insert("end", f"Assistant: {text}\n")
        self.terminal.see("end")
        engine.say(text)
        engine.runAndWait()

    def take_user_input(self, timeout=10):
        self.terminal.insert("end", "Listening for command...\n")
        self.terminal.see("end")

        model = Model(r".\Speech Recognition Model\vosk-model-en-in-0.5")
        recognizer = KaldiRecognizer(model, 16000)

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)

        try:
            start_time = time.time()
            self.terminal.insert("end", "Waiting for command...\n")
            self.terminal.see("end")
            audio_data = b''
            while True:
                if time.time() - start_time > timeout:
                    self.terminal.insert("end", "Input timeout\n")
                    self.terminal.see("end")
                    return 'None'

                data = stream.read(4096, exception_on_overflow=False)
                audio_data += data
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    recognized_text = result['text']
                    if recognized_text:
                        self.terminal.insert("end", f"Recognized: {recognized_text}\n")
                        self.terminal.see("end")
                        return recognized_text.lower()

        except Exception as e:
            self.terminal.insert("end", f"Error in speech recognition: {e}\n")
            self.terminal.see("end")
            return 'None'
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def process_command(self, query):
        if 'exit' in query or 'stop' in query or 'bye' in query:
            hour = datetime.now().hour
            if hour >= 21 or hour < 6:
                self.speak("Good night sir, take care!")
            else:
                self.speak('Have a good day sir! , See You Soon')
            self.quit()

        elif 'open notepad' in query:
            self.speak("Opening Notepad")
            open_notepad()

        elif f"{BOTNAME.lower()}" in query:
            self.speak('Yes Sir')

        elif f"hello {BOTNAME.lower()}" in query or "hello" in query:
            self.speak("Hello sir, how are you ?")

        elif "i am fine" in query:
            self.speak("That's great, sir")

        elif "how are you" in query:
            self.speak("Perfect, sir")

        elif "thank you" in query:
            self.speak("You are welcome, sir")

        elif 'open discord' in query:
            self.speak("Opening Discord")
            open_discord()

        elif 'open command prompt' in query or 'open cmd' in query:
            self.speak("Opening Command Prompt")
            open_cmd()

        elif 'open camera' in query:
            self.speak("Opening Camera")
            open_camera()

        elif 'open calculator' in query:
            self.speak("Opening Calculator")
            open_calculator()

        elif 'ip address' in query:
            ip_address = find_my_ip()
            self.speak(f'Your IP Address is {ip_address}.\nFor your convenience, I am printing it on the screen sir.')
            print(f'Your IP Address is {ip_address}')

        elif 'wikipedia' in query:
            self.speak('What do you want to search on Wikipedia, sir?')
            search_query = self.take_user_input().lower()
            results = search_on_wikipedia(search_query)
            self.speak(f"According to Wikipedia, {results}")
            self.speak("For your convenience, I am printing it on the screen sir.")
            print(results)

        elif 'youtube' in query:
            self.speak('What do you want to play on Youtube, sir?')
            video = self.take_user_input().lower()
            play_on_youtube(video)

        elif 'search on google' in query:
            self.speak('What do you want to search on Google, sir?')
            query = self.take_user_input().lower()
            search_on_google(query)

        elif "send whatsapp message" in query:
            self.speak('On what number should I send the message sir? Please enter in the console: ')
            number = input("Enter the number: ")
            self.speak("What is the message sir?")
            message = self.take_user_input().lower()
            send_whatsapp_message(number, message)
            self.speak("I've sent the message sir.")

        elif "send an email" in query:
            self.speak("On what email address do I send sir? Please enter in the console: ")
            receiver_address = input("Enter email address: ")
            self.speak("What should be the subject sir?")
            subject = self.take_user_input().capitalize()
            self.speak("What is the message sir?")
            message = self.take_user_input().capitalize()
            if send_email(receiver_address, subject, message):
                self.speak("I've sent the email sir.")
            else:
                self.speak("Something went wrong while I was sending the mail. Please check the error logs sir.")

        elif 'joke' in query:
            self.speak(f"Hope you like this one sir")
            joke = get_random_joke()
            self.speak(joke)
            self.speak("For your convenience, I am printing it on the screen sir.")
            pprint(joke)

        elif "advice" in query:
            self.speak(f"Here's an advice for you, sir")
            advice = get_random_advice()
            self.speak(advice)
            self.speak("For your convenience, I am printing it on the screen sir.")
            pprint(advice)

        elif "trending movies" in query:
            self.speak(f"Some of the trending movies are: {get_trending_movies()}")
            self.speak("For your convenience, I am printing it on the screen sir.")
            print(*get_trending_movies(), sep='\n')

        elif 'news' in query:
            self.speak(f"I'm reading out the latest news headlines, sir")
            self.speak(get_latest_news())
            self.speak("For your convenience, I am printing it on the screen sir.")
            print(*get_latest_news(), sep='\n')

        elif 'weather' in query:
            ip_address = find_my_ip()
            city = requests.get(f"https://ipapi.co/{ip_address}/city/").text
            self.speak(f"Getting weather report for your city {city}")
            weather, temperature, feels_like = get_weather_report(city)
            self.speak(f"The current temperature is {temperature}, but it feels like {feels_like}")
            self.speak(f"Also, the weather report talks about {weather}")
            self.speak("For your convenience, I am printing it on the screen sir.")
            print(f"Description: {weather}\nTemperature: {temperature}\nFeels like: {feels_like}")

        else:
            self.speak("I'm sorry, I didn't understand that command. Can you please repeat?")

    def run_alex(self):
        self.speak(f"System is Now Live, {BOTNAME} Initialized")
        
        model = Model(r".\Speech Recognition Model\vosk-model-en-in-0.5")
        recognizer = KaldiRecognizer(model, 16000)

        self.terminal.insert("end", f"{BOTNAME} is listening for keywords...\n")
        self.terminal.see("end")

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)

        try:
            while True:
                data = stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result['text']
                    if text:
                        if detect_keyword(text):
                            self.terminal.insert("end", f"Heard: {text}\n")
                            self.terminal.see("end")
                            self.speak(f"Yes, {USERNAME}")
                            command = self.take_user_input()
                            if command and command != 'None':
                                self.command_queue.put(command)
                            recognizer = KaldiRecognizer(model, 16000)  # Reset recognizer

                time.sleep(0.1)
        except Exception as e:
            self.terminal.insert("end", f"\nAn error occurred: {e}\n")
            self.terminal.see("end")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def process_command_queue(self):
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                self.process_command(command)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_command_queue)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = VideoApp()
    app.mainloop()
        
