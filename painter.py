import math
import time

import cairo

import fshape
import geometry
from stroker import Stroker
from utils import uniqfy, Area


class Painter:
    def __init__(self, styler):
        self.styler = styler
        #self._cairo_paths = {} # jeigu kesuojame elementu path'us - tai ia juos galim susideti

        # siuos nustatytmus reikia perkelti i styler!
        self.pixel_radius = 1.0 # pixel size in 0 level
        self.line_width = 1.5 # 0.5, pixel 1.0
        self._context_listeners = {}
        

    def background(self, ctx, area, color=None, clip=False):
        #ctx.rectangle(0, 0, area.width, area.height)
        self._area = area
        
        ctx.rectangle(area.x, area.y, area.width, area.height)
        if clip:
            ctx.clip_preserve()
        
        if color:
            ctx.set_source_rgb(*color)
            ctx.fill()
        else:
            ctx.new_path() # jeigu nreikia backgroundo tai isvalome rectangle path'a
        

    def setup(self, ctx, transform={}):
        
        ctx.set_line_width(self.line_width)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        
        ctx.select_font_face('Arial', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(2.02)
        
        #ctx.set_antialias(cairo.ANTIALIAS_NONE)
        
        options = ctx.get_font_options()
        #options.set_antialias(cairo.ANTIALIAS_GRAY)
        #options.set_antialias(cairo.ANTIALIAS_DEFAULT) # blogiau nei GRAY
        #options.set_subpixel_order(cairo.SUBPIXEL_ORDER_RGB)
        options.set_hint_metrics(cairo.HINT_METRICS_OFF) 
        options.set_hint_style(cairo.HINT_STYLE_NONE) # kitaip scalinant blogai atrodo juoda/pilka
        ctx.set_font_options(options)
        
        if "translate" in transform:
            ctx.translate(*transform["translate"])
        if "scale" in transform:
            ctx.scale(transform["scale"], transform["scale"])

        self._ctx = ctx
        #self._elements_zindex = {}
        
    
    
    def addContextListener(self, listener):
        key = time.time()
        self._context_listeners[key] = listener
        return key
        
    def removeContextListener(self, key):
        #print "remove", key, "from", self._context_listeners
        del self._context_listeners[key]
        
    
    def callContextListeners(self, ctx, id, draw_type):
        for listener in self._context_listeners.values():
            listener.run(ctx, id, draw_type)
            
    
    def draw(self, element, update={}, fill_or_stroke=True):
        """draw element - add new (width higher z-index) subelements to "update - zindex" if such are created"""
        shape, style, id = element
        self._elements_zindex = update
        
        if style.get("status", 0) == 2: # hidden; 1-protected; 0-normal
            return
        
        self.draw_shape(self._ctx, shape, style, fill_or_stroke=fill_or_stroke, id=id) # kazka jis visada nupies - kadangi isrusiuota pagal z-index (reiskia kazkuri elemento dalis atitinka sita z-index)

        
    def draw_later(self, zindex, element):
        #print "draw later: ", element
        self._elements_zindex[zindex].append(element)
        

    def draw_shape(self, ctx, shape, style, fill_or_stroke=True, id=None):
        """ get_extents - [] i ji sudesime bounds tu objektu kurie sukuriami darbo eigoje..."""
        #print "type: ", type, "symbol"
        type, symbol, inline_style, points = shape[0], shape[1], shape[2], shape[3:]
        #print "shape: ", type, symbol, inline_style
        
        self.styler.setup_style(ctx, type, style) # reikia nustatyti figuros stiliu iki to kai padarome save(), nes kitaip po restore() mes ji prarastume
        # context_listener.run() reikia kviesti po restore, tam kad vel dirbtume su normaliom koordinatem (o ne transformuotom su translate ar rotate)

        ctx.save()
        
        if "translate" in style:
            ctx.translate(*style.get("translate"))
        if "rotate" in style:    
            ctx.rotate(style.get("rotate"))
        
        if type == fshape.POINT:
            self.draw_point2(ctx, points, style, fill_or_stroke, id)
            
        elif type == fshape.POLYLINE:
            self.draw_line(ctx, points, style, fill_or_stroke, id)
            
        elif type == fshape.CURVE:
            self.draw_curve2(ctx, points, style, fill_or_stroke, id)
            
        elif type == fshape.POLYGON:
            self.draw_polygon(ctx, points, style, fill_or_stroke, id)

        elif type == fshape.POLYGON_CURVE:
            self.draw_polygon_curve(ctx, points, style, fill_or_stroke, id)

        elif type == fshape.TEXT: # unformatted text
            self.draw_text(ctx, points, style, fill_or_stroke, id)
        
        else:
            print "WTF@"
            
        ctx.restore() # toku budu bus atstatyti defaultiniai settingai! nereiks tikrinti kokie fill_rule ar panasiai nustatyti simboliu paisymo metu
        
        

        #if context_listener and not composite:
        #    context_listener.run(ctx, type, transform)
            
        #if fill_or_stroke:
        #    self.styler.render_shape(ctx, type, style) 
            #- sita reikia nakinti ir padaryti kad metodai patys rupintusi fill/stroke ir tikrintu context listeneri.
            # nes pvz linija su dviem krastai iskarto nupaiso dvi savo sonines linijas tai ten reikia ir kviesti context listeneri?

        """
        if composite:
            bbox = self.css.get_bbox(Shape.decompress(shape))
            ctx.rectangle(bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1])
            ctx.set_source_rgb(255,0,0)
            ctx.set_line_width(1.0)
            ctx.set_dash((), 0)
            ctx.stroke()
        """


            
    def draw_text(self, ctx, points, style, fill_or_stroke=True, id=None):
        x, y = points[0], points[1]
        #ctx.select_font_face('Arial', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        #ctx.set_font_size(0.5)
        #color = ((rgbint >> 16) & 255, (rgbint >> 8) & 255, rgbint & 255)
        
        #ctx.set_source_rgb(*style["color"])
        
        #fascent, fdescent, fheight, fxadvance, fyadvance = ctx.font_extents()[2]
        #xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(text)
        
        #print "Font Face: ", ctx.get_font_face().get_family(), ctx.font_extents()
        
        font_height = ctx.font_extents()[2]
        
        ctx.save()
        ctx.move_to(x, y)
        ctx.rotate(math.radians(-style["angle"]/10.0)) # -angle; nes rotatiname ne objekta o pagrinda
        
        (x, y) = ctx.get_current_point()
        text = style.get("text", "")
        for line in text.splitlines():
            #ctx.show_text(line) # antialiasing suck - probably because of glyph caching
            ctx.text_path(line)
            ctx.rel_move_to(-(ctx.get_current_point()[0] - x), font_height)
        
        ctx.restore()
        
        self.callContextListeners(ctx, id, fshape.FILL)
        
        if fill_or_stroke:
            ctx.fill()
            
        #self.draw_line(ctx, points, {"color":(255,0,0)}, fill_or_stroke)
        

    """
    def draw_point_symbol(self, ctx, symbol_data, fill_or_stroke=True, context_listener=None, transform=None):
        #self.setup(ctx) - naudojamas tik pradzioje....
        
        #print "shapes: ", symbol_data, type(symbol_data)
        
        for shape in symbol_data:
            style = self.styler.get_style(shape)
            self.draw_shape(ctx, shape, style, fill_or_stroke, context_listener, transform)
            
            if not fill_or_stroke and context_listener: # draw_shape jau bus iskvietes context_listener.run()
                ctx.new_path()
    """

    def draw_point2(self, ctx, point, style, fill_or_stroke=True, id=None):
        x, y = point #[0], point[1]
        
        if "symbol-data" in style:
            symbol_data = style.get("symbol-data")
            angle = math.radians(-(style.get("angle", 0)/10.0)) # -angle; nes rotatiname ne objekta o pagrinda

            zindex_list = style.get("z-index-list", []) 
            
            for shape in symbol_data:
                new_style = self.styler.get_style(shape) # reikia kopijos...
                new_style.update({"translate":(x,y), "rotate":angle}) # prisegam informacija apie transformacija kuria reikia padaryti pries paisant
                
                zindex = new_style.get("z-index")
                
                if zindex == zindex_list[0]: #zindexas sutampa su einamuoju - galim piesti
                    #print "new_style", new_style
                    self.draw_shape(ctx, shape, new_style, fill_or_stroke, id)
                else:
                    self.draw_later(zindex, (shape, new_style, id))
                
        else:
            if "radius" in style:
                radius = style.get("radius")
            else:
                radius = self.pixel_radius
            
            draw_type = fshape.STROKE if ("line-width" in style or style.get("paint", fshape.FILL) == fshape.STROKE) else fshape.FILL
            #if draw_type == canvas.STROKE:
            #    radius += style.get("line-width", 0)/2.0
            
            #print "graw radius realpoint!", style.get("radius"), style.get("line-width"), radius

            ctx.arc(x, y, radius, 0, 2 * math.pi) 
        
            
            #print draw_type, "WTF?", style.get("line-width", "?")
            
            self.callContextListeners(ctx, id, draw_type)

            if fill_or_stroke:
                if draw_type == fshape.STROKE:
                    ctx.stroke()
                else:
                    ctx.fill()
        
    # nupaiso taska, kuriam duotos realios 100% (level 0) koordinates
    """
    def draw_point(self, ctx, point, style, fill_or_stroke=True, context_listener=False, symbol=None):
        x, y = point #[0], point[1]
        
        if symbol:
            ctx.translate(x, y)
            angle = math.radians(-(style.get("angle", 0)/10.0))
            ctx.rotate(angle) # -angle; nes rotatiname ne objekta o pagrinda
            
            self.styler.draw_point_symbol(ctx, symbol, fill_or_stroke, context_listener, transform={"translate":(x,y), "rotate":angle})
                
        else:
            radius = style.get("radius", 0) or self.pixel_radius
            
            ctx.arc(x, y, radius, 0, 2 * math.pi) 
    """

                
    def draw_line(self, ctx, line, style, fill_or_stroke=True, id=None):
        #ctx.save()
        #print "draw_line angle: ", style["angle"]
        ctx.move_to(line[0], line[1])
        ctx.rotate(math.radians(-style.get("angle", 0)/10.0)) # -angle; nes rotatiname ne objekta o pagrinda

        #ctx.move_to(line[0], line[1])
        for i in xrange(2, len(line), 2):
            ctx.rel_line_to(line[i]-line[i-2], line[i+1]-line[i-1])
        
        self.callContextListeners(ctx, id, fshape.STROKE)
        
        if fill_or_stroke:
            ctx.stroke()

        #ctx.restore()

        
    def draw_polygon(self, ctx, polygon, style, fill_or_stroke=True, id=None):
        first = [polygon[0], polygon[1]]
        ctx.move_to(first[0], first[1])
        
        i = 2
        line_length = len(polygon)
        while i < line_length:
            ctx.line_to(polygon[i], polygon[i+1])
            
            if polygon[i] == first[0] and polygon[i+1] == first[1] and (i+2) < line_length:
                i += 2
                first[0], first[1] = polygon[i], polygon[i+1]
                ctx.move_to(first[0], first[1])
            
            i += 2
            
        ctx.close_path()
        
        draw_type = fshape.STROKE if "line-width" in style else fshape.FILL
        
        self.callContextListeners(ctx, id, draw_type)
        
        if fill_or_stroke:
            if draw_type == fshape.STROKE:
                ctx.stroke()
            else:
                ctx.fill()

       
    def draw_curve2(self, ctx, curve, style, fill_or_stroke=True, id=None):
        #print "draw_curve2"
        stroker = Stroker(self, ctx, style)
        
        if len(curve) == 1: # atsiustas cairo.Path objektas - kuri anksciau sugeneravo strokeris
            ctx.append_path(curve[0])
        else:
            ctx.move_to(curve[0], curve[1]) # 0,1 <- pirmas taskas neturi handlo is kaires, bet jie sutampa
            for i in range(2, len(curve), 6):
                P2h = (curve[i], curve[i + 1])
                
                P3h = (curve[i + 2], curve[i + 3])
                P4 = (curve[i + 4], curve[i + 5])
                
                ctx.curve_to(P2h[0], P2h[1], P3h[0], P3h[1], P4[0], P4[1])
                
                stroker.check_special_point(i+4) # dash or corner
                
                #if(self._area and (P4[0] < self._area.x or P4[0] > self._area.x+self._area.width)): # or P4[1] < self._area.y or P4[1] > self._area.y + self._area.height)):
                    #print self._area, P4
                    #break

            
        #if fill_or_stroke:
        stroker.draw(fill_or_stroke, id)

           
    def draw_polygon_curve(self, ctx, curve, style, fill_or_stroke=True, id=None):
        ctx.move_to(curve[0], curve[1])
        
        #print "print fill rule: ", ctx.get_fill_rule()
        
        curve_length = len(curve)
        i = 2
        while i < curve_length:
            try:
                #print "i:::", i
                if curve[i+2] == None: # hole, +2 - nes praleidziam sito tasko handle'a is kaires
                    #print "Hole: ", i
                    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)                     
                    ctx.move_to(curve[i + 3], curve[i + 4]) # pereiname prie pirmojo skyles tasko
                    i += 7 # dar praleidziam pirma handle
                
                P2h = (curve[i], curve[i + 1])
                P3h = (curve[i + 2], curve[i + 3])
                P4 = (curve[i + 4], curve[i + 5])
                
                ctx.curve_to(P2h[0], P2h[1], P3h[0], P3h[1], P4[0], P4[1])
                i += 6
            except:
                print "Exception", ["%i:%s" % (i, str(curve[i])) for i in range(len(curve))], i, P2h, P3h, P4
                raise

        ctx.close_path()

        draw_type = fshape.STROKE if "line-width" in style else fshape.FILL

        self.callContextListeners(ctx, id, draw_type)

        if fill_or_stroke:
            if draw_type == fshape.STROKE:
                ctx.stroke()
            else:
                ctx.fill()

                
    def draw_svg(self, ctx, filename):
        svg = rsvg.Handle(file=file_name)
        symbol_dpi = 75
        svg.set_dpi(symbol_dpi)
        svg.render_cairo(ctx)
            
        #bbox:
        #width, height = svg.props.width, svg.props.height
        #c = math.sqrt(math.pow(width, 2) + math.pow(height, 2)) / 2.0
        #return (point.x-c, point.y-c, point.x+c, point.y+c)
        

        
