"""
Brezinio pagrindas, visada galima paprasyti nubraizyti jo gabala
0--------
|     ___
|    |___|
|
"""

# python system libs
import os
import pickle
import math
import random

# 3party libs
import cairo
from rtree import Rtree


#my libs
import fshape
from fcadfile import ShapeFile, StyleFile, OcadFile
from utils import timer, Point, Area, inf
from styler import Styler
from painter import Painter, ContextObjectsListener, ContextBoundsListener
from projection import GisProjection
        
        
class GisCanvas:
    """
    Top-level drawing class that contains a list of all the objects to draw.
    """
    def __init__(self):
        """Initialise the class by creating an instance of each object."""
        self._ratio_index = (0.05, 0.1, 0.2, 0.5, 1, 2, 4, 8, 16, 32, 64) # pagal sita dydi turi kisti tasko atstumas nuo zoominimo centro
        self._zoom_level = self._ratio_index.index(4) # 0-dirbame su realiomis koordinatemis - kitur koordinates yra gaunamos atliekant dalyba... todel nera labai tikslios
        
        self._device_area = None # gtk.gdk.Rectangle()
        
        self._shapes = [] # shapes data
        self._index_rtree = Rtree() # shapes indexes in self._shapes
        
        self._offset = Point(0, 0) #- naudojamas ctx.translate() #device koordinates
  
        self._prj = GisProjection()
        self._styler = Styler(self)
        self._painter = Painter(self._styler)
        
        self._drag_to_center = True # jeigu norime kad resize metu (bus iskviestas set_device_area) butu iskvietsas center()

        
    def load(self, name):
        self._styler.load_css_file("%s.css" % name)
        self.load_fcad_file("%s.fcad" % name)

        
    def save(self, file_name):
        #self.create_fcad_file("%s.fcad" % file_name)
        ShapeFile.create_fcad_file("%s.fcad" % file_name, self._shapes)
        StyleFile.create_css_file("%s.css" % file_name, self._styler.get_shapes_style(), self._styler.get_symbols_style(), prettyprint=True)
        
        #self._styler.create_css_file("%s.css" % file_name, prettyprint=True)
        
        
        
    def clear(self):
        print "clear canvas!"
        self._zoom_level = self._ratio_index.index(1)
        self._offset = Point(0, 0)
       
        self._shapes = []
        #self._cairo_paths = {}
        self._index_rtree = Rtree()
        self._styler.load_default_style()

       
    def load_pickle(self, file_path):
        timer.start("loading shapes.p")
        if os.path.exists(file_path):
            self._shapes = pickle.load(open(file_path, "rb"))
            
            if len(self._shapes):
                def generator_function(points):
                    for i, obj in enumerate(points):
                        if obj == None: continue
                        yield (i, self._styler.get_bbox(fshape.Shape.decompress(obj)), obj)
                self._index_rtree = Rtree(generator_function(self._shapes))
        timer.end("loading shapes.p")

        
    def save_pickle(self, file_path):
        pickle.dump(self._shapes, open(file_path, "wb"))

        
    def load_fcad_file(self, file_path):
        timer.start("loading shapes.fcad")
        self._shapes = ShapeFile.read_fcad_file(file_path)
    
        if len(self._shapes):
            def generator_function(points):
                for i, obj in enumerate(points):
                    if obj == None: continue
                    yield (i, self._styler.get_bbox(fshape.Shape.decompress(obj)), obj)
            self._index_rtree = Rtree(generator_function(self._shapes))
        timer.end("loading shapes.fcad")
     
     
    def set_device_area(self, area): # atnaujina screen.resize()
        self._device_area = area
        
        if self._drag_to_center:
            self.center()
            self._drag_to_center = False


    def get_shape_by_id(self, id):
        compressed_shape = self._shapes[id]
        if compressed_shape == None: return None
        return fshape.Shape.decompress(compressed_shape)

        
    def get_object_by_id(self, id):
        return self._shapes[id]

        
    def draw_100(self, ctx, area):
        """100% draw for printing, no scale, area in user coordinates"""
        page_area = Area(0, 0, area.width, area.height)
        #ctx.rectangle(0, 0, area.width, area.height) 
        #ctx.clip() # tam kad nepaisytu uzh sito staciakampio ribu (tada gaunasi dubliuotos linijos)
        #self.background(ctx, page_area) # paint white background
        
        self._painter.background(ctx, page_area, color=(1,1,1), clip=True) # paint white background
        self._painter.setup(ctx, transform={"translate":(-area.x, -area.y)})

        radius = 0 #self.pixel_radius + self.line_width # ne cia reikia prideti radiusa, o ten kur dedame i cavas'a shape'us
        
        elements = self._index_rtree.intersection((area.x-radius, area.y-radius, area.x+area.width+radius, area.y+area.height+radius))
        elements_zindex = self._styler.create_zindex(elements) # jis yra pilnas visu galimu zindex'u sarasas - pradzioje dalis ju gali buti ir tusti []
        
        timer.start("draw100")
        for zindex in sorted(elements_zindex.keys()):
            for element in elements_zindex[zindex]:
                self._painter.draw(element, update=elements_zindex) # kazka visada nupaiso - bet dar papildomai gali iterpti elementu su didesniu zindex'u
                # tie elementai bus nupaisomi veliau.
            
        timer.end("draw100")
            
            
    
    
    def draw_object(self, ctx, id, fill_or_stroke=True):
        #self.apply_transforms(ctx) # drag and scale
        self._painter.setup(ctx, transform={"translate":self.get_offset(), "scale": self.get_ratio()})
        
        elements_zindex = self._styler.create_zindex([id])
        
        timer.start("draw single object")
        for zindex in sorted(elements_zindex.keys()):
            for element in elements_zindex[zindex]:
                self._painter.draw(element, update=elements_zindex, fill_or_stroke=fill_or_stroke) # kazka visada nupaiso - bet dar papildomai gali iterpti elementu su didesniu zindex'u
            
        timer.end("draw single object")
    

    def draw(self, ctx, area, fill_or_stroke=True):
        """Draw the complete drawing by drawing each object in turn."""
        
        self._painter.background(ctx, area, color=(1,1,1), clip=True) # paint white background
        self._painter.setup(ctx, transform={"translate":self.get_offset(), "scale": self.get_ratio()})
        
        # paishysime tik tuos tashkus kurie pakliuna i vartotojo langa
        # reikia device_area konvertuoti i user koordinates
        x, y = self.device_to_user(Point(area.x, area.y))
        x2, y2 = self.device_to_user(Point(area.x + area.width, area.y + area.height))
        
        radius = 0 #self.pixel_radius + self.line_width # ne cia reikia prideti radiusa, o ten kur dedame i cavas'a shape'us
        # geriau cia, nes paprasciau yra iskviesti nupaisyti didesni gabala nei paskaiciuoti tikslu pvz linijo simboliu dydi...
        
        elements = self._index_rtree.intersection((x-radius, y-radius, x2+radius, y2+radius))
        elements_zindex = self._styler.create_zindex(elements) # jis yra pilnas visu galimu zindex'u sarasas - pradzioje dalis ju gali buti ir tusti []
        
        timer.start("draw")
        for zindex in sorted(elements_zindex.keys()):
            for element in elements_zindex[zindex]:
                #print "element: ", element[0][0]
                self._painter.draw(element, update=elements_zindex, fill_or_stroke=fill_or_stroke) # kazka visada nupaiso - bet dar papildomai gali iterpti elementu su didesniu zindex'u
                # tie elementai bus nupaisomi veliau.
            
        timer.end("draw")
        
        
        
    def get_ratio(self, level=None):
        if level == None: level = self._zoom_level 
        return self._ratio_index[level]

    
    def drag2(self, drag_offset):
        self._offset = Point(self._offset.x + drag_offset.x, self._offset.y + drag_offset.y)
    
        
    def get_offset(self):
        return self._offset


    def find_objects_at_position(self, point):
        #ctx = self.get_context(transform=False) # naujas kontekstas kur paisysime, transformuoti nereikia - nes tai padarys .draw()
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 0,  0)) # naujas kontekstas kur paisysime, transformuoti nereikia - nes tai padarys .draw()
      
        area = Area(point.x, point.y, 1, 1)

        listener = ContextObjectsListener(point)
        listener_id = self._painter.addContextListener(listener)

        try:
            self.draw(ctx, area, fill_or_stroke=False) # nepaisysime tik sukursime path'us context'e ir su jais kazka atliks ContextListeneris
        finally:
            self._painter.removeContextListener(listener_id)
        
        return listener.get_objects() # rastu elementu indeksai

        
    def get_shape_redraw_area(self, id):
        #ctx = self.get_context(transform=False)
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 0,  0))
        
        shape = self.get_object_by_id(id)
        if shape == None: return None
        
        listener = ContextBoundsListener()
        listener_id = self._painter.addContextListener(listener)
        
        try:
            self.draw_object(ctx, id, fill_or_stroke=False)
        finally:
            self._painter.removeContextListener(listener_id)
            
        area = listener.get_area()
        #print "Area: ", area
        return area
        
        
    def device_to_user(self, point):
        #x, y = self.ctx.device_to_user(point.x, point.y)
        #x, y = self.get_context().device_to_user(point.x, point.y)
        
        ratio = self.get_ratio()
        offset = self.get_offset()
        x, y = (point.x - offset.x)/ratio, (point.y - offset.y)/ratio
        
        return Point(x, y)

        
    def user_to_device(self, point, offset=(0, 0)):
        #x, y = self.ctx.user_to_device(point.x, point.y)
        #x, y = self.get_context().user_to_device(point.x, point.y)
        
        ratio = self.get_ratio()
        drag_offset = self.get_offset()
        x, y = (point.x  * ratio) + drag_offset.x, (point.y  * ratio) + drag_offset.y
        
        return Point(x + offset[0], y + offset[1])

    
    def add(self, shape):
        id = len(self._shapes) # top element index
        self._shapes.append(shape.compress())
        self._index_rtree.add(id, self._styler.get_bbox(shape))
        return id

        
    def remove(self, id):
        shape = self.get_shape_by_id(id)
        self._index_rtree.delete(id, shape.bbox()) # po sito as jau niekada tokio id negausiu (nes viskas eina per rtree)
        self._shapes[id] = None

        
    def replace(self, id, shape):
        old = self.get_shape_by_id(id)
        #print "before :", list(self._index_rtree.intersection(old.bbox())) 
        if old != None:
            self._index_rtree.delete(id, old.bbox())
        #print "after :", list(self._index_rtree.intersection(old.bbox()))
        self._shapes[id] = shape.compress()
        self._index_rtree.add(id, self._styler.get_bbox(shape))
    
        
    def zoom(self, direction, center=None):
        """center cia yra device koordinatemis - jeigu butu paspausta su zoom irankiu peles pagalba"""
        new_zoom_level = self._zoom_level+direction
        if new_zoom_level in range(0, len(self._ratio_index)):
            #esamas centro taskas atlikus zooma turi islikti toje pacioje vietoje
            center = center or Point(self._device_area.width/2, self._device_area.height/2) # vartotojo parinktas tashkas arba tiesiog centras
            center_user = self.device_to_user(center)
            
            # gauname priesh tai buvusio centro koordinates naujame zoom lygyje
            new_ratio = self.get_ratio(new_zoom_level)
            new_center = Point(center_user.x * new_ratio, center_user.y * new_ratio)
                
            # gauname centro poslinki (per tiek reikia perstumti visa vaizdeli)
            self._offset = Point(center.x - new_center.x, center.y - new_center.y) # naujas poslinkis
            #print "zoom: ", self._offset
            self._zoom_level = new_zoom_level
            return True
        return False


    def center(self, point=None):
        """center to user point"""
        if not point:
            bounds = self._index_rtree.bounds
            point = Point((bounds[0]+bounds[2])/2.0, (bounds[1]+bounds[3])/2.0)
        
        hand = self.user_to_device(point)
        to = Point(self._device_area.width/2, self._device_area.height/2)
        self.drag2(Point(to.x-hand.x, to.y-hand.y))

        
    def get_projection(self):
        return self._prj
        
    def get_styler(self):
        return self._styler

        
    def load_ocad_file(self, file_path, generator=True):
        #import ocadfile
        #self.add(Shape(1, Point(0, 0), symbol="graphics")) # koordinaciu centras

        self._prj = GisProjection()
        self._zoom_level = self._ratio_index.index(4)
        
        of = OcadFile(file_path, self._prj)
        #self._styler.load_ocad_symbols(of, prj)

        timer.start("Adding ocad symbols")
        self._styler.set_symbols_style(of.get_symbols_style())
        timer.end("Adding ocad symbols")
        
        
        timer.start("Adding ocad elements")
        shapes = of.get_shapes()
        print "Shapes: ", len(shapes)
        for shape in shapes:
            self.add(shape)
        timer.end("Adding ocad elements")
        
        self.center()

        
    def load_shape_file(self, file_path, generator=True):
        import shapefile
        from random import randint

        sf = shapefile.Reader(file_path)
        print "Number of shapes: ", sf.numRecords
        
        self.add(fshape.Shape(1, Point(0, 0), style={"z-index":99})) # koordinaciu centras
        
        if self.prj.scale == 1: # pirmas kartas
            prj = GisProjection(self, sf.bbox)
            #po sito ciklo jau turesime zemelapio ribas
            center = prj.map_to_user(prj.get_center())
            self.center(center)
            self.prj = prj
                    
        timer.start("Adding shapes")
        symbol = sf.shapeName.split("/")[-1]
        self._styler.set_symbol_style(symbol, {"color": (randint(0,255),randint(0,255),randint(0,255))})
        
        for shape in sf.ogis_shapes(self.prj):
            self.add(fshape.Shape(shape.shapeType, shape.points, symbol=symbol))
        timer.end("Adding shapes")
                    
        

    def add_random_points(self, number, area, generator=True):
        """Kai generator=False - sunaudoja maziau atminties ikrovimo metu, bet trunka gerokai leciau
        """
        self._shapes = []
        timer.start("Adding random data")

        from random import randint
        for x in range(0, number):
            color = 65536 * randint(0,255) + 256 * randint(0,255) + randint(0,255) # RGBint
            x, y = randint(2, area.width), randint(2, area.height)

            if not generator: # darysime rtree.add kiekvienam taskui atskirai
                self.add(fshape.Shape(1, Point(x, y), color=color))
            else:
                self._shapes.append((1, color, x, y))
        
        if generator:
            def generator_function(points):
                for i, obj in enumerate(points):
                    yield (i, (obj[2], obj[3], obj[2], obj[3]), obj)
            self._index_rtree = Rtree(generator_function(self._shapes))
        
        timer.end("Adding random data")
        #print list(self._index_rtree.intersection((0,0,100,100)))
            
            


