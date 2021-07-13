#!/usr/bin/env python

from PIL import Image
import time
import unicornhathd

g_display_width, g_display_height = unicornhathd.get_shape() 

g_sprite_sheet = '/home/ubuntu/environments/img/franklin-sprite-sheet.png'
g_sprite_metadata = {
        "bubble-loop": [(0, 0), (16, 0), (32, 0), (48, 0), (0,0)],
        "fall": [(0, 16), (16, 16), (32, 16), (48, 16), (64, 16), (80, 16), (96, 16)]}

class Franklin:
    def __init__(self, sprite_sheet, sprite_sheet_metadata):
        sprites = Image.open(sprite_sheet)
        self.sprite_pixels = sprites.load()
        self.sprite_metadata = sprite_sheet_metadata
    
    def bubble_loop(self):
        bubble = self.sprite_metadata["bubble-loop"]

        for frame in bubble:
            display_sprite(frame, self.sprite_pixels)
            time.sleep(0.5)

    def swim_loop(self):
        swim = self.sprite_metadata["fall"]
        
        # Initialize the loop.
        swim_frame = 2  # Start Franklin in the natural position.
        fall, rise = 1, -1
        direction = fall
        
        for i in range(13):
            display_sprite(swim[swim_frame])
            
            # Franklin falls slowly and rises quickly.
            sleep(0.5) if direction == fall else sleep(0.1)
            
            # Change direction if needed.
            if direction == fall and swim_frame == len(swim):
                direction = rise
            if direction == rise and swim_frame == 0:
                direction = fall

            # Advance to the next frame.
            swim_frame += direction        

    def run(self):
        try:
            while True:
                self.bubble_loop()
                self.bubble_loop()
                self.swim_loop()
                self.swim_loop()
        
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