class ContextBoundsListener:
    def __init__(self):
        #self._extents = []
        self._x_list = [] # visos x koordinates
        self._y_list = [] # visos y koordinates
        
    def run(self, ctx, id, draw_type):
        
        if draw_type == fshape.STROKE:
            extents = ctx.stroke_extents()
        else:
            extents = ctx.fill_extents()

        top_left = ctx.user_to_device(*extents[:2])
        bottom_right = ctx.user_to_device(*extents[2:])
        
        self._x_list.append(top_left[0])
        self._x_list.append(bottom_right[0])
        self._y_list.append(top_left[1])
        self._y_list.append(bottom_right[1])

        #print "ContextBoundsListener.run: ", id, draw_type, extents
        ctx.new_path() # isvalome path'a

    def get_area(self):
        x, y = min(self._x_list), min(self._y_list)
        # pridedam po viena pixeli is visu krastu, nes kitaip kartais nesimato krastu antialiasingo
        return Area(math.floor(x)-1, math.floor(y)-1, math.ceil(max(self._x_list)-x)+2,  math.ceil(max(self._y_list)-y)+2)
        
        
class ContextObjectsListener:
    def __init__(self, point):
        self._point = point
        self._objects = []

    def run(self, ctx, id, draw_type):
        point = ctx.device_to_user(*self._point)
        #print "ContextObjectsListener.run:", id, draw_type, " point:", point
        
        in_context = ctx.in_stroke(*point) if draw_type == fshape.STROKE else ctx.in_fill(*point)
        if in_context:
            self._objects.append(id)
                    
        ctx.new_path() # isvalome path'a
    
    def get_objects(self):
        return uniqfy(self._objects)