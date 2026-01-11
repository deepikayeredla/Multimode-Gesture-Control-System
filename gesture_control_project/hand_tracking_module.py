import cv2
import mediapipe as mp
import time

class HandDetector:
    """
    Finds Hands in a BGR image.
    Creates properties:
    - landmarks: A list of 21 3D landmarks (x, y, z) for each detected hand.
    - hands_type: "Left" or "Right" for each detected hand.
    """
    def __init__(self, mode=False, max_hands=1, model_complexity=1, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.model_complexity = model_complexity
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = mp.solutions.hands
        # Note: static_image_mode is set to self.mode
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_draw.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4)
        self.connection_spec = self.mp_draw.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2)
        
        self.landmarks = []
        self.hands_type = [] # "Left" or "Right"

    def find_hands(self, img, draw=True):
        """
        Finds hands in a BGR image and draws the landmarks.
        Returns the image with or without drawings.
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        self.landmarks = []
        self.hands_type = []

        if self.results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(self.results.multi_hand_landmarks, self.results.multi_handedness):
                # Save landmarks
                my_hand = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    my_hand.append(lm)
                self.landmarks.append(my_hand)
                
                # Save hand type (Left/Right)
                self.hands_type.append(handedness.classification[0].label)
                
                # Draw landmarks if requested
                if draw:
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.drawing_spec,
                        self.connection_spec
                    )
        return img

    def get_landmarks(self):
        """
        Returns the landmarks list.
        Each item in the list is a hand.
        Each hand is a list of 21 landmarks.
        """
        return self.landmarks

if __name__ == "__main__":
    # Test script
    cap = cv2.VideoCapture(0)
    detector = HandDetector()
    while True:
        success, img = cap.read()
        if not success:
            break
        
        img = detector.find_hands(img, draw=True)
        landmarks = detector.get_landmarks()
        
        if landmarks:
            # Print info for the first hand
            print(f"Detected {len(landmarks)} hand(s).")
            print(f"Hand type: {detector.hands_type[0]}")
            # print(f"Thumb Tip (Landmark 4): {landmarks[0][4]}")
            
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
