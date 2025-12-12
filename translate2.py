import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sounddevice as sd
import numpy as np
import queue
import threading
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import pygame
import tempfile
import os
import time

recognizer = sr.Recognizer()
translator = Translator()
pygame.mixer.init()

audio_queue = queue.Queue()
recording = False
audio_data = None

languages = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Japanese": "ja"
}

input_lang = "en"
output_lang = "ta"

def audio_callback(indata, frames, time_info, status):
    if recording:
        audio_queue.put(indata.copy())

def start_recording():
    global recording, audio_queue
    recording = True
    audio_queue = queue.Queue()
    status_label.config(text="🎤 Listening... Speak now!")
    threading.Thread(target=record_thread, daemon=True).start()

def record_thread():
    global audio_data
    with sd.InputStream(samplerate=16000, channels=1, callback=audio_callback):
        while recording:
            sd.sleep(100)
    all_data = []
    while not audio_queue.empty():
        all_data.append(audio_queue.get())
    if all_data:
        audio_np = np.concatenate(all_data, axis=0)
        audio_bytes = (audio_np * 32767).astype(np.int16).tobytes()
        audio_data = sr.AudioData(audio_bytes, 16000, 2)
        status_label.config(text="🛑 Recording stopped. Click 'Translate Speech'")

def stop_recording():
    global recording
    recording = False
    status_label.config(text="⏹️ Stopped recording.")

def translate_and_speak(text):
    global input_lang, output_lang
    if not text.strip():
        messagebox.showwarning("Warning", "Please type or record something!")
        return
    try:
        status_label.config(text="🌍 Translating...")
        translated = translator.translate(text, src=input_lang, dest=output_lang)
        recognized_text_label.config(text=f"✅ Input: {text}")
        translated_text_label.config(text=f"💬 Output: {translated.text}")
        history_box.configure(state="normal")
        history_box.insert(tk.END, f"Input ({input_lang_var.get()}): {text}\n")
        history_box.insert(tk.END, f"Output ({output_lang_var.get()}): {translated.text}\n\n")
        history_box.configure(state="disabled")
        history_box.yview(tk.END)
        status_label.config(text="🔊 Speaking as Sophia...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            audio_file = tmpfile.name
        tts = gTTS(translated.text, lang=output_lang, slow=True)
        tts.save(audio_file)
        pygame.mixer.quit()
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            root.update()
            pygame.time.wait(100)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        try:
            os.remove(audio_file)
        except Exception:
            pass
        status_label.config(text="✅ Done.")
    except Exception as e:
        messagebox.showerror("Error", f"Error: {e}")
        status_label.config(text="⚠️ Error occurred.")

def translate_speech():
    global audio_data
    if audio_data is None:
        messagebox.showwarning("Warning", "Please record your voice first!")
        return
    try:
        status_label.config(text="🎧 Recognizing speech...")
        text = recognizer.recognize_google(audio_data, language=input_lang)
        translate_and_speak(text)
        audio_data = None
    except sr.UnknownValueError:
        messagebox.showerror("Error", "Couldn't understand your voice. Try again.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Sophia - AI Voice & Text Translator")
root.geometry("650x750")
root.config(bg="#f9f9f9")

title_label = tk.Label(root, text="💫 Sophia - Your AI Translator", font=("Arial", 18, "bold"), bg="#f9f9f9", fg="#333")
title_label.pack(pady=10)

frame_lang = tk.Frame(root, bg="#f9f9f9")
frame_lang.pack(pady=5)

tk.Label(frame_lang, text="Input Language:", font=("Arial", 12), bg="#f9f9f9").grid(row=0, column=0, padx=10)
input_lang_var = tk.StringVar(value="English")
input_dropdown = ttk.Combobox(frame_lang, textvariable=input_lang_var, values=list(languages.keys()), state="readonly")
input_dropdown.grid(row=0, column=1)

tk.Label(frame_lang, text="Output Language:", font=("Arial", 12), bg="#f9f9f9").grid(row=0, column=2, padx=10)
output_lang_var = tk.StringVar(value="Tamil")
output_dropdown = ttk.Combobox(frame_lang, textvariable=output_lang_var, values=list(languages.keys()), state="readonly")
output_dropdown.grid(row=0, column=3)

tk.Label(root, text="Type text to translate:", font=("Arial", 12), bg="#f9f9f9").pack(pady=5)
text_entry = tk.Text(root, height=5, width=60, font=("Arial", 12))
text_entry.pack(pady=5)

button_frame = tk.Frame(root, bg="#f9f9f9")
button_frame.pack(pady=10)

start_button = tk.Button(button_frame, text="🎙️ Start Speaking", command=start_recording, bg="#4CAF50", fg="white", font=("Arial", 12), width=15)
start_button.grid(row=0, column=0, padx=5)

stop_button = tk.Button(button_frame, text="⏹️ Stop", command=stop_recording, bg="#F44336", fg="white", font=("Arial", 12), width=10)
stop_button.grid(row=0, column=1, padx=5)

speak_translate_button = tk.Button(button_frame, text="🗣️ Translate Speech", command=translate_speech, bg="#2196F3", fg="white", font=("Arial", 12), width=18)
speak_translate_button.grid(row=0, column=2, padx=5)

text_translate_button = tk.Button(root, text="💬 Translate Typed Text", command=lambda: set_lang_and_translate_text(), bg="#9C27B0", fg="white", font=("Arial", 12), width=25)
text_translate_button.pack(pady=10)

recognized_text_label = tk.Label(root, text="", font=("Arial", 12), bg="#f9f9f9")
recognized_text_label.pack(pady=5)

translated_text_label = tk.Label(root, text="", font=("Arial", 12, "italic"), fg="#555", bg="#f9f9f9")
translated_text_label.pack(pady=5)

status_label = tk.Label(root, text="💬 Ready to assist you.", font=("Arial", 12), fg="blue", bg="#f9f9f9")
status_label.pack(pady=10)

tk.Label(root, text="Translation History:", font=("Arial", 12, "bold"), bg="#f9f9f9").pack(pady=5)
history_box = scrolledtext.ScrolledText(root, width=75, height=15, state='disabled', font=("Arial", 10))
history_box.pack(pady=5)

def set_lang_and_translate_text():
    global input_lang, output_lang
    input_lang = languages[input_lang_var.get()]
    output_lang = languages[output_lang_var.get()]
    text = text_entry.get("1.0", tk.END)
    translate_and_speak(text)

root.mainloop()
