from tkinter import *
import math
from PIL import ImageTk, Image
import os
import time
import pygame
from threading import Thread

# Color and font constants
YELLOW="#FFFF00"
RED = "#e7305b"
GREEN = "#9bdeac"
BLACK = "#000000"
BLUE="#0000FF"
FONT_NAME = "Courier"


WORK_MIN = 25
SHORT_BREAK_MIN = 5
LONG_BREAK_MIN=10

SESSIONS=3

# Global variables
reps = 0
timer = None
angle = 0
total_time = 0
session_step= 0

# Initialize pygame for sound
pygame.mixer.init()

# Function to play sound
def play_sound(file, callback=None, delay=2000):
    def check_playing():
        if not pygame.mixer.music.get_busy():  # Check if sound has finished
            if callback:
                window.after(delay, callback)  # Call the callback after a delay
        else:
            window.after(100, check_playing)

    def start_playing():
        pygame.mixer.music.load(file)  # Load sound file
        pygame.mixer.music.play()  # Play sound
        window.after(100, check_playing)  # Check sound status

    if not pygame.mixer.get_init():
        pygame.mixer.init()  # Initialize pygame mixer if not already done
    window.after(delay, start_playing)  # Start sound with a specified delay

# Rotate the pomodoro image continuously
def rotate_pomodoro(elapsed, duration, clockwise=True):
    global angle, pomodoro_image, rotated_image
    if duration == 0:  # Prevent division by zero
        duration = 1
    # Calculate the rotation angle based on elapsed time
    angle = (elapsed / duration) * 360 if clockwise else 360 - ((elapsed / duration) * 360)  # Calculate the angle based on elapsed time
    # Rotate the image
    rotated = pomodoro_image.rotate(angle, resample=Image.Resampling.BICUBIC)  # Rotate the image
    # Convert to a PhotoImage for tkinter
    rotated_image = ImageTk.PhotoImage(rotated)  # Convert rotated image for tkinter
    # Update the canvas with the rotated image
    canvas.itemconfig(image_id, image=rotated_image)  # Update image in canvas
    canvas.update_idletasks()  # Ensure the canvas refreshes

# Reset the timer
def reset_timer():
    global timer, angle, reps, session_step
    if timer:
        window.after_cancel(timer)  # Cancel any active timer
    canvas.itemconfig(timer_text, text="00:00")  # Reset displayed timer
    title_label.config(text="Timer", font=(FONT_NAME, 50, "bold"), fg=GREEN, bg=BLACK)  # Reset title
    angle = 0  # Reset rotation angle
    reps = 0  # Reset number of sessions
    session_step= 0   #Reset session step
    timer = None  # Clear timer
    rotated_image = ImageTk.PhotoImage(pomodoro_image)  # Reset image
    canvas.itemconfig(image_id, image=rotated_image)  # Update canvas image

def next_phase():
    """
    Advances to the next phase in the cycle. The cycle order is:
       0 → 1 → 2, then back to 0 (which increments the session count).
    """
    global session_step, reps
    session_step+=1
    if session_step>3:
        session_step=0
        reps+=1
    start_timer()    

def count_up(count, target):
    """
    Counts upward from 0 to target seconds. Used for the break phase.
    """
    global timer
    minutes=math.floor(count/60)
    seconds=count%60
    if seconds<10:
        seconds=f"0{seconds}"
    canvas.itemconfig(timer_text, text=f"{minutes}:{seconds}") 
    rotate_pomodoro(count, target, clockwise=True)
    if count<target:
        timer=window.after(1000, count_up, count + 1, target)
    else:
        play_sound(r"sound-6-95056.mp3", next_phase, delay=3000)      

# Count up then down mechanism (clockwise timer)
def count_up_then_down(count, target_time, is_counting_up):
    """
    For work phases:
      - When is_counting_up is True: count from 00:00 up to target_time (clockwise rotation).
      - When is_counting_up is False: count from target_time down to 00:00 (anti-clockwise rotation).
    """
    global timer
    minutes = math.floor(count / 60)
    secs = count % 60
    if secs < 10:
        secs = f"0{secs}"
    canvas.itemconfig(timer_text, text=f"{minutes}:{secs}")  # Update timer display
    rotate_pomodoro(count if is_counting_up else (target_time - count), target_time, clockwise=is_counting_up)
    if is_counting_up and count < target_time:
        timer = window.after(1000, count_up_then_down, count + 1, target_time, True)
    elif is_counting_up and count == target_time:
        play_sound(r"sound-6-95056.mp3", next_phase, delay=3000)    
    elif not is_counting_up and count > 0:
        timer = window.after(1000, count_up_then_down, count - 1, target_time, False)
    elif not is_counting_up and count == 0:
        play_sound(r"sound-6-95056.mp3", next_phase, delay=3000)

# Start the timer
def start_timer():
    """
    Determines which phase to run based on session_step:
      0 → Work (clockwise count up from 00:00 to 25:00)
      1 → Break (clockwise count up from 00:00 to 05:00)
      2 → Work (anti-clockwise count down from 25:00 to 00:00)
    After phase 2, the cycle completes and reps is incremented.
    """
    global total_time, session_step, reps
    work_sec = int(WORK_MIN * 60)
    short_break_sec = int(SHORT_BREAK_MIN * 60)
    long_break_sec = int(LONG_BREAK_MIN * 60)
    #check if we have reached the total sessions.
    if reps>=SESSIONS:
        title_label.config(text="Done", fg=BLUE)
        return
        
    # Define the sequence explicitly
    if session_step == 0:
        title_label.config(text="Work", fg=YELLOW)
        total_time = work_sec
        count_up_then_down(0, work_sec, True)      # First work session, clockwise
    elif session_step == 1:
        title_label.config(text="Short Break", fg=RED)
        total_time = short_break_sec
        count_up(0, short_break_sec)      # Break session, clockwise
    elif session_step == 2:
        title_label.config(text="Work", fg=GREEN)
        total_time = work_sec
        count_up_then_down(work_sec, work_sec, False)     # Second work session, anti-clockwise
    elif session_step == 3:
        title_label.config(text="Long Break", fg=BLUE)
        total_time = long_break_sec
        count_up(0, long_break_sec)

# Create the main window
window = Tk()
window.title("Pomodoro")
window.config(padx=100, pady=50, bg=BLACK)

# Title label
title_label = Label(text="Timer", font=(FONT_NAME, 50, "bold"), fg=BLUE, bg=BLACK)
title_label.grid(column=1, row=0)

# Canvas & image
canvas = Canvas(width=400, height=400, bg=BLACK, highlightthickness=0)
# Load & resize the pomodoro image
pomodoro_image = Image.open(r"tomato.png")
pomodoro_image = pomodoro_image.resize((200, 200))
rotated_image = ImageTk.PhotoImage(pomodoro_image)
image_id = canvas.create_image(200, 200, image=rotated_image)
timer_text = canvas.create_text(200, 200, text="00:00", fill="white", font=(FONT_NAME, 35, "bold"))
canvas.grid(column=1, row=1)

# Buttons
start_button = Button(text="Start", highlightbackground=BLACK, command=start_timer)
start_button.grid(column=0, row=2)

reset_button = Button(text="Reset", highlightbackground=BLACK, command=reset_timer)
reset_button.grid(column=2, row=2)

window.mainloop()
