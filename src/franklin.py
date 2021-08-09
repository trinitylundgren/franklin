#!/usr/bin/env python

"""
Module: franklin

Author: Trinity Lundgren <trinity@trinitylundgren.com>

Description: Runs franklin, the digital companion that does wakeword listening
speech to text and face recognition.
"""

import subprocess
import time

from io import BytesIO
from PIL import Image
from precise_runner import PreciseEngine, PreciseRunner
import cv2
import face_recognition
import sounddevice as sd
from scipy.io.wavfile import write
import unicornhathd

g_display_width, g_display_height = unicornhathd.get_shape()

G_SPRITE_SHEET = "/home/ubuntu/environments/img/franklin-sprite-sheet.png"
g_sprite_metadata = {
    "bubble-loop": [(0, 0, 10), (16, 0, 10), (32, 0, 10)],
    "fall": [
        (0, 16, 5),
        (16, 16, 5),
        (32, 16, 5),
        (48, 16, 5),
        (64, 16, 5),
        (80, 16, 5),
        (96, 16, 5),
        (112, 16, 5),
    ],
    "startle": [(0, 32, 1)],
    "fall-asleep": [
        (0, 48, 5),
        (16, 48, 5),
        (32, 48, 5),
        (48, 48, 5),
        (64, 48, 5),
        (80, 48, 5),
        (96, 48, 5),
        (112, 48, 5),
    ],
    "sleep": [(0, 64, 10), (16, 64, 10), (32, 64, 10)],
    "search": [(0, 80, 10), (16, 80, 10), (32, 80, 10)],
    "found": [(0, 96, 10), (16, 96, 10), (32, 96, 10)],
    "listen": [(0, 80, 10)],
}


class Animation:
    """ Build an animation from the sprite sheet for an LED Matrix display. """

    def __init__(self, frames):
        self.frames = frames
        self.total_length = sum([frame[2] for frame in self.frames])

    def get_frame(self, frame_number):
        """ Returns the next frame of the animation. """
        frame_number = frame_number % self.total_length
        for frame in self.frames:
            if frame_number < frame[2]:
                return (frame[0], frame[1])
            frame_number -= frame[2]
        return (0, 0)


