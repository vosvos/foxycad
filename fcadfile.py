"""
Kadangi visi metodai statiniai - turbut butu logiska juos sudeti i du failus
fcadfile.py
fssfile.py
sukurti file/

from file.fcadfile import ...
"""
#import canvas
import os
import codecs
import json
import ocadfile
import fshape
import cairo

from css_parser import inline_parse, parse
from utils import Point, Colors


class ShapeFile:

    @staticmethod
    def create_fcad_string(shapes, header=True):
        lines = []
        if header:
            lines.append("shape,symbol,style,points;ver20120319") 
        
        for shape in shapes:
            symbol = ("" if shape[1] == None else shape[1])
            #print "SHAPE", shape
            lines.append("%i,%s,%s,%s" % (shape[0], symbol, StyleFile.style2txt(shape[2]), ",".join([("" if value == None else str(value)) for value in shape[3:]])))
        
        return "\n".join(lines)

        
    @staticmethod
    def create_fcad_file(file_path, shapes):
        file = codecs.open(file_path, "w", "utf-8" )
        file.write(ShapeFile.create_fcad_string(shapes))
        file.close()


    @staticmethod
    def read_fcad_string(string, header=True):
        lines = string.splitlines()
        
        if header and len(lines):
            header = lines[0]
            lines = lines[1:]
        
        shapes = []
        for line in lines:
            #print "line: ", line
            index1 = line.index(",")
            shape = line[:index1]
            index2 = line[index1+1:].index(",")
            symbol = line[index1+1:index1+1+ index2]
            #print "xxx: ", line[index1+1+index2], line[index1+1+index2+1]
            #print "xxx: ", shape, symbol
            
            if line[index1+1+index2+1] == ",":
                style = {}
                end = index1+1+index2
            else:
                start = line.index(",{")
                #shape, symbol = line[:start].split(",")
                end = line.rindex("},")
                #print "css: ", line[start+1:end+1]
                
                #style = self.txt2style(line[start+1:end+1])
                style = inline_parse(line[start+1:end+1], StyleFile.decode_data)
            data = map(lambda x: None if x=="" else float(x), line[end+2:].split(","))
            #print line[end+2:], data
            
            data.insert(0, style)
            data.insert(0, symbol)
            data.insert(0, int(shape))
            shapes.append(data)
        
        #print "read_fcad_string: ", len(shapes)

        return shapes
        
    
        
    @staticmethod
    def read_fcad_file(file_path, header=True):
        """nuskaito faila ir grazina shapes[]"""
        if os.path.exists(file_path):
            file = codecs.open(file_path, "r", "utf-8" )
            return ShapeFile.read_fcad_string(file.read(), header)
        else:
            raise Exception("File not found: %s" % file_path)
            
    
       
    
    
