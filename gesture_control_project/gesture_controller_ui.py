import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import time
import math
import os_actions_module as actions

# --- Constants ---
CAM_WIDTH, CAM_HEIGHT = 640, 480
UI_WIDTH, UI_HEIGHT = 1000, 600
VIDEO_X_OFFSET, VIDEO_Y_OFFSET = 30, 70
VIDEO_WIDTH, VIDEO_HEIGHT = 440, 330
MENU_X_OFFSET = 500
MENU_Y_OFFSET = 70

# Colors (B, G, R)
COLOR_BG = (29, 23, 20)        # Dark background
COLOR_MENU_BG = (43, 33, 29)   # Menu item background
COLOR_TEXT = (230, 230, 230)   # Light text
COLOR_HIGHLIGHT = (0, 190, 255) # Highlight yellow/orange
COLOR_ACCENT = (195, 128, 255)  # Pink/Purple accent
COLOR_GREEN = (0, 255, 0)
COLOR_WHITE = (255, 255, 255)

# Action Timing
ACTION_DELAY_SECONDS = 2.0  # Hold gesture for 2 seconds
SMOOTHING_FACTOR = 0.5      # For smoothing analog controls

# --- Tunable ranges for analog controls ---
BRIGHT_DIST_MIN = 30        # Min distance for "Thumb + Index"
BRIGHT_DIST_MAX = 200       # Max distance for "Thumb + Index"
VOL_Y_MIN = 100             # Pixel Y-coord for 100% volume (closer to top)
VOL_Y_MAX = 380             # Pixel Y-coord for 0% volume (closer to bottom)