class Franklin:
    """ Class for franklin, the digital companion. """

    def __init__(self, sprite_sheet, sprite_sheet_metadata):
        sprites = Image.open(sprite_sheet)
        self.sprite_pixels = sprites.load()
        self.sprite_metadata = sprite_sheet_metadata

        self.animations = {
            "idle": Animation(g_sprite_metadata["bubble-loop"]),
            "startle": Animation(g_sprite_metadata["startle"]),
            "fall-asleep": Animation(g_sprite_metadata["fall-asleep"]),
            "sleep": Animation(g_sprite_metadata["sleep"]),
            "search": Animation(g_sprite_metadata["search"]),
            "found": Animation(g_sprite_metadata["found"]),
            "listen": Animation(g_sprite_metadata["listen"]),
        }

        # Initialize franklin's state.
        self.state = "idle"
        self.frames_in_state = 0

        # Set up hotword detection.
        self.engine = PreciseEngine("precise-engine/precise-engine", "ok-franklin.pb")
        self.runner = PreciseRunner(self.engine, on_activation=lambda: self.handle_hotword())
        self.runner.start()
        self.hotword_detected = False

        # Initialize the camera and set resolution.
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 320)
        self.cap.set(4, 240)

        # Set up Deepspeech subprocess.
        self.recording_filename = "output.wav"
        self.deepspeech_path = "/home/ubuntu/DeepSpeech/deepspeech"
        self.deepspeech_model = (
            "/home/ubuntu/DeepSpeech/deepspeech-0.6.1-models/output_graph.tflite"
        )
        self.deepspeech_lm = "/home/ubuntu/DeepSpeech/deepspeech-0.6.1-models/lm.binary"
        self.deepspeech_trie = "/home/ubuntu/DeepSpeech/deepspeech-0.6.1-models/trie"

        self.game = False
        self.seen = False

    def capture_frame(self):
        """ Capture an image from the camera. Return status and image. """
        if self.cap.isOpened():
            ret, img = self.cap.read()
            return ret, img
        print("Error accessing camera")
        return None, None

    def detect_face(self):
        """ Capture an image from the camera, return true if face detected. """
        ret, img = self.capture_frame()
        if ret:
            _, jpeg_image = cv2.imencode(".jpeg", img)
            file_jpegdata = BytesIO(jpeg_image.tobytes())
            image = face_recognition.load_image_file(file_jpegdata)
            return len(face_recognition.face_locations(image)) != 0
        return (ret, None)

    def record_audio(self):
        """ Records and saves audio from the microphone. """
        sample_rate = 44100
        duration = 5
        my_recording = sd.rec(
            int(duration * sample_rate), samplerate=sample_rate, channels=2
        )
        sd.wait()
        write(self.recording_filename, sample_rate, my_recording)

    def speech_to_text(self):
        """ Opens a recorded wav file and transcribes speech to text. """
        cmd = [
            f"{self.deepspeech_path}",
            "--model",
            f"{self.deepspeech_model}",
            "--lm",
            f"{self.deepspeech_lm}",
            "--trie",
            f"{self.deepspeech_trie}",
            "--audio",
            f"./{self.recording_filename}",
        ]
        text = subprocess.check_output(cmd)
        return text.decode("utf-8").split()

    def get_next_frame(self):
        """ Gets the next animation frame to display. """
        return self.animations[self.state].get_frame(self.frames_in_state)

    def update_state(self, ret=None, img=None):
        """ Updates the franklin state machine. """
        if self.state == "startle":
            if self.frames_in_state > 30:
                self.state = "listen"
                self.frames_in_state = 0
                self.hotword_detected = False

        elif self.state == "listen":
            if self.frames_in_state > 10:

                # Stop hotword detection, record audio.
                self.runner.stop()
                self.record_audio()
                command = self.speech_to_text()
                print(command)
                self.runner.start()

                if "play" in command:
                    self.state = "search"
                else:
                    self.state = "idle"
                self.frames_in_state = 0

        elif self.state == "search":
            if self.hotword_detected:
                self.state = "idle"
                self.hotword_detected = False
                self.frames_in_state = 0
            elif self.detect_face():
                self.state = "found"
                self.frames_in_state = 0
            elif self.frames_in_state >= 100:
                self.state = "idle"
                self.frames_in_state = 0

        elif self.state == "found":
            if self.hotword_detected:
                self.state = "idle"
                self.frames_in_state = 0
                self.hotword_detected = False
            elif self.frames_in_state >= 30:
                if not self.detect_face():
                    self.state = "search"
                self.frames_in_state = 0

        elif self.state == "idle":
            if self.hotword_detected:
                self.state = "startle"
                self.frames_in_state = 0

            # An image was passed in.
            elif ret:
                # Convert to HSV to check brightness.
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                brightness = hsv[..., 2].mean()

                if brightness < 40:
                    self.state = "fall-asleep"
                    self.frames_in_state = 0

        elif self.state == "fall-asleep":
            if self.hotword_detected:
                self.state = "startle"
                self.frames_in_state = 0
                return

            if ret:
                # Convert to HSV to check brightness.
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                brightness = hsv[..., 2].mean()

                if brightness > 50:
                    self.state = "startle"
                    self.frames_in_state = 0

            if self.frames_in_state >= 8:
                self.state = "sleep"
                self.frames_in_state = 0

        elif self.state == "sleep":
            if ret:
                # Convert to HSV to check brightness.
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                brightness = hsv[..., 2].mean()

                if brightness > 50:
                    self.state = "startle"
                    self.frames_in_state = 0

    def display_frame(self):
        """ Render the next frame of the animation. """
        next_frame = self.get_next_frame()
        display_sprite(next_frame, self.sprite_pixels)

    def handle_hotword(self):
        """ Sets flag that hotword has been detected. """
        self.hotword_detected = True

    def peek_a_boo(self):
        """ Initiates peek-a-boo game state flags. """
        self.game = True
        self.seen = False

    def run(self):
        """ Franklin main loop. """
        try:
            loop_counter = 0
            while True:
                # Capture an image every 10 loops.
                if loop_counter % 10 == 0:
                    ret, img = self.capture_frame()

                # Advance state machine.
                self.update_state(ret, img)

                # Display a frame.
                self.display_frame()
                time.sleep(0.016)

                self.frames_in_state += 1
                loop_counter += 1

        except KeyboardInterrupt:
            self.runner.stop()
            self.cap.release()
            return


def display_sprite(start_xy, pixels):
    """ Display a sprite on the UnicornHD LED Matrix. """
    for x_coord in range(g_display_width):
        for y_coord in range(g_display_height):

            sprite_x = start_xy[0] + x_coord
            sprite_y = start_xy[1] + y_coord

            red, green, blue = pixels[sprite_x, sprite_y]
            unicornhathd.set_pixel(
                g_display_width - x_coord - 1, y_coord, red, green, blue
            )

    unicornhathd.show()


if __name__ == "__main__":

    # Configure the LED Display Matrix.
    unicornhathd.rotation(0)
    unicornhathd.brightness(0.6)

    franklin = Franklin(G_SPRITE_SHEET, g_sprite_metadata)
    franklin.run()

    unicornhathd.off()