class StyleFile:

    @staticmethod
    def decode_data(key, value):
        return {
            "double-width": lambda x:float(x),
            "double-left-width": lambda x:float(x),
            "double-right-width": lambda x:float(x),
            "double-color": lambda x: map(lambda y: float(y), value[1:-1].split(",")),
            "double-left-color": lambda x: map(lambda y: float(y), value[1:-1].split(",")),
            "double-right-color": lambda x: map(lambda y: float(y), value[1:-1].split(",")),
            "z-index": lambda x:int(x),
            "double-z-index": lambda x:int(x),
            "double-left-z-index": lambda x:int(x),
            "double-right-z-index": lambda x:int(x),
            "line-cap": lambda x:int(x),
            "line-join": lambda x:int(x),
            "line-width": lambda x:float(x),
            "length-main": lambda x:float(x),
            "length-end": lambda x:float(x),
            "length-gap": lambda x:float(x),
            "symbol-distance": lambda x:float(x),
            "symbol-repeat": lambda x:int(x),
            "radius": lambda x:float(x),
            "color": lambda x: map(lambda y: float(y), value[1:-1].split(",")),
            #"dash-pattern": lambda x: map(lambda y: float(y), value[1:-1].split(",")),
            "dash-points": lambda x: map(lambda y: int(y), value[1:-1].split(",")),
            "corner-points": lambda x: map(lambda y: int(y), value[1:-1].split(",")),
            "text": lambda x: x, #json.loads(x)
            "angle":lambda x:int(x),
            "symbol-data": lambda x: ShapeFile.read_fcad_string("\n".join(x), header=False),
            "font-weight":lambda x:int(x),
            "font-style":lambda x:int(x),
            "font-size":lambda x:float(x)
        }.get(key, lambda x:x)(value)

        
    @staticmethod    
    def encode_data(key, value):
        return {
            "color": lambda x: tuple(map(lambda y: int(y), x)),
            "double-color": lambda x: tuple(map(lambda y: int(y), x)),
            "double-left-color": lambda x: tuple(map(lambda y: int(y), x)),
            "double-right-color": lambda x: tuple(map(lambda y: int(y), x)),
            #"dash-pattern": lambda x: tuple(map(lambda y: int(y), x)),
            "text": lambda x: json.dumps(x),
            "data" : lambda x: """\"%s\"""" % x,
            "symbol-data" : lambda x: """\"%s\"""" % ShapeFile.create_fcad_string(x, header=False)
        }.get(key, lambda x:x)(value)

        
    @staticmethod
    def style2txt(style, prettyprint=False):
        if not len(style): return ""
        inline_style = []
        
        for key, value in style.items():
            #inline_style[key] = str(self.encode_data(key, value))
            
            if key in ["symbol-data"]:
                #inline_style.append("%s%s:\"\"\"%s\"\"\"" % (("\t" if prettyprint else ""), "data2", self.encode_data(key, value)))
                shapes = value #self.get_symbol_shapes(symbol)
                
                symbol_data = []
                for shape in shapes:
                    symbol_id = ("" if shape[1] == None else shape[1])
                    symbol_data.append("\t\t%i,%s,%s,%s" % (shape[0], symbol_id, StyleFile.style2txt(shape[2]), ",".join([("" if value == None else str(value)) for value in shape[3:]])))
                    
                inline_style.append("\t%s:\"\"\"\n%s\n\t\"\"\"" % (key, "\n".join(symbol_data)))
            else:
                inline_style.append("%s%s:%s" % (("\t" if prettyprint else ""), key, StyleFile.encode_data(key, value)))
                
        
        join = ";%s" % ("\n" if prettyprint else "")
        data = join.join(inline_style)

        join2 = "%s" % ("\n" if prettyprint else "")
        
        return join2.join(("{", data, "}"))

        
    @staticmethod
    def create_css_file(file_path, css_shape, css_symbol, prettyprint=False):
        file = codecs.open(file_path, "w", "utf-8" )
        
        for shape, style in css_shape.items():
            file.write("%s %s\n" % (shape, StyleFile.style2txt(style, prettyprint=prettyprint)))
            
            if prettyprint:
                file.write("\n")
            
            #file.write("%i,%s,%s,%s\n" % (shape[0], symbol, self.style2txt(shape[2]), ",".join([("" if value == None else str(value)) for value in shape[3:]])))
        file.write("\n")
        
        for symbol, style in css_symbol.items():
            file.write(".%s %s\n" % (symbol, StyleFile.style2txt(style, prettyprint=prettyprint)))

            if prettyprint:
                file.write("\n")
        
        file.close()

        
    @staticmethod
    def read_css_file(file_path):
        if os.path.exists(file_path):
            file = codecs.open(file_path, "r", "utf-8" )
            return parse(file.read(), StyleFile.decode_data)
        else:
            raise Exception("File not found: %s" % file_path)


            
