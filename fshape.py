from utils import Point, inf #Colors, timer, Point, Area, inf, uniqfy
from vec2d import Vec2d
from bezier import draw_point, debug_points


POINT = 1
POLYLINE = 3
CURVE = 4
POLYGON = 5
POLYGON_CURVE = 6 # area
TEXT = 101

STROKE = 0
FILL = 1

class Shape:
    @staticmethod
    def decompress(shape):
        type = shape[0]
        symbol = shape[1]
        style = shape[2]
        #text = None
        
        #if type == 101: #text
        #    text = shape[2]
        #    data = shape[3:]
        #else:
        #    data = shape[2:]
        data = shape[3:]
        
        if type == 1:
            return Shape(1, Point(data[0], data[1]), symbol, style)
        elif type in (3, 5, 101): # line, area, text
            line = []
            for i in range(0, len(data), 2):
                line.append(Point(data[i], data[i+1]))
            return Shape(type, line, symbol, style)
        elif type in (4, 6): # bezier linija arba poligonas
            curve = []
            #for i in range(0, len(data), 6):
            #    curve.append((Point(data[i], data[i+1]), Point(data[i+2], data[i+3]), Point(data[i+4], data[i+5])))
                
            i, length = 0, len(data)
            
            while i < length:
                if data[i] == None: # skyle poligone
                    curve.append(None)
                    i += 1
                elif i == 0:
                    curve.append((Point(data[i], data[i+1]), Point(data[i], data[i+1]), Point(data[i+2], data[i+3])))
                    i += 4
                elif i == length - 4:
                    curve.append((Point(data[i], data[i+1]), Point(data[i+2], data[i+3]), Point(data[i+2], data[i+3])))
                    i += 4
                else:
                    curve.append((Point(data[i], data[i+1]), Point(data[i+2], data[i+3]), Point(data[i+4], data[i+5])))
                    i += 6
            return Shape(type, curve, symbol, style)
        
    
    def __init__(self, type, data, symbol=None, style={}):
        self._type = type
        if type == 1 and len(data) == 1: # [Point(x,y)]
            self._data = data[0]
        else:
            self._data = data
        
        #if type == 101: # UnformattedText
        #    self._text = text
            #self._angle = angle

        self._symbol = symbol
        self._style = style
        #self._compressed = None
        self._bottom = Vec2d(inf, inf) # bottom left corner, ne Point, kadangi negaliu pointijn.x = 1
        self._top = Vec2d(-inf, -inf) # top rigth corner
        #self._bbox = bbox # galima perduoti iskarto jeigu zinoma

    def get_symbol(self):
        return self._symbol
        
    def get_data(self):
        return self._data
        
    def get_style(self):
        return self._style
     
    def get_type(self):
        return self._type
        
    def move(self, canvas, offset):
        #print "move --- ", self._type, offset, "bbox: ", self._bbox
        """move all coordinates by offset"""
        points = self.to_device(canvas, offset)
        if self._type == 1:
            #user_offset = canvas.device_to_user(Point._make(offset))
            self._data = canvas.device_to_user(points[0])
            #if self._bbox: # jeigu tai simbolis, reikia atnaujinti jo duomenis
            #    print "move point by offset: ", offset, self._bbox
            #    bottom = canvas.device_to_user(canvas.user_to_device(Point._make(self._bbox[:2])) + offset[0])
            #    top = canvas.device_to_user(canvas.user_to_device(Point._make(self._bbox[2:])) + offset[1])
            #    self._bbox = (bottom.x, bottom.y, top.x, top.y)
            #    print "new: ", self._bbox
                                
            #xdata = canvas.device_to_user(points[0])
            #self._data = Point(self._data.x + offset_user.x, self._data.y + offset_user.y) #canvas.device_to_user(points[0])
            #print "compare: ", xdata, self._data            
        elif self._type in (4, 6): # bezier
            self._data = []
            for triplet in points:
                if triplet != None: #skip holes
                    c1 = canvas.device_to_user(Point(triplet[0], triplet[1]))
                    xy = canvas.device_to_user(Point(triplet[2], triplet[3]))
                    c2 = canvas.device_to_user(Point(triplet[4], triplet[5]))
                    self._data.append((xy, c1, c2))
                else:
                    self._data.append(None)
        else:
            self._data = [canvas.device_to_user(point) for point in points]
        
    
    def to_device(self, canvas, offset=(0,0), skip_holes=False):
        if self._type == 1:
            return [canvas.user_to_device(self._data, offset)]
        elif self._type == 4 or self._type == 6:
            points = []
            for triplet in self._data:
                if triplet != None: #skip holes
                    c1 = canvas.user_to_device(triplet[0], offset)
                    xy = canvas.user_to_device(triplet[1], offset)
                    c2 = canvas.user_to_device(triplet[2], offset)
                    points.append((xy.x, xy.y, c1.x, c1.y, c2.x, c2.y))
                elif not skip_holes:
                    points.append(None)
            return points
        else:
            return [canvas.user_to_device(point, offset) for point in self._data]
    
    def is_point(self):
        return self._type == 1
        
    def is_line(self):
        return self._type in (3, 5) # line o polygon
        
    def is_path(self):
        return self._type in (3, 4) # line o curve
        
    def is_polygon(self):
        return self._type in (5, 6)

    def is_curve(self):
        return self._type in (4, 6) # bezier line or bezier polygon

    def is_text(self):
        return self._type == 101 # unformatted text
        
    def draw_handlers(self, ctx, canvas, offset=(0, 0)):
        points = self.to_device(canvas, offset, skip_holes=True)
        
        if self.is_curve():
            debug_points(ctx, points)
        else:
            color = (0,0,1) # blue
            for point in points:
                draw_point(ctx, point.x, point.y, 0.5, color=color)

        
    def compress(self):
        if self._type == POINT:
            #print "self._data: ", self._data
            return (POINT, self._symbol, self._style, self._data[0], self._data[1])
        elif self._type in (POLYLINE, POLYGON, TEXT): #, == 3 or self._type == 5 or self._type == 101:
            line = [self._type, self._symbol, self._style]
            #if self._type == TEXT: 
            #    line.append(self._text)
            for point in self._data:
                line.extend(point)
            return tuple(line)
        elif self._type in (CURVE, POLYGON_CURVE): #== 4 or self._type == 6:
            curve = [self._type, self._symbol, self._style]
            
            i, length = 0, len(self._data)
            
            while i < length:
                triplet = self._data[i]
                
                if triplet:
                    if i != 0: 
                        curve.extend(triplet[0]) # c1
                    curve.extend(triplet[1]) # xy
                    if i != length -1:
                        curve.extend(triplet[2]) # c2
                else:
                    curve.append(None) # skyle poligone...
                i += 1

            return tuple(curve)

    def _extend(self, point):
        if point.x > self._top.x: self._top.x = point.x
        if point.x < self._bottom.x: self._bottom.x = point.x
        if point.y > self._top.y: self._top.y = point.y
        if point.y < self._bottom.y: self._bottom.y = point.y
    
    
    def size(self):
        box = self.bbox()
        return (box[2] - box[0], box[3] - box[1])
        
    
    def bbox(self, border=0):
        #if self._bbox: # jeigu tai simbolis kuriam reikia paskaiciuoti dydi...
        #    #print "return bbox: ", self._bbox
        #    return self._bbox
    
        if self._bottom.x != inf: # tam kad pakartotinai nekviestume
            pass
        elif self._type == POINT:
            self._extend(self._data)
            radius = self._style.get("radius", "")
            if radius:
                self._extend(Point(self._data.x - radius, self._data.y - radius))
                self._extend(Point(self._data.x + radius, self._data.y + radius))
            
        elif self._type in (POLYLINE, POLYGON, TEXT):
            for point in self._data:
                self._extend(point)
        elif self._type in (CURVE, POLYGON_CURVE):
            for point3 in self._data:
                if point3: # gali buti none 0 skyle poligone...
                    for point in point3: #[1:]: # praleidziam xy
                        self._extend(point)
                    
        #if border:
        #    print "border:", border
        #    print "old: ", (self._bottom.x, self._bottom.y, self._top.x, self._top.y)
        #    print "new: ", (self._bottom.x - border, self._bottom.y - border, self._top.x + border, self._top.y + border)
        
        #print "self._style", self._style
        return (self._bottom.x - border, self._bottom.y - border, self._top.x + border, self._top.y + border)
