#timer.start("GTK loading")
import gtk
#timer.end("GTK loading")

import re
import time
import Image, ImageCms

from collections import namedtuple
import os.path
#import colorsys

Point = namedtuple('Point', ['x', 'y'])
Area = namedtuple('Area', ['x', 'y', 'width', 'height'])
Event = namedtuple('Event', ['x', 'y', 'button'])

global inf
inf = float('inf')

def bbox(points, create_line=False):
    top = [-inf, -inf] # top rigth corner
    bottom = [inf, inf] # bottom left corner
    line = []
    
    for point in points:
        if point[0] > top[0]: top[0] = point[0]
        if point[0] < bottom[0]: bottom[0] = point[0]
        if point[1] > top[1]: top[1] = point[1]
        if point[1] < bottom[1]: bottom[1] = point[1]
        line.append(point[0])
        line.append(point[1]) 
        
    bounds = [Point._make(bottom), Point._make(top)]
    if create_line:
        bounds.append(line) 
        
    return tuple(bounds)

    
def uniqfy(seq):
    """Returns List Without Duplicates Preserving the Original Order"""
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]



class Timer():
    test_data = {}
    
    def start(self, key):
        print "'%s' runtime test start" % key
        self.test_data[key] = {"start":time.clock()}
    
    def end(self, key):
        tobject = self.test_data[key]
        tobject["end"] = time.clock()
        tobject["time"] = tobject["end"] - tobject["start"]
        self.show(key)
     
    def get(self, key):
        return self.test_data[key]

    def show(self, key):
        tobject = self.test_data[key]
        print "'%s' execution time: %f" % (key, tobject["time"])

timer = Timer()


class Colors(object):
    hex_color_normal = re.compile("#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})")
    hex_color_short = re.compile("#([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])")
    hex_color_long = re.compile("#([a-fA-F0-9]{4})([a-fA-F0-9]{4})([a-fA-F0-9]{4})")
    
    rgb_icc_profile = os.path.join("lib", "icc", "srgb.icm") # ImageCms.get_display_profile()
    cmyk_icc_profile = os.path.join("lib", "icc", "uswebcoatedswop.icc") # from c:\windows\system32\spool\drivers\color\
    #cmyk_icc_profile = os.path.join("lib", "icc", "coatedfogra27.icc") # from c:\windows\system32\spool\drivers\color\
    # "coatedfogra27.icc",  "coatedfogra39.icc"

    
    def get_rgbint(self, r, g=None ,b=None):
         if g == None:
            return 65536 * r[0] + 256 * r[1] + r[2]
         return 65536 * r + 256 * g + b
    
    def parse(self, color):
        assert color is not None

        if isinstance(color, int): #RGBint
            color = ((color >> 16) & 255, (color >> 8) & 255, color & 255)

        #parse color into rgb values
        if isinstance(color, basestring):
            match = self.hex_color_long.match(color)
            if match:
                color = [int(color, 16) / 65535.0 for color in match.groups()]
            else:
                match = self.hex_color_normal.match(color)
                if match:
                    color = [int(color, 16) / 255.0 for color in match.groups()]
                else:
                    match = self.hex_color_short.match(color)
                    color = [int(color + color, 16) / 255.0 for color in match.groups()]

        #elif isinstance(color, gtk.gdk.Color):
        #    color = [color.red / 65535.0,
        #             color.green / 65535.0,
        #             color.blue / 65535.0]
        else:
            # otherwise we assume we have color components in 0..255 range
            if color[0] > 1 or color[1] > 1 or color[2] > 1:
                color = [c / 255.0 for c in color]

        return tuple(color)

    def rgb(self, color):
        return [c * 255 for c in self.parse(color)]
        
        
    def hex(self, color):
        """ convert an (R, G, B) tuple to #RRGGBB """
        #color = self.parse(color)
        rgb_tuple = self.rgb(color)
        #print "rgb_tuple: ", rgb_tuple
        return '#%02x%02x%02x' % (rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])

    def convert_cmyk_hash(self, hash, icc=False):
        """ {color_id: (c,m,y,k)} -> {color_id: (r,g,b)}"""
        cmyk_colors = hash.values()
        rgb_colors = self.from_cmyk(cmyk_colors, icc)
        
        converted_hash = {}
        i = 0
        for key in hash.keys():
            converted_hash[key] = rgb_colors[i]
            i += 1
        return converted_hash
    
    def from_cmyk(self, colors, icc=False):
        """convert cmyk->(0,0,0,0) -> rgb(0,0,0)
            if icc then use ICC profiles, colors -> single tuple, o list of tuples
        """
        single_color = False
        if not isinstance(colors, list): 
            colors = [colors]
            single_color = True
        
        pixels = [tuple(map(lambda x: int(round(x*255/100.0)), pixel)) for pixel in colors] # converts from 100 to 255 format
        img = Image.new("CMYK", (1, len(pixels)))
        img.putdata(pixels)
        
        if not icc:
            converted_colors = list(img.convert("RGB").getdata()) # .getpixel((0,0))
        else:
            converted_colors = list(ImageCms.profileToProfile(img, self.cmyk_icc_profile, self.rgb_icc_profile, outputMode="RGB").getdata()) #.getpixel((0,0))
        
        return single_color and converted_colors[0] or converted_colors # ir arg is single color cmyk tuple -> return single color crgb

        
    def to_cmyk(self, color, icc=False):
        """convert rgb(0,0,0) -> cmyk->(0,0,0,0)"""
        img = Image.new("RGB", (1, 1), color)
        if not icc:
            pixel = img.convert("CMYK").getpixel((0,0))
        else:
            pixel = ImageCms.profileToProfile(img, self.rgb_icc_profile, self.cmyk_icc_profile, outputMode="CMYK").getpixel((0,0))
        #return tuple(map(lambda x: x*100/255.0, pixel))
        return pixel

    #def gdk(self, color):
    #    c = self.parse(color)
    #   return gtk.gdk.Color(int(c[0] * 65535.0), int(c[1] * 65535.0), int(c[2] * 65535.0))

Colors = Colors() # this is a static class, so an instance will do

waitarrow_string = ( #sized 24x24
      "X                       ",
      "XX          XXXXXXXXXX  ",
      "X.X         XX......XX  ",
      "X..X        XXXXXXXXXX  ",
      "X...X        X......X   ",
      "X....X       X......X   ",
      "X.....X      X...X..X   ",
      "X......X     XX X..XX   ",
      "X.......X     XX..XX    ",
      "X........X     XX.X     ",
      "X.........X   XX..XX    ",
      "X......XXXXX XX....XX   ",
      "X...X..X     X..X...X   ",
      "X..XX..X     X.X.X..X   ",
      "X.X  X..X    XX.X.X.X   ",
      "XX   X..X   XXXXXXXXXX  ",
      "X     X..X  XX......XX  ",
      "      X..X  XXXXXXXXXX  ",
      "       X..X             ",
      "       X..X             ",
      "        XX              ",
      "                        ",
      "                        ",
      "                        ")
    
      
waitcross_string = ( #sized 32x20
      "        X       XXXXXXXXXX      ",
      "        X       XX......XX      ",
      "        X       XXXXXXXXXX      ",
      "        X        X......X       ",
      "        X        X......X       ",
      "        X        X...X..X       ",
      "        X        XX X..XX       ",
      "        X         XX..XX        ",
      "XXXXXXXXXXXXXXXXX  XX.X         ",
      "        X         XX..XX        ",
      "        X        XX....XX       ",
      "        X        X..X...X       ",
      "        X        X.X.X..X       ",
      "        X        XX.X.X.X       ",
      "        X       XXXXXXXXXX      ",
      "        X       XX......XX      ",
      "        X       XXXXXXXXXX      ",
      "                                ",
      "                                ",
      "                                ",
      "                                ",
      "                                ",
      "                                ",
      "                                ")
     