# --- Helper Functions ---
def draw_ui(img, current_gesture_name, current_action_text, progress, menu_visible, video_frame, gesture_menu_dict):
    """Draws the entire UI onto the background image."""
    
    # 1. Background
    img[:] = COLOR_BG
    
    # 2. Header
    cv2.putText(img, "Gesture Menu", (MENU_X_OFFSET, MENU_Y_OFFSET - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_ACCENT, 2, cv2.LINE_AA)
    
    # 3. Video Feed
    video_frame_resized = cv2.resize(video_frame, (VIDEO_WIDTH, VIDEO_HEIGHT))
    cv2.rectangle(img, (VIDEO_X_OFFSET - 5, VIDEO_Y_OFFSET - 5),
                  (VIDEO_X_OFFSET + VIDEO_WIDTH + 5, VIDEO_Y_OFFSET + VIDEO_HEIGHT + 5), COLOR_ACCENT, 2, cv2.LINE_AA)
    img[VIDEO_Y_OFFSET:VIDEO_Y_OFFSET + VIDEO_HEIGHT, VIDEO_X_OFFSET:VIDEO_X_OFFSET + VIDEO_WIDTH] = video_frame_resized
    
    # 4. "Detected" Tag
    if current_gesture_name != "NO_HAND":
        tag_text = f"Detected: {current_gesture_name}"
        (w, h), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (VIDEO_X_OFFSET, VIDEO_Y_OFFSET + VIDEO_HEIGHT - h - 14),
                      (VIDEO_X_OFFSET + w + 10, VIDEO_Y_OFFSET + VIDEO_HEIGHT), (0, 0, 0, 0.5), -1)
        cv2.putText(img, tag_text, (VIDEO_X_OFFSET + 5, VIDEO_Y_OFFSET + VIDEO_HEIGHT - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 2, cv2.LINE_AA)

    # 5. Gesture Menu
    if menu_visible:
        y_pos = MENU_Y_OFFSET + 20
        item_height = 40
        item_width = UI_WIDTH - MENU_X_OFFSET - 30
        
        for key in ["Thumbs Up", "Thumbs Down", "One Finger", "Thumb + Index", "Fist", "Two Fingers", "Open Palm", "Thumb + Pinky", "Three Fingers", "Four Fingers"]:
            if key not in gesture_menu_dict:
                continue
            _, text, _, _, action_name = gesture_menu_dict[key]
            is_current = (key == current_gesture_name)
            bg_color = COLOR_HIGHLIGHT if is_current else COLOR_MENU_BG
            text_color = (0, 0, 0) if is_current else COLOR_TEXT
            
            cv2.rectangle(img, (MENU_X_OFFSET, y_pos),
                          (MENU_X_OFFSET + item_width, y_pos + item_height), bg_color, -1, cv2.LINE_AA)
            cv2.rectangle(img, (MENU_X_OFFSET, y_pos),
                          (MENU_X_OFFSET + item_width, y_pos + item_height), COLOR_TEXT, 1, cv2.LINE_AA)
            
            full_text = f"{text}: {action_name}" 
            cv2.putText(img, full_text, (MENU_X_OFFSET + 20, y_pos + 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2, cv2.LINE_AA)
            y_pos += item_height + 5

    # 6. Current Action Box
    action_box_y = UI_HEIGHT - 70
    cv2.rectangle(img, (VIDEO_X_OFFSET, action_box_y),
                  (UI_WIDTH - 30, action_box_y + 40), COLOR_MENU_BG, -1, cv2.LINE_AA)
    cv2.rectangle(img, (VIDEO_X_OFFSET, action_box_y),
                  (UI_WIDTH - 30, action_box_y + 40), COLOR_ACCENT, 1, cv2.LINE_AA)
    cv2.putText(img, "Current Action:", (VIDEO_X_OFFSET + 10, action_box_y + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_ACCENT, 2, cv2.LINE_AA)
    cv2.putText(img, current_action_text, (VIDEO_X_OFFSET + 200, action_box_y + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_WHITE, 2, cv2.LINE_AA)

    # 7. Progress Bar for one-shot actions
    if progress > 0:
        bar_x = VIDEO_X_OFFSET
        bar_y = VIDEO_Y_OFFSET + VIDEO_HEIGHT + 15
        bar_width = VIDEO_WIDTH
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + 10), COLOR_GREEN, -1)

def get_gesture_name(fingers, hand, detector):
    """Translates the cvzone fingersUp list into a gesture name."""
    
    lmList = hand["lmList"]
    
    if fingers == [1, 0, 0, 0, 0]:
        thumb_tip_y = lmList[4][1]
        thumb_mcp_y = lmList[2][1]
        if thumb_tip_y < thumb_mcp_y:
            return "Thumbs Up"
        else:
            return "Thumbs Down"

    if fingers == [0, 0, 0, 0, 0]:
        return "Fist"

    if fingers == [1, 0, 0, 0, 1]:
        return "Thumb + Pinky"
        
    if fingers == [0, 1, 1, 0, 0]:
        return "Two Fingers"
        
    if fingers == [1, 1, 1, 1, 1]:
        return "Open Palm"
        
    if fingers == [0, 1, 0, 0, 0]:
        return "One Finger"
        
    if fingers == [0, 1, 1, 1, 0]:
        return "Three Fingers"
        
    if fingers == [0, 1, 1, 1, 1]:
        return "Four Fingers"
    
    if fingers == [1, 1, 0, 0, 0]:
        return "Thumb + Index"
            
    return "UNKNOWN"

# --- Main Application ---
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera.")
        return
        
    cap.set(3, CAM_WIDTH)
    cap.set(4, CAM_HEIGHT)
    
    # OS Controller
    controller = actions.OSController()
    
    # --- GESTURE_MENU ---
    GESTURE_MENU = {
        "Thumbs Up":     ["👍", "Thumbs Up", controller.play_pause, True, "Play / Pause"],
        "Thumbs Down":   ["👎", "Thumbs Down", controller.next_track, True, "Next Track"],
        "Thumb + Pinky": ["🤙", "Thumb + Pinky", controller.open_chrome, True, "Open Google"],
        "Thumb + Index": ["👌", "Thumb + Index", "analog_brightness", False, "Adjust Brightness"],
        "Fist":          ["✊", "Fist", controller.lock_screen, True, "Lock Screen"],
        "Two Fingers":   ["✌️", "Two Fingers", controller.take_screenshot, True, "Screenshot"],
        "Open Palm":     ["✋", "Open Palm", "toggle_menu", False, "Toggle Menu"],
        "One Finger":    ["☝️", "One Finger", "analog_volume", False, "Adjust Volume"],
        "Three Fingers": ["", "Three Fingers", controller.open_calendar, True, "Open Calendar"],
        "Four Fingers":  ["", "Four Fingers", controller.open_camera, True, "Open Camera"],
        "UNKNOWN":       ["", "UNKNOWN", None, False, ""],
        "NO_HAND":       ["", "", None, False, ""]
    }
    
    # Use cvzone HandDetector
    detector = HandDetector(detectionCon=0.8, maxHands=1)
    
    # UI and State variables
    ui_image = np.zeros((UI_HEIGHT, UI_WIDTH, 3), dtype=np.uint8)
    menu_visible = True
    current_gesture_name = "NO_HAND"
    current_action_text = "---"
    
    # Timing and Action State
    last_gesture_name = "NO_HAND"
    gesture_start_time = 0
    action_triggered = False
    
    # Separate smoothing variables
    smoothed_volume = 50
    smoothed_brightness = 50

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to read frame, exiting.")
            break
            
        img = cv2.flip(img, 1) # Flip horizontally
        
        # --- Hand Detection ---
        hands, img_with_landmarks = detector.findHands(img, draw=True) # Draw on a copy
        
        action_progress = 0
        current_action_text = "---"

        if hands:
            hand = hands[0]
            fingers = detector.fingersUp(hand) 
            current_gesture_name = get_gesture_name(fingers, hand, detector)
            
            # --- Gesture Logic ---
            gesture_data = GESTURE_MENU.get(current_gesture_name, GESTURE_MENU["UNKNOWN"])
            action_func_or_name = gesture_data[2]
            is_one_shot = gesture_data[3]

            if action_func_or_name:
                if is_one_shot:
                    # --- One-Shot Action ---
                    action_func = action_func_or_name
                    if current_gesture_name != last_gesture_name:
                        gesture_start_time = time.time()
                        action_triggered = False
                    
                    time_held = time.time() - gesture_start_time
                    action_progress = min(time_held / ACTION_DELAY_SECONDS, 1.0)
                    current_action_text = f"Holding {current_gesture_name}... ({time_held:.1f}s)"
                    
                    if time_held >= ACTION_DELAY_SECONDS and not action_triggered:
                        
                        # --- SPECIAL CASE FOR CAMERA ---
                        # Check if the function to be called is 'open_camera'
                        if action_func == controller.open_camera:
                            current_action_text = "ACTION: Opening Camera... Releasing control."
                            # Draw this final message on the UI
                            draw_ui(ui_image, current_gesture_name, current_action_text, action_progress, menu_visible, img, GESTURE_MENU)
                            cv2.imshow("Gesture Controller", ui_image)
                            cv2.waitKey(1000) # Show message for 1 sec
                            
                            print("Releasing camera to open app...")
                            cap.release() # Release the webcam
                            cv2.destroyAllWindows() # Close our window
                            action_func() # Call open_camera()
                            action_triggered = True
                            break # Exit the main loop, as we've released the camera
                        
                        else: # Normal one-shot action
                            action_func() # Call the action function
                            current_action_text = f"ACTION: {current_gesture_name} Triggered!"
                            action_triggered = True
                        
                else:
                    # --- Analog or Toggle Action ---
                    action_triggered = False
                    
                    if action_func_or_name == "analog_volume":
                        lmList = hand["lmList"]
                        index_tip_y = lmList[8][1] 
                        # print(f"DEBUG: Volume Y-position: {index_tip_y:.0f}") 
                        vol_percent = np.interp(index_tip_y, [VOL_Y_MIN, VOL_Y_MAX], [100, 0])
                        smoothed_volume = (SMOOTHING_FACTOR * vol_percent) + ((1 - SMOOTHING_FACTOR) * smoothed_volume)
                        controller.set_volume(smoothed_volume)
                        current_action_text = f"Setting Volume: {smoothed_volume:.0f}%"
                        
                    elif action_func_or_name == "analog_brightness":
                        lmList = hand["lmList"]
                        length, _, _ = detector.findDistance(lmList[4][1:3], lmList[8][1:3], None)
                        # print(f"DEBUG: Brightness distance: {length:.0f}")
                        bright_percent = np.interp(length, [BRIGHT_DIST_MIN, BRIGHT_DIST_MAX], [0, 100])
                        smoothed_brightness = (SMOOTHING_FACTOR * bright_percent) + ((1 - SMOOTHING_FACTOR) * smoothed_brightness)
                        controller.set_brightness(smoothed_brightness)
                        current_action_text = f"Setting Brightness: {smoothed_brightness:.0f}%"

                    elif action_func_or_name == "toggle_menu":
                        current_action_text = "Toggle Menu"
                        if current_gesture_name != last_gesture_name:
                             menu_visible = not menu_visible
            else:
                 current_action_text = "No action assigned"
                 action_triggered = False
                 
        else:
            current_gesture_name = "NO_HAND"
            action_triggered = False
            smoothed_volume = 50
            smoothed_brightness = 50

        # --- Draw the Final UI ---
        draw_ui(ui_image, current_gesture_name, current_action_text, action_progress, menu_visible, img, GESTURE_MENU)
        
        # Draw landmarks on the video feed in the UI
        video_frame_with_landmarks = cv2.resize(img_with_landmarks, (VIDEO_WIDTH, VIDEO_HEIGHT))
        ui_image[VIDEO_Y_OFFSET:VIDEO_Y_OFFSET + VIDEO_HEIGHT, VIDEO_X_OFFSET:VIDEO_X_OFFSET + VIDEO_WIDTH] = video_frame_with_landmarks
        
        cv2.imshow("Gesture Controller", ui_image)
        
        # Update last gesture
        last_gesture_name = current_gesture_name

        # --- Quit ---
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print("Gesture controller closed.")

if __name__ == "__main__":
    main()