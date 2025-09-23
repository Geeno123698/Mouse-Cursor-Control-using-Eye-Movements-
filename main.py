import cv2
import mediapipe as mp
import pyautogui
import time
import tkinter as tk
from PIL import Image, ImageTk
from threading import Thread
import sys
import io

if sys.stdout is not None and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

cam = cv2.VideoCapture(0)

screen_w, screen_h = pyautogui.size()

calibrated_pupil = None
calibration_frames = 0

last_click_time_left = 0
last_click_time_right = 0
click_cooldown = 0.5

cursor_speed = 5

root = tk.Tk()
root.title("تتبع العين")
root.geometry("800x600")

awareness_label = tk.Label(root, text="الإعاقة ليست إعاقة حركية وإنما الإعاقة إعاقة فكرية", font=("Arial", 14, "bold"), fg="red")
awareness_label.pack(pady=5)

video_label = tk.Label(root, width=640, height=480)
video_label.pack(pady=5)

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

tk.Button(button_frame, text="زيادة سرعة المؤشر", font=("Arial", 12), command=lambda: increase_cursor_speed()).pack(side="left", padx=10)
tk.Button(button_frame, text="إنقاص سرعة المؤشر", font=("Arial", 12), command=lambda: decrease_cursor_speed()).pack(side="left", padx=10)

def increase_cursor_speed():
    global cursor_speed
    if cursor_speed < 15:
        cursor_speed += 1

def decrease_cursor_speed():
    global cursor_speed
    if cursor_speed > 1:
        cursor_speed -= 1

def update_video():
    global calibrated_pupil, calibration_frames, last_click_time_left, last_click_time_right

    ret, image = cam.read()
    if not ret:
        root.after(10, update_video)
        return

    image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    processed_image = face_mesh.process(rgb_image)

    if processed_image.multi_face_landmarks:
        landmarks = processed_image.multi_face_landmarks[0].landmark

        left_pupil_x = (landmarks[133].x + landmarks[33].x) / 2
        left_pupil_y = (landmarks[159].y + landmarks[145].y) / 2

        if calibrated_pupil is None and calibration_frames < 30:
            calibration_frames += 1
            calibrated_pupil = (left_pupil_x, left_pupil_y)

        elif calibrated_pupil is not None:
            offset_x = left_pupil_x - calibrated_pupil[0]
            offset_y = left_pupil_y - calibrated_pupil[1]

            movement_x = int(offset_x * screen_w * cursor_speed * 0.2)
            movement_y = int(offset_y * screen_h * cursor_speed * 0.2)

            screen_x = max(10, min(screen_w - 10, pyautogui.position().x + movement_x))
            screen_y = max(10, min(screen_h - 10, pyautogui.position().y + movement_y))

            pyautogui.moveTo(screen_x, screen_y, duration=0.05)

        left_eye_distance = abs(landmarks[159].y - landmarks[145].y)
        right_eye_distance = abs(landmarks[386].y - landmarks[374].y)

        if left_eye_distance < 0.01 and (time.time() - last_click_time_left) > click_cooldown:
            Thread(target=pyautogui.click).start()
            last_click_time_left = time.time()

        if right_eye_distance < 0.01 and (time.time() - last_click_time_right) > click_cooldown:
            Thread(target=pyautogui.doubleClick).start()
            last_click_time_right = time.time()

    try:
        img = Image.fromarray(rgb_image)
        imgtk = ImageTk.PhotoImage(image=img)

        if video_label is not None:
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)

    except AttributeError:
        pass

    root.after(10, update_video)

update_video()
root.mainloop()
cam.release()