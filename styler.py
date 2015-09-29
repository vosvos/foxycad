from utils import inf
#from css_parser import inline_parse, parse
#from cStringIO import StringIO

from fcadfile import StyleFile

import fshape
#import rsvg
import cairo
import math


class Styler:
    def __init__(self, cnv):
        self._canvas = cnv
        
        self._canvas_shape = {
            fshape.POINT: "point",
            fshape.POLYLINE: "line",
            fshape.CURVE: "line",
            fshape.POLYGON: "area",
            fshape.POLYGON_CURVE: "area",
            fshape.TEXT: "text"
        }
        # situos nustatymus reikia perkelti i self._css_shape[]
        #self.pixel_radius = 1.0 # pixel size in 0 level
        #self.line_width = 1.5 # 0.5, pixel 1.0
        
        self.load_default_style()
        
    
    def load_default_style(self):
        """ sitie css nustatymai pasirenkami pacioje pradzioje ir gali buti perrasyti _css_symbol, _css_element
             elementas: (canvas.POINT, symbol=None, points,....)
             cia pateiktas reiksmes galima perrasyti .css faile point {}
        """
        self._css_shape = {
            "point": {"color": (255,0,0), "paint": fshape.FILL, "z-index":0},
            "line": {"color": (0,255,0), "paint": fshape.STROKE, "z-index":0},
            "area": {"color": (0,0,255), "paint": fshape.FILL, "z-index":0},
            "text": {"color": (0,0,0), "angle":0, "paint": fshape.FILL, "z-index":0}
        }
        
        # jeigu simbolis yra nurodytas, tai cia jo stiliaus aprasymas
        self._css_symbol = {
            "graphics": {"z-index":1000, "color": (255,0,0), "line-width":0.12} # ocad simboliams kurie yra paversti i grafika
            #"901_1": {"name":"Road", "color": (204, 204, 204)}
        }

        
    def get_shapes_style(self):
        return self._css_shape

        
    def get_symbols_style(self):
        return self._css_symbol

        
    def set_symbol_style(self, symbol, style):
        if symbol in self._css_symbol:
            self._css_symbol[symbol].update(style)
        else:
            self._css_symbol[symbol] = style
            
    
    def set_symbols_style(self, symbols_style):
        for symbol, style in symbols_style.items():
            self.set_symbol_style(symbol, style)

            
    def get_style(self, shape):
        #print "get_style: ", shape
        canvas_shape, symbol, inline_style = shape[0], shape[1], shape[2]
        style = self._css_shape[self._canvas_shape[canvas_shape]].copy() # uzteks shallow copy?
        
        if symbol != None and symbol in self._css_symbol:
            style.update(self._css_symbol[symbol])
        
        #if symbol == "graphics":
        #    print "style/...", style, self._css_symbol["graphics"]
        #if id != None and id in self._css_element:
        #    style.update(self._css_element[id])
        
        if inline_style != None and len(inline_style):
            style.update(inline_style)
            
        zindex_list = [] # sarasas visu spalvu zindexu, kurios gali buti sitame objekte...
        if "z-index" in style:
            zindex_list.append(style.get("z-index"))
        
        if "color" in style:
            style["color"] = map(lambda x:x/255.0, style["color"]) # cairo naudoja (1,1,1)
        
        if "double-color" in style:
            style["double-color"] = map(lambda x:x/255.0, style["double-color"])
            zindex_list.append(style.get("double-z-index", -1))

        if "double-left-color" in style:
            style["double-left-color"] = map(lambda x:x/255.0, style["double-left-color"])
            zindex_list.append(style.get("double-left-z-index", -1))

        if "double-right-color" in style:
            style["double-right-color"] = map(lambda x:x/255.0, style["double-right-color"])
            zindex_list.append(style.get("double-right-z-index", -1))
        
        if "symbol-data" in style:
            """silmbolyje gali buti ivairiu spalvu, todel reikia patikrinti ju zindex'us """
            for shape in style["symbol-data"]:
                inline_style = shape[2]
                if "z-index" in inline_style:
                    zindex_list.append(inline_style["z-index"])
        
        
        style["z-index-list"] = sorted(zindex_list) #, reverse=True)
        
        #f symbol==None:
        #    style["z-index"] = 0#100000
        
        return style

        
    def setup_style(self, ctx, type, style):
        if type == fshape.POINT:
            #if "data" in style:
            #    print "DATA IN STYLE!"
            #    pass
            if "line-width" in style:
                ctx.set_source_rgb(*style["color"])
                ctx.set_line_width(style["line-width"])
                ctx.set_dash((), 0)
            else:
                ctx.set_source_rgb(*style["color"])

        elif type == fshape.POLYLINE:
            ctx.set_source_rgb(*style["color"])
            
            if "line-width" in style:
                ctx.set_line_width(style["line-width"])
                ctx.set_dash((), 0)
            if "line-cap" in style:
                ctx.set_line_cap(style["line-cap"])
            if "line-join" in style:
                ctx.set_line_join(style["line-join"])
            ctx.set_dash((), 0)
            
        elif type == fshape.CURVE:
            ctx.set_source_rgb(*style["color"])
            if "line-width" in style:
                line_width = style["line-width"]
                ctx.set_line_width(line_width) # or self._canvas.line_width)
                if not line_width:
                    ctx.set_source_rgba(0,0,0,0)
                
            if "line-cap" in style:
                ctx.set_line_cap(style["line-cap"])
            if "line-join" in style:
                ctx.set_line_join(style["line-join"])
            #if "dash-pattern" in style:
            #    pattern = style["dash-pattern"]
            #    ctx.set_dash((pattern[2], pattern[5]), 0)
            #else:
            ctx.set_dash((), 0)
                
        elif type == fshape.POLYGON:
            ctx.set_source_rgb(*style["color"])
            if "line-width" in style:
                ctx.set_line_width(style["line-width"])
                ctx.set_dash((), 0)
            
        elif type == fshape.POLYGON_CURVE:
            ctx.set_source_rgb(*style["color"])

            if "line-width" in style:
                ctx.set_line_width(style["line-width"])
                ctx.set_dash((), 0)
            if "line-cap" in style:
                ctx.set_line_cap(style["line-cap"])
            if "line-join" in style:
                ctx.set_line_join(style["line-join"])
                
        elif type == fshape.TEXT: # unformatted text
            ctx.set_source_rgb(*style["color"])

            ctx.select_font_face('Arial', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            
            #if "font-size" in style:
            #    ctx.set_font_size(style["font-size"] / 4) #2.02
                
            #print "SETUP TEXT: italic: ", style.get("font-style", cairo.FONT_SLANT_NORMAL)
                
            ctx.select_font_face(style.get("font-name", 'Arial'), style.get("font-style", cairo.FONT_SLANT_NORMAL), style.get("font-weight", cairo.FONT_WEIGHT_NORMAL))
            
            #print "TEXT STYLE: ", style
        
    
    def get_symbol_shapes(self, symbol_id):
        return self._css_symbol[symbol_id].get("symbol-data", [])

        
    def get_bbox(self, shape):
        if shape.is_point() and shape.get_symbol():
            point = shape.get_data()
        
            shapes = self.get_symbol_shapes(shape.get_symbol())
            if not len(shapes): # tai nera ocad point objektas o paprastas .shp taskas
                return shape.bbox()
            
            bounds = [inf, inf, -inf, -inf]
            for shape in shapes:
                shape = fshape.Shape.decompress(shape)
                bbox = shape.bbox()

                if bbox[0] < bounds[0]: bounds[0] = bbox[0]
                if bbox[1] < bounds[1]: bounds[1] = bbox[1]
                if bbox[2] > bounds[2]: bounds[2] = bbox[2]
                if bbox[3] > bounds[3]: bounds[3] = bbox[3]
            #print "bounds: ", bounds
            mx = max(map(lambda x:abs(x), bounds)) # imituojame obkejto apsukima aplink centra 0,0
            bounds = (-mx, -mx, mx, mx)
            
            width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
            #print "width, height", width, height
            
            c = math.sqrt(math.pow(width, 2) + math.pow(height, 2)) / 2.0
            # padidiname ribas pagal spinduli, kad galetume apsukti aplink asi
            return (point.x-c, point.y-c, point.x+c, point.y+c)
        
        #if shape.is_path() and shape.get_symbol():
        #    style = self.get_style([shape.get_type(), shape.get_symbol(), shape.get_style()])
        #    width = style.get("line-width", 0)

        #    double_width = style.get("double-width", 0)
        #    if double_width:
        #        width = double_width + style.get("double-left-width", 0) + style.get("double-right-width", 0)
        #    print "width: ", width
        #    return shape.bbox(border = width)
        else:
            return shape.bbox()
                
    
    #Load css settings file
    def load_css_file(self, css_file_path):
        data = StyleFile.read_css_file(css_file_path)
        
        for key, style in data.items():
            #print "key", key, " : ", style
            if key.startswith("."): # simbolis
                symbol_id = key[1:]
                self.set_symbol_style(symbol_id, style)
            else: # shape text, area, etc.
                if key in self._css_shape:
                    self._css_shape[key].update(style)
                else:
                    self._css_shape[key] = style
                        
    
    def create_svg_symbol(self, elements, symbol_id, prj):
        svg_file = "symbols/%s.svg" % symbol_id
        fo = file(svg_file, 'w')
        shapes = self.create_symbol(elements, prj)
        #self._symbols[symbol_id] = shapes
        
        surface = cairo.SVGSurface(fo)
        ctx = cairo.Context(surface)
        self._canvas.setup_context(ctx)

        for shape in shapes:
            self._canvas.draw_shape(ctx, shape, self.get_style(shape), fill_or_stroke=True)
        
        surface.finish()
        

    def sorted_by_zindex_with_style2(self, elements):
        elements_with_style = []
        for id in elements:
            obj = self._canvas.get_object_by_id(id)
            elements_with_style.append((obj, self.get_style(obj), id))
            #elements_with_style.extend(self.create_graphics(id))
        
        elements_with_style.sort(key=lambda x:x[0][1]) # sort by symbol id, 
        # Starting with Python 2.2, sorts are guaranteed to be stable. 
        # That means that when multiple records have the same key, their original order is preserved.
        return sorted(elements_with_style, key=lambda x: x[1].get("z-index", -1))
      

    def create_zindex(self, elements):
        """returns dict: {zindex0:[elements,...], zindex1:[elements,...], ...}"""
        elements_zindex = {}
        
        #for index in self.color_index:
        #    elements_zindex[index] = []
                    
        for id in elements:
            obj = self._canvas.get_object_by_id(id)
            style = self.get_style(obj)
            
            zindex_list = style.get("z-index-list", [])
            for index in zindex_list: # visi simbolyje galimi zindexai
                if not index in elements_zindex:
                    elements_zindex[index] = []
            
            if not "z-index" in style:
                print "SYMBOL:", obj[1], " SR:", style, obj#- cia symbol-data tikrai yra! reikia, kodel jos reiksme nera parsinama parse!
                raise Exception("no zindex!")
            
            #zindex = style.get("z-index") # jeigu negrazins zindexo - tai cia bus sudetinis objektas kuri apdorojus bus grazinti nauji elementai su didesniais zindex uz 0
            elements_zindex[zindex_list[0]].append((obj, style, id)) # galima nerusiuoti pagal simboli - nes nera svarbu ka anksciau nupiesime
        
        return elements_zindex