class OcadFile:
    types = {
        ocadfile.Point: fshape.POINT,
        ocadfile.Line: fshape.CURVE,
        ocadfile.Area: fshape.POLYGON_CURVE,
        ocadfile.UnformattedText: fshape.TEXT,
        ocadfile.FormattedText: 102,
        # OCAD 9 only
        ocadfile.LineText: 103,
        ocadfile.RectangleO: 104
    }
    
    def __init__(self, file_path, prj):
        if os.path.exists(file_path):
            self._of = ocadfile.Reader(file_path)
            self._prj = prj
        else:
            raise Exception("File not found: %s" % file_path)

            
    def get_shapes(self):
        shapes = []

        elements = self._of.elements()
        for element in elements:
            otp = element.Otp()
            t = OcadFile.types.get(otp, 102)
            if t < 102:
                symbol_id = element.symbol()
                id = None
                
                angle = element.Angle()
                style = ({} if angle==0 else {"angle": angle})
                
                if otp == ocadfile.Line or otp == ocadfile.Area :
                    shapes.append(fshape.Shape(t, self.ocadLine2Curve(element.points(), style=style), symbol_id, style))
                    #id = self.add(Shape(t, self.ocadLine2Curve(element.points(), prj=prj, style=style), symbol_id, style))
                elif otp == ocadfile.UnformattedText:
                    style["text"] = element.Text()
                    shapes.append(fshape.Shape(t, [self._prj.map_to_user(cord) for cord in element.points()], symbol_id, style))
                    #id = self.add(Shape(t, [self._prj.map_to_user(cord) for cord in element.points()], symbol_id, style))
                elif otp == ocadfile.Point:
                    points = [self._prj.map_to_user(cord) for cord in element.points()]
                    shapes.append(fshape.Shape(t, points, symbol=symbol_id, style=style))
                    #id = self.add(Shape(t, points, symbol=symbol_id, style=style))
                else:
                    shapes.append(fshape.Shape(t, [self._prj.map_to_user(cord) for cord in element.points()], symbol_id, style))
                    #id = self.add(Shape(t, [self._prj.map_to_user(cord) for cord in element.points()], symbol_id, style))
            else:
                print "Ocad object: ", t
        
        return shapes

        
    def get_symbols_style(self):
        pass


    def ocadLine2Curve(self, points, style=None):
        # takas1 C1, C2 takas C1, C2 taskas C1, C2 Takas
        curve = []
        length = len(points)
        
        #def map_to_user(cord):
        #    if self._prj:
        #        return self._prj.map_to_user(cord)
        #    return cord
        
        def read_point_attributes(cord, k):
            if cord.IsFirstInHole(): # skyle poligone...
                curve.append(None)

            if style != None and cord.IsDashPoint():
                if not "dash-points" in style: style["dash-points"] = []
                style["dash-points"].append(k)
            
            if style != None and cord.IsCornerPoint():
                if not "corner-points" in style: style["corner-points"] = []
                style["corner-points"].append(k)
        
        first_curve_point = False # aptikome pirma bezier taskas kuris turi tik viena rankena...
        i = 0
        
        #for cord in points:
        #    if cord.IsDashPoint():
        #        print "DASH FOUND!!!", i
        k = 0 # naujas indexas - kad gauti teisinga dash indeksa, kai imami ne bezier o paprasti taskai
        
        #print "line?"
        while i < length:
            cord = points[i] # prasideti turi nuo isUsual(), tada arba vel Usual arba C1,C2
            point = self._prj.map_to_user(cord) #map_to_user(cord)

            #print "Dash: ", k
            #if cord.IsFirstInHole(): # skyle poligone...
            #    curve.append(None)
            
            #if style != None and cord.IsDashPoint():
            #    if not "dash-points" in style: style["dash-points"] = []
            #    style["dash-points"].append(i)
            #print "isUsual: ", cord.IsUsual(), cord.IsNoLeftDouble(), cord.IsNoRightDouble()
            
            if not first_curve_point and (i+1 < length and points[i+1].IsUsual()) or i+1 == length: # apdorojame visus ne bezier taskus
                read_point_attributes(cord, k+1)
                
                curve.append((point, point, point)) 
                #print "Non bezier, now dash index could be wrong ! could not use ix2!"
                i += 1
                k += 3
                #print "0"
            else:
                if not first_curve_point and i+1 < length and cord.IsUsual() and points[i+1].IsFirstCurve(): # susitavrekom su pirmu bezier tasku
                    read_point_attributes(cord, k+1)
                    
                    c2 = self._prj.map_to_user(points[i+1]) #
                    curve.append((point, point, c2)) # pirmasis bezier taskas turi tik viena rankena
                    first_curve_point = True
                    i += 2
                    k += 3
                    #print "1"
                elif first_curve_point and i+2 < length and not points[i+2].IsUsual(): # vidinis bezier taskas
                    read_point_attributes(points[i+1], k+1) # cia realus bezier taskas (is sonu handlai)

                    #print "second handle is not usual: sec.curve:", points[i+2].IsSecondCurve(), " first.curve:", points[i+2].IsFirstCurve()
                    #print "second handle is not usual: sec.curve:", points[i+2].IsSecondCurve(), " first.curve:", points[i+2].IsFirstCurve()
                    
                    bezier = self._prj.map_to_user(points[i+1])
                    c2 = self._prj.map_to_user(points[i+2])
                    #curve.append((bezier, point, c2))
                    curve.append((point, bezier, c2)) 
                    i += 3
                    k += 3
                    #print "2"
                elif first_curve_point: # paskutinis bezier taskas su viena rankena
                    #print "last bezier point"
                    read_point_attributes(points[i+1], k+1) # cia realus bezier taskas (is sonu handlai)

                    bezier = self._prj.map_to_user(points[i+1])
                    
                    curve.append((point, bezier, bezier))
                    first_curve_point = False
                    i += 2
                    k += 3
                    #print "3"
                else:
                    print "else!"
                    i += 1

        #print "ocadLine2Curve: ", points, " ---- ", curve
        return curve

        
    def get_symbols_style(self):
        symbols_style = {}
        
        ocad_symbols = self._of.symbols()
        ocad_colors = self._of.colors()
        self.rgb_colors = Colors.convert_cmyk_hash(dict(ocad_colors), icc=True)
        
        self.color_index = [data[0] for data in reversed(ocad_colors)] # 0 pozicijoje yra ta kuria reikia nupieshti veliausiai, todel apverciam
        
        for symbol_id, symbol in ocad_symbols.items():
            #print "symbol_id: ", symbol_id
            symbol_style = {}
            symbols_style[symbol_id] = symbol_style
             
             
        
            #symbol_id = symbol_id.replace(".", "_")
            color_id = symbol.Color() # reikalinga z-index nustatyti
            type = symbol.Otp()
            #print "gavom pslavo koda :", color_id, " simbolis: ", symbol_id, " tipas:", type
            style = symbol.ESym()
            
            if symbol_id == "518.0":
                print "518.0 style: ", style
            
            if symbol_id == "503.0":
                print "503.0 style: ", style
                
            if symbol_id == "525.0":
                print "525.0 style: ", style
                
            zindex = None
            
            #0: Normal; 1: Protected; 2: Hidden
            if symbol.Status() == 2: # hidden 
                symbol_style["status"] = 2
            
            symbol_style["color"] = self.rgb_colors.get(color_id, (0,0,0))
            #self.set_symbol_style(symbol_id, {"color": self.rgb_colors.get(color_id, (0,0,0))})
            if color_id in self.color_index:
                zindex = self.color_index.index(color_id)

            if zindex== None:
                print "alert no color!", symbol_id, color_id, self.color_index
            
            if type == ocadfile.Line:
                width = style.LineWidth# or style.DblWidth
                symbol_style["line-width"] = width/100.0 * self._prj.map_scale
                
                if style.DblWidth: # and style.DblFillColor: - color gali buti 0
                    symbol_style["double-width"] = style.DblWidth/100.0 * self._prj.map_scale
                    symbol_style["double-color"] = self.rgb_colors.get(style.DblFillColor, (0,0,0))
                    
                    if style.DblFlags: # 0 - fill off, 1 - fill on, 2 - background on?
                        double_zindex = self.color_index.index(style.DblFillColor)
                        symbol_style["double-z-index"] = double_zindex # jeigu nera zindexo - tai nepaisysime
                        
                        #if double_zindex < zindex:
                        #    zindex = double_zindex
                    
                if style.DblLeftWidth: # and style.DblLeftColor: # spalva nesvarbi jeigu nera plocio! ar atvrksciai
                    symbol_style["double-left-width"] = style.DblLeftWidth/100.0 * self._prj.map_scale
                    symbol_style["double-left-color"] = self.rgb_colors.get(style.DblLeftColor, (0,0,0))
                    double_left_zindex = self.color_index.index(style.DblLeftColor)
                    symbol_style["double-left-z-index"] = double_left_zindex
                    
                    #if double_left_zindex < zindex:
                    #    zindex = double_left_zindex
                    
                if style.DblRightWidth: # and style.DblRightColor: # rusiskuose failuose yra DblRightColor - kuriu neranda index'e!
                    symbol_style["double-right-width"] = style.DblRightWidth/100.0 * self._prj.map_scale
                    symbol_style["double-right-color"] = self.rgb_colors.get(style.DblRightColor, (0,0,0))
                    double_right_zindex = self.color_index.index(style.DblRightColor)
                    symbol_style["double-right-z-index"] = double_right_zindex
                    
                    #if double_right_zindex < zindex:
                    #    zindex = double_right_zindex
                
                if style.MainLength:
                    symbol_style["length-main"] = style.MainLength/100.0 * self._prj.map_scale
                    
                if style.EndLength:
                    symbol_style["length-end"] = style.EndLength/100.0 * self._prj.map_scale
                    
                if style.MainGap:
                    symbol_style["length-gap"] = style.MainGap/100.0 * self._prj.map_scale
                    
                if style.nPrimSym and style.nPrimSym > 1:
                    symbol_style["symbol-repeat"] = style.nPrimSym
                    symbol_style["symbol-distance"] = style.PrimSymDist/100.0 * self._prj.map_scale
                     
                elements = symbol.Elements()
                if len(elements):
                    shapes = self.create_symbol_data(elements)
                    symbol_style["symbol-data"] = shapes
                    
                    for shape in shapes:
                        new_zindex = shape[2].get("z-index")
                        #if new_zindex < zindex: # randame maziausia z-index'a!
                        #    zindex = new_zindex
                    
            elif type == ocadfile.Point:
                shapes = self.create_symbol_data(symbol.Elements())
                
                zindex = shapes[0][2].get("z-index") # privalo tureti spalva ir z-index'a tuo paciu !
                for shape in shapes[1:]:
                    new_zindex = shape[2].get("z-index")
                    if new_zindex < zindex: # randame maziausia z-index'a!
                        zindex = new_zindex
                
                symbol_style["symbol-data"] = shapes
            
            elif type in (ocadfile.UnformattedText, ocadfile.FormattedText):
                symbol_style["font-size"] = style.FontSize/10
                symbol_style["font-name"] = style.FontName
                symbol_style["font-weight"] = cairo.FONT_WEIGHT_BOLD if style.Weight == 700 else cairo.FONT_WEIGHT_NORMAL
                symbol_style["font-style"] = cairo.FONT_SLANT_ITALIC if style.Italic ==1 else cairo.FONT_SLANT_NORMAL
                #print "TEXT STYLE:", symbol_id, " -:- ", style
            
            symbol_style["z-index"] = zindex

        return symbols_style

        
    def create_symbol_data(self, elements):
        #top = [-inf, -inf] # top rigth corner
        #bottom = [inf, inf] # bottom left corner
        #def extend_viewbox(bbox):
        #    if bbox[2] > top[0]: top[0] = bbox[2]
        #    if bbox[0] < bottom[0]: bottom[0] = bbox[0]
        #    if bbox[3] > top[1]: top[1] = bbox[3]
        #    if bbox[1] < bottom[1]: bottom[1] = bbox[1]

        shapes = []
        # cia reikes isrusiuoti elements pagal spalvas!
        types = {
            1: fshape.CURVE,
            2: fshape.POLYGON_CURVE,
            3: fshape.POINT, # circle
            4: fshape.POINT # dot
        }
       
        for header, points in elements:
            t = types.get(header.stType, 5) #1: line,  2: area, 3: circle, 4: dot (filled circle)
            
            if header.stType in (1, 2): 
                points = self.ocadLine2Curve(points)
                #points = self.mirror(points) # reikia apversti

                #style = {"color":map(lambda x:x/255.0, self.rgb_colors.get(header.stColor, (0,0,0))),
                #             "z-index": 0}
                style = {"color": self.rgb_colors.get(header.stColor, (0,0,0)), "z-index": 0}

                if t == fshape.CURVE: # tik linijoms:
                    style["line-width"] = header.stLineWidth / 100.0 * self._prj.map_scale
                    if header.stFlags == 0:
                        style["line-cap"] = cairo.LINE_CAP_BUTT
                        style["line-join"] = cairo.LINE_JOIN_ROUND
                    elif header.stFlags == 1:
                        style["line-cap"] = cairo.LINE_CAP_ROUND
                        style["line-join"] = cairo.LINE_JOIN_ROUND
                    elif header.stFlags == 4:
                        style["line-cap"] = cairo.LINE_CAP_BUTT
                        style["line-join"] = cairo.LINE_JOIN_MITER # astrus kampai
                        # tokie objektai kaip starto simbolis - linijos kampai turi buti nubrezti atitinkamai (4)...
                        # pirmas ir paskutinis linijos taskas sutampa - taigi tai poligonas su stroke
                        #if points[0][0].x == points[-1][0].x and points[0][0].y == points[-1][0].y:
                        if points[0][1].x == points[-1][1].x and points[0][1].y == points[-1][1].y:
                            t = fshape.POLYGON_CURVE
                    
                if header.stColor in self.color_index:
                    style["z-index"] = self.color_index.index(header.stColor)
                
                shape = fshape.Shape(t, points, style=style)
               # extend_viewbox(shape.bbox())
                shapes.append(shape.compress())
                #self._canvas.draw_shape(ctx, shape.compress(), {"color":(0,0,0)}, fill_or_stroke=True)
            elif header.stType in (3, 4): # circle
                point = self._prj.map_to_user(Point(points[0].x, -points[0].y))
                
                                
                radius = header.stDiameter / 200.0 * self._prj.map_scale # /100/2
                style = {"color": self.rgb_colors.get(header.stColor, (0,0,0)), # map(lambda x:x/255.0, self.rgb_colors.get(header.stColor, (0,0,0))),
                             "z-index": 0,
                             "radius":  radius #- (header.stLineWidth/100.0)
                            }
                            
                #extend_viewbox((point.x - radius, point.y - radius, point.x + radius, point.y + radius)) # apskritimo bbox priklauso ir nuo jo diametro
                            
                if header.stColor in self.color_index:
                    style["z-index"] = self.color_index.index(header.stColor)
                    
                if header.stType == 3: # circle with stroke
                    style["line-width"] = header.stLineWidth / 100.0 * self._prj.map_scale
                    
            
                point = Point(point.x, -point.y)
                shape = fshape.Shape(t, point, style=style)
                shapes.append(shape.compress())
            
       # width, height = (top[0] - bottom[0], top[1] - bottom[1])
        #print "create_svg_symbol: ", width, height
        #ctx.translate(self._canvas.line_width/2.0, 0)
        #ctx.scale(10, 10)
        
        return sorted(shapes, key=lambda x: x[2].get("z-index", -1))
