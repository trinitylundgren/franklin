#!/usr/bin/env python

from PIL import Image
from precise_runner import PreciseEngine, PreciseRunner
import time
import unicornhathd

g_display_width, g_display_height = unicornhathd.get_shape()

g_sprite_sheet = "/home/ubuntu/environments/img/franklin-sprite-sheet.png"
g_sprite_metadata = {
    "bubble-loop": [(0, 0, 10), (16, 0, 10), (32, 0, 10)],
    "fall": [
        (0, 16),
        (16, 16),
        (32, 16),
        (48, 16),
        (64, 16),
        (80, 16),
        (96, 16),
        (112, 16),
    ],
    "startle": [(0, 32, 1)],
}


class Animation:
    def __init__(self, frames):
        self.frames = frames
        self.total_length = sum([frame[2] for frame in self.frames])

    def get_frame(self, frame_number):
        frame_number = frame_number % self.total_length
        for frame in self.frames:
            if frame_number < frame[2]:
                return (frame[0], frame[1])
            frame_number -= frame[2]


class Franklin:
    def __init__(self, sprite_sheet, sprite_sheet_metadata):
        sprites = Image.open(sprite_sheet)
        self.sprite_pixels = sprites.load()
        self.sprite_metadata = sprite_sheet_metadata

        self.animations = {
            "idle": Animation(g_sprite_metadata["bubble-loop"]),
            "startle": Animation(g_sprite_metadata["startle"]),
        }

        self.state = "idle"
        self.frames_in_state = 0

        self.hotword_detected = False

    def bubble_loop(self):
        bubble = self.sprite_metadata["bubble-loop"]

        for frame in bubble:
            display_sprite(frame, self.sprite_pixels)
            time.sleep(0.5)

    def swim_loop(self):
        swim = self.sprite_metadata["fall"]

        # Initialize the loop.
        swim_frame = 3  # Start Franklin in the natural position.
        fall, rise = 1, -1
        direction = fall

        for i in range(14):
            display_sprite(swim[swim_frame], self.sprite_pixels)

            # Franklin falls slowly and rises quickly.
            time.sleep(0.3) if direction == fall else time.sleep(0.03)

            # Change direction if needed.
            if direction == fall and swim_frame == len(swim) - 1:
                direction = rise
            if direction == rise and swim_frame == 0:
                direction = fall

            # Advance to the next frame.
            swim_frame += direction

    def startle(self):
        startle = self.sprite_metadata["startle"]
        display_sprite(startle[0], self.sprite_pixels)
        time.sleep(1)

    def idle(self):
        self.bubble_loop()
        self.swim_loop()
        self.swim_loop()

    def get_next_frame(self):
        return self.animations[self.state].get_frame(self.frames_in_state)

    def update_state(self):
        if self.state == "startle":
            if self.frames_in_state > 50:
                self.state = "idle"
                self.frames_in_state = 0
                self.hotword_detected = False

        elif self.state == "idle":
            if self.hotword_detected:
                self.state = "startle"
                self.frames_in_state = 0

    def display_frame(self):
        next_frame = self.get_next_frame()
        display_sprite(next_frame, self.sprite_pixels)

    def handle_hotword(self):
        self.hotword_detected = True

    def run(self):
        # Set up hotword detection.
        engine = PreciseEngine("precise-engine/precise-engine", "ok-franklin.pb")
        runner = PreciseRunner(engine, on_activation=lambda: self.handle_hotword())
        runner.start()

        try:
            while True:
                # Advance state machine.
                self.update_state()

                # Display a frame.
                self.display_frame()
                time.sleep(0.016)

                self.frames_in_state += 1

        except KeyboardInterrupt:
            return


def display_sprite(start_xy, pixels):
    for x in range(g_display_width):
        for y in range(g_display_height):

            sprite_x = start_xy[0] + x
            sprite_y = start_xy[1] + y

            r, g, b = pixels[sprite_x, sprite_y]
            unicornhathd.set_pixel(x, y, r, g, b)

    unicornhathd.show()


if __name__ == "__main__":

    # Configure the LED Display Matrix.
    unicornhathd.rotation(0)
    unicornhathd.brightness(0.6)

    franklin = Franklin(g_sprite_sheet, g_sprite_metadata)
    franklin.run()

    unicornhathd.off()