def create_xbm(icon_str, filename=None):
    """filename - create file with xbm data"""
    from pygame.cursors import compile #gtk privalo buti importuotas priesh pygame
    from struct import pack
    
    masktuple, datatuple = compile(icon_str, black='X', white='.', xor='o' )
    def reverse_bits(original, numbits):
        return sum(1<<(numbits-1-i) for i in range(numbits) if original>>i&1)
    
    pix =  [reverse_bits(digit, 8) for digit in datatuple] # reverse bits
    mask = [reverse_bits(digit, 8) for digit in masktuple]

    if filename:
        pix_str = "\\".join(["x%0.2X" % digit for digit in pix])
        mask_str = "\\".join(["x%0.2X" % digit for digit in mask])
        f = open(filename, "w")
        f.writelines(('xbm = ("\\', pix_str, '",\n', '"\\', mask_str, '")'))
        f.close()
        
    return ("".join([pack("@B", digit) for digit in pix]), "".join([pack("@B", digit) for digit in mask]))
    

def create_icon(xbm, width, height, hotspot=Point(0, 0)):
    pix_str, mask_str = xbm
    pix = gtk.gdk.bitmap_create_from_data(None, pix_str , width, height)
    mask = gtk.gdk.bitmap_create_from_data(None, mask_str, width, height)
    #set cursor from pixmap
    color = gtk.gdk.Color()
    return gtk.gdk.Cursor(mask, pix, color, color, hotspot.x, hotspot.y)

wait_arrow_xbm = ("\x01\x00\x00\x03\xF0\x3F\x07\xF0\x3F\x0F\xF0\x3F\x1F\xE0\x1F\x3F\xE0\x1F\x7F\xE0\x1F\xFF\x60\x1F\xFF\xC1\x0F\xFF\x83\x07\xFF\xC7\x0F\xFF\xEF\x1F\xFF\xE0\x1F\xFF\xE0\x1F\xE7\xE1\x1F\xE3\xF1\x3F\xC1\xF3\x3F\xC0\xF3\x3F\x80\x07\x00\x80\x07\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
"\x00\x00\x00\x00\x00\x00\x02\xC0\x0F\x06\x00\x00\x0E\xC0\x0F\x1E\xC0\x0F\x3E\xC0\x0D\x7E\x00\x06\xFE\x00\x03\xFE\x01\x02\xFE\x03\x03\x7E\x80\x07\x6E\xC0\x0E\x66\x40\x0D\xC2\x80\x0A\xC0\x00\x00\x80\xC1\x0F\x80\x01\x00\x00\x03\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
#WAIT_ARROW = create_icon(create_xbm(waitarrow_string), 24, 24)
WAIT_ARROW = create_icon(wait_arrow_xbm, 24, 24)

wait_cross_xbm = ("\x00\x01\xFF\x03\x00\x01\xFF\x03\x00\x01\xFF\x03\x00\x01\xFE\x01\x00\x01\xFE\x01\x00\x01\xFE\x01\x00\x01\xF6\x01\x00\x01\xFC\x00\xFF\xFF\x79\x00\x00\x01\xFC\x00\x00\x01\xFE\x01\x00\x01\xFE\x01\x00\x01\xFE\x01\x00\x01\xFE\x01\x00\x01\xFF\x03\x00\x01\xFF\x03\x00\x01\xFF\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
"\x00\x00\x00\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00\xFC\x00\x00\x00\xFC\x00\x00\x00\xDC\x00\x00\x00\x60\x00\x00\x00\x30\x00\x00\x00\x20\x00\x00\x00\x30\x00\x00\x00\x78\x00\x00\x00\xEC\x00\x00\x00\xD4\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")    
#WAIT_CROSS = create_icon(create_xbm(waitcross_string), 32, 24, Point(8,8))
WAIT_CROSS = create_icon(wait_cross_xbm, 32, 24, Point(8,8))
