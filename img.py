#!/usr/bin/env python3
from PIL import Image
import sys
if len(sys.argv)<2:
    print("Usage: %s image [dither_amount]" % sys.argv[0])
    exit()

image = Image.open(sys.argv[1])
dither = 0.5
if len(sys.argv)>=3:
    dither=float(sys.argv[2])

def ansi_color(image,dither):
    pal_image= Image.new("P", (1,1))
    b=255
    pal_image.putpalette(
        (0,0,0,
         b,0,0,
         0,b,0,
         b,b,0,
         0,0,b,
         b,0,b,
         0,b,b,
         b,b,b,
         #255,255,255
        )+(0,0,0)*(255-8)
    )
    image = image.convert("RGB")
    smooth = image.quantize(palette=pal_image,dither=0).convert("RGB")
    smooth = Image.blend(smooth, image, dither)
    return smooth.quantize(palette=pal_image)

w,h = image.size
if w>80:
    image = image.resize((80,int(h/(w/80))),resample=Image.BICUBIC)
    w,h=image.size

image = ansi_color(image,dither)
   
text = ""
obg = -1
ofg = -1
if h % 2:
    h = h -1
for y in range(0,h,2):
    for x in range(0,w):
        bg = image.getpixel((x,y))
        fg = image.getpixel((x,y+1))
        if bg>=8:
            bg=0
        if fg>=8:
            fg=0
        if bg==fg:
            if bg==obg:
                text+=" "
            elif fg==ofg:
                text+="█"
            else:
                text+="\033[%dm█" % (fg+30)
                ofg=fg
        elif fg==ofg and bg==obg:
            text += "▄"
        elif fg==ofg:
            text += "\033[%dm▄" % (bg+40)
            obg = bg
        elif bg==obg:
            text += "\033[%dm▄" % (fg+30)
            ofg=fg
        else:
            text += "\033[%d;%dm▄" % (fg+30,bg+40)
            ofg=fg
            obg=bg
    text+="\033[49m\n"
    obg=-1
text+="\033[m"
print(text)
#image.save("out.png")
#"▄█"
