import math

class GestureRecognizer:
    """
    Translates hand landmarks into a specific gesture.
    Uses a more robust, rotation-invariant detection logic.
    """
    def __init__(self, tip_ids=None):
        if tip_ids is None:
            # Landmark IDs for the tip of each finger
            self.tip_ids = [4, 8, 12, 16, 20]
        self.landmarks = None
    
    def get_finger_status(self):
        """
        Determines which fingers are extended (up).
        Returns a list of 5 booleans (True=Up, False=Down) for [Thumb, Index, Middle, Ring, Pinky].
        
        FINAL ROBUST LOGIC (Rotation Invariant):
        - 4 Fingers: "up" if tip is farther from wrist (0) than its PIP joint.
        - Thumb: "up" if tip (4) is farther from wrist (0) than its inner IP joint (3).
        
        This logic is the most robust for a tucked thumb.
        """
        if not self.landmarks:
            return [False] * 5
            
        fingers = []
        wrist = self.landmarks[0] # Use wrist as the anchor
        
        # --- Thumb ---
        # A thumb is "up" if its tip (4) is farther from the wrist (0)
        # than its inner joint (3).
        thumb_tip = self.landmarks[self.tip_ids[0]]
        thumb_ip = self.landmarks[self.tip_ids[0] - 1] # Inner joint (3)
        
        dist_tip_to_wrist = math.hypot(thumb_tip.x - wrist.x, thumb_tip.y - wrist.y, thumb_tip.z - wrist.z)
        dist_ip_to_wrist = math.hypot(thumb_ip.x - wrist.x, thumb_ip.y - wrist.y, thumb_ip.z - wrist.z)
        
        if dist_tip_to_wrist > dist_ip_to_wrist:
            fingers.append(True)
        else:
            fingers.append(False)
        
        # --- Four Fingers (Index, Middle, Ring, Pinky) ---
        # A finger is "up" if its tip is farther from the wrist (0)
        # than its PIP joint (middle of the finger).
        for id in range(1, 5):
            tip = self.landmarks[self.tip_ids[id]]
            pip = self.landmarks[self.tip_ids[id] - 2] # PIP joint (e.g., 6, 10, 14, 18)
            
            dist_tip_to_wrist = math.hypot(tip.x - wrist.x, tip.y - wrist.y, tip.z - wrist.z)
            dist_pip_to_wrist = math.hypot(pip.x - wrist.x, pip.y - wrist.y, pip.z - wrist.z)

            if dist_tip_to_wrist > dist_pip_to_wrist:
                fingers.append(True)
            else:
                fingers.append(False)
                
        return fingers

    def get_distance(self, p1_idx, p2_idx):
        """Calculates 3D distance between two landmark indices."""
        if not self.landmarks:
            return 0
        p1 = self.landmarks[p1_idx]
        p2 = self.landmarks[p2_idx]
        
        # Use 3D distance (x, y, z) for robust, rotation-invariant distance
        distance = math.hypot(p1.x - p2.x, p1.y - p2.y, p1.z - p2.z)
        # Normalize distance by comparing to wrist-index-base distance
        # to make it scale-invariant, but let's use a raw value for now.
        return distance

    def recognize_gesture(self, landmarks_list):
        """
        Takes the list of landmarks and returns a string representing the gesture.
        """
        # We only work with the first hand detected
        if not landmarks_list:
            return "NO_HAND"
            
        self.landmarks = landmarks_list[0]
        fingers = self.get_finger_status()
        
        # --- Gesture Logic ---
        # [Thumb, Index, Middle, Ring, Pinky]

        # Calculate distance between thumb tip (4) and index tip (8) for "OK" gesture
        dist_thumb_index = self.get_distance(4, 8)
        
        # --- Start with most specific gestures ---

        # OK (👌) - Common Version (3 fingers down)
        # We must check this BEFORE "Thumbs Up" or "One Finger"
        if (fingers == [True, True, False, False, False] or \
            fingers == [False, True, False, False, False]) and \
            dist_thumb_index < 0.08: # Threshold is very small
             return "OK"

        # OK (👌) - Other Version (3 fingers up)
        if (fingers == [True, True, True, True, False] or \
            fingers == [False, False, True, True, True] or \
            fingers == [True, False, True, True, True]) and \
            dist_thumb_index < 0.1: 
             return "OK"

        # 5: Open Palm (✋)
        if fingers == [True, True, True, True, True]:
            return "OPEN_PALM"
            
        # Thumbs Down (👎)
        # ** FIX: This check must come BEFORE Fist. **
        if fingers == [False, False, False, False, False]:
             thumb_tip = self.landmarks[self.tip_ids[0]]
             thumb_mcp = self.landmarks[self.tip_ids[0] - 2] # Base
             
             # Use Y-coordinate just for this specific up/down check
             if thumb_tip.y > thumb_mcp.y: 
                return "THUMBS_DOWN"
             else:
                # If it's not Thumbs Down, it's a regular Fist.
                return "FIST"
            
        # 2: Peace (✌️)
        if fingers == [False, True, True, False, False]:
            return "PEACE"

        # 1: Index (1)
        if fingers == [False, True, False, False, False]:
            return "ONE_FINGER"
            
        # 3: Three Fingers (3)
        if fingers == [False, True, True, True, False]:
            return "THREE_FINGERS"
            
        # 4: Four Fingers (4)
        if fingers == [False, True, True, True, True]:
            return "FOUR_FINGERS"

        # Thumbs Up (👍)
        # Thumb is up, other 4 are down.
        if fingers == [True, False, False, False, False]:
             return "THUMBS_UP"

        # Call Me / Shaka (🤙)
        if fingers == [True, False, False, False, True]:
            return "CALL_ME"

        # If no specific gesture is matched
        return "UNKNOWN"

