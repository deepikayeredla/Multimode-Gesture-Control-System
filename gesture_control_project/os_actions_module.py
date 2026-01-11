import subprocess
import platform
import os
from pynput.keyboard import Key, Controller as KeyboardController
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import math

class OSController:
    """
    Handles all operating system level actions.
    This module is OS-dependent (primarily Windows).
    """
    def __init__(self):
        self.platform = platform.system()
        self.keyboard = KeyboardController()
        
        if self.platform == "Windows":
            # Initialize volume control for Windows
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
                self.vol_range_db = self.volume.GetVolumeRange() # (-74.0, 0.0, 1.0)
                self.min_vol_db = self.vol_range_db[0]
                self.max_vol_db = self.vol_range_db[1]
                print(f"Volume control initialized. Range: {self.vol_range_db}")
            except Exception as e:
                print(f"Error initializing Windows volume: {e}")
                print("Volume control will be disabled.")
                self.volume = None
        else:
            self.volume = None
            print(f"Volume control not implemented for {self.platform}")
            print("Brightness control will be disabled (sbc only supports Windows/Linux).")

    # --- Media Actions (using pynput for system-wide control) ---
    def play_pause(self):
        print("ACTION: Play/Pause")
        self.keyboard.press(Key.media_play_pause)
        self.keyboard.release(Key.media_play_pause)

    def next_track(self):
        print("ACTION: Next Track")
        self.keyboard.press(Key.media_next)
        self.keyboard.release(Key.media_next)

    # --- System Actions ---
    def take_screenshot(self):
        print("ACTION: Taking Screenshot")
        self.keyboard.press(Key.print_screen)
        self.keyboard.release(Key.print_screen)

    def lock_screen(self):
        print("ACTION: Locking Screen")
        if self.platform == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        elif self.platform == "Darwin": # macOS
            subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
        else: # Linux
            subprocess.run(["xdg-screensaver", "lock"])

    # --- Application Actions ---
    def open_chrome(self):
        print("ACTION: Opening Google Chrome")
        try:
            if self.platform == "Windows":
                subprocess.run(["start", "chrome"], shell=True)
            elif self.platform == "Darwin": # macOS
                subprocess.run(["open", "-a", "Google Chrome"])
            else: # Linux
                subprocess.run(["google-chrome"])
        except Exception as e:
            print(f"Error opening Chrome: {e}")

    def open_calendar(self):
        print("ACTION: Opening Calendar")
        try:
            if self.platform == "Windows":
                subprocess.run(["start", "outlookcal:"], shell=True) # Opens Windows Calendar
            elif self.platform == "Darwin": # macOS
                subprocess.run(["open", "-a", "Calendar"])
            else: # Linux
                print("Cannot open calendar on Linux (no standard command)")
        except Exception as e:
            print(f"Error opening calendar: {e}")

    def open_camera(self):
        print("ACTION: Opening Camera")
        try:
            if self.platform == "Windows":
                subprocess.run(["start", "microsoft.windows.camera:"], shell=True)
            elif self.platform == "Darwin": # macOS
                subprocess.run(["open", "-a", "Photo Booth"])
            else: # Linux
                subprocess.run(["cheese"]) # Common Linux camera app
        except Exception as e:
            print(f"Error opening camera: {e}")
    
    # --- Analog Controls ---
    def set_volume(self, percent):
        """Sets the system volume (0-100)."""
        if self.volume:
            try:
                # Clamp value
                percent = max(0, min(100, percent))
                
                # Convert linear percentage to dB (logarithmic)
                # This formula maps 0-100% to the decibel range
                if percent == 0:
                    db = self.min_vol_db
                else:
                    # S-curve interpolation is better, but this is a good approximation
                    db = self.min_vol_db + (self.max_vol_db - self.min_vol_db) * (percent / 100)
                
                # Ensure we don't go out of bounds
                db = max(self.min_vol_db, min(self.max_vol_db, db))

                self.volume.SetMasterVolumeLevel(db, None)
                print(f"Set Volume: {percent:.0f}% ({db:.2f} dB)")
            except Exception as e:
                print(f"Error setting volume: {e}")
        else:
            print(f"Volume control disabled. Set Volume: {percent:.0f}%")

    def set_brightness(self, percent):
        """Sets the screen brightness (0-100)."""
        if self.platform == "Windows" or self.platform == "Linux":
            try:
                # Clamp value
                percent = int(max(0, min(100, percent)))
                sbc.set_brightness(percent)
                print(f"Set Brightness: {percent}%")
            except Exception as e:
                print(f"Error setting brightness: {e}")
        else:
            print(f"Brightness control disabled. Set Brightness: {percent}%")

# --- Standalone test ---
if __name__ == '__main__':
    # This allows you to test the module directly
    print("Testing OSController...")
    controller = OSController()
    
    print("Testing Volume (setting to 50%)...")
    controller.set_volume(50)
    
    print("Testing Brightness (setting to 70%)...")
    controller.set_brightness(70)
    
    print("Testing Play/Pause...")
    controller.play_pause()
    
    print("Testing Next Track...")
    controller.next_track()
    
    print("Test complete. (Lock/Open functions not run for safety)")

