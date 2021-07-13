#!/usr/bin/env python

from PIL import Image
import time
import unicornhathd

g_display_width, g_display_height = unicornhathd.get_shape() 

g_sprite_sheet = '/home/ubuntu/environments/img/franklin-sprite-sheet.png'
g_sprite_metadata = {
        "bubble-loop": [(0, 0), (16, 0), (32, 0), (48, 0)]}

class Franklin:
    def __init__(self, sprite_sheet, sprite_sheet_metadata):
        sprites = Image.open(sprite_sheet)
        self.sprite_pixels = sprites.load()
        self.sprite_metadata = sprite_sheet_metadata
    
    def bubble_loop(self):
        bubble = self.sprite_metadata["bubble-loop"]
        try:
            bubble_frame = 0
            while True:
                display_sprite(bubble[bubble_frame], self.sprite_pixels)
                time.sleep(0.5)
                bubble_frame = (bubble_frame + 1) % len(bubble)
        except KeyboardInterrupt:
            return

    def run(self):
        self.bubble_loop()

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
