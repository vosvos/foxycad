"""
Tapininkas tarp GTK ir Canvas
Tam kad galima butu paprasta pakeisti GTK kitu UI
Taip pat jis atsakyngas uz "statiniu" objektu uzpaisyma ant ekrano (liniuote, mygtukas, copyrightas, etc)
"""
import os.path

import cairo
import gtk, gobject

from canvas import GisCanvas
from fshape import Shape
from utils import Point, Area, timer, WAIT_ARROW, WAIT_CROSS
from bezier import draw_point, debug_points, poly_curve

class Screen(object):
    """
    Bazine ekrano klase primityviai realizuojanti visas pagrindines funkcijas, bet nebutinai efektyviausiu metodu
    Nenaudoja bufferiu ir expose metu visada perpaiso pilna ekrana, todel yra leta
    draw_invalid_regions - niekad nera kveciamas kdangi perpaisoma viskas
    """
    def __init__(self):
        self._canvas = GisCanvas()
        self._canvas.load("dump")
        self._device_area = None # keiciant programos lango dydi reikia perpaisyti naujus gabalus, tai cia isssaugosime ankstesni view dydi.
        # nededame jo i init, nes padarius clear - sitas dydis turi islikti
        self.init()

    def init(self):
        #print "init screen"
        self._drag_start = False # pagal tai nuspresime ka perpaisyti ir ka pastumti
        self._offset = Point(0, 0) # kiek paslinkti pradzios taska nuo praejusio karto
        self._screen_overlays = [] # statiniai ekrano elementai (SceenOverlay), liniuotes, copyright ir pan
        
    def clear(self):
        #print "screen clear..."
        self._canvas.clear()
        self.init()
    
    def get_area(self):
        return self._device_area
    
    def get_canvas(self):
        return self._canvas

    def ui_redraw(self): # user interface specific redraw - subclasses must implement
        pass

    def ui_open_file(self): # dialog
        pass

    def open_file(self, file_path):
        #self._surface_buffer = None
        
        extension = os.path.splitext(file_path)[1]
        if extension == ".shp":
            self._canvas.load_shape_file(file_path)
        elif extension == ".ocd":
            self._canvas.load_ocad_file(file_path)
        else:
            print "Unknown file format: %s" % extension
        self.redraw()
        
    def mouse_move(self, point): # jeigu yra state - tai reikia kad paspaustas peles klavisas ar kazkas panasaus
        #if self._canvas.get_context(): # no bitmask like: gtk.gdk.BUTTON3_MASK:
        user = self._canvas.device_to_user(point)
        map = self._canvas.get_projection().user_to_map(user)
        return "Device: (%i, %i) User: (%i, %i) Map: (%f, %f) " % (point.x, point.y, user.x, user.y, map.x, map.y)

        
    def draw_screen_overlays(self, context):
        #context.set_antialias(cairo.ANTIALIAS_GRAY) 
        #context.save()
        #context.set_antialias(cairo.ANTIALIAS_NONE)
        #context.set_operator(23) # difference

        for overlay in self._screen_overlays:
            if overlay:
                overlay.draw(context, self)
        #context.restore()


        
    def expose(self, ctx, area):
        """
        pats primityviausias ir patikimiausias expose - kuris visada perpaiso viska...
        """
        self.ctx = ctx
        self._canvas.drag2(self._offset) #jeigu pradetas draginimas tai reikia pastumti ir canvas'a - darome tai cia kadangi kartais ivyksta keli "tusti" motion_notify
        self._offset = Point(0, 0) # reikia cia nunulinti - kadangi kartais vyksta keli motion_notify()

        ctx.save() # del sito dabar blogai veiks zoom'inimas (nes tures klaidinga ctx'a), DragSWcreen sitos bedos neturi kadangi piesiama i ImageSurface
        self._canvas.draw(ctx, area)
        ctx.restore()
        self.draw_screen_overlays(ctx)
      
        
    def drag_start(self, point):
        self._drag_start = point
        #self._offset = Point(0, 0)
        
    def drag_end(self, point):
        #print "drag end!"
        self._drag_start = False
        self._offset = Point(0, 0)

        
    def drag(self, point):
        if self._drag_start:
            offset = Point(point.x - self._drag_start.x,  point.y - self._drag_start.y)
            self._offset = Point(self._offset.x + offset.x, self._offset.y + offset.y) 
            """kartais ivyksta keli "motion_notify" o redraw tarp ju neivyksta, 
                todel reikia saugoti sena self._offset.x ir ji nunulinti kai ivyksta update_drag_regions()
            """
            self._drag_start = point
            self.ui_redraw()
            #self.draw_area.queue_draw()

    def resize(self, area):
        self._device_area = area
        self._canvas.set_device_area(area)
        #print "resize"

    # turetu grazinti indexa pagal kuri galeciau pasalinti
    def add(self, screen_overlay):
        self._screen_overlays.append(screen_overlay)
        self.ui_redraw()
        return len(self._screen_overlays) - 1

    def remove(self, overlay_index):
        self._screen_overlays[overlay_index] = None
        self.ui_redraw()
        
    def replace(self, overlay_index, screen_overlay):
        self._screen_overlays[overlay_index] = screen_overlay
        self.ui_redraw()

    def redraw(self, regions=False):
        self.ui_redraw()

    def zoom(self, direction):
        if self._canvas.zoom(direction):
            self.redraw()

            
    def is_control(self, control, point):
        dcontrol = self._canvas.user_to_device(control)
        dpoint = self._canvas.user_to_device(point)
    
        draw_point(self.ctx, dcontrol.x, dcontrol.y, 1, stroke=False)
        rvalue = self.ctx.in_stroke(dpoint.x, dpoint.y) or self.ctx.in_fill(dpoint.x, dpoint.y)
        #print "iscontrol?", control, point, rvalue
        self.ctx.new_path()
        return rvalue
        
    #def find_objects_at_position(self, point):
    #    #point = Point(point.x + 0.5, point.y + 0.5)
    #    #upoint = self._canvas.device_to_user(point)
    #    #upoint = Point(upoint.x + 0.5, upoint.y + 0.5)
    #   #print "find_objects_at_position: ", point, upoint
    #    
    #    return self._canvas.find_objects_at_position(point)


    def add_shape(self, shape):
        id = self._canvas.add(shape)
        self.redraw(self._canvas.get_shape_redraw_area(id))
        return id
        
    def remove_shape(self, id):
        #shape = self._canvas.get_shape_by_id(id)
        area = self._canvas.get_shape_redraw_area(id)
        self._canvas.remove(id)
        self.redraw(area)
        
    def replace_shape(self, id, shape):
        old_area = self._canvas.get_shape_redraw_area(id)
        self._canvas.replace(id, shape)
        
        update_area = [self._canvas.get_shape_redraw_area(id)]
        if old_area: # jeigu tai buvo seniau istryntas, None objektas
            update_area.append(old_area)
        self.redraw(update_area)
        
        
    def move_shape(self, id, offset):
        old_area = self._canvas.get_shape_redraw_area(id)
        #print "old area: ", old_area
        #print "move offset: ", offset
        shape = self._canvas.get_shape_by_id(id)
        shape.move(self._canvas, offset)
        self._canvas.replace(id, shape)
        #new_id = self._canvas.add(shape)
        
        
        new_area = Area(old_area.x + offset[0], old_area.y + offset[1], old_area.width, old_area.height)
        #new_area = self._canvas.get_shape_redraw_area(new_id)
        #print "new area: ", new_area

        self.redraw([old_area, new_area])
        #print "move_shape", id, offset
        

      
class CopyScreen(Screen):
    """Experimentinis, pagal: http://www.mail-archive.com/gtk-app-devel-list@gnome.org/msg07601.html
    Pirmaji karta pasidarome ctx.surface kopija:
    self._surface_buffer = ctx.cairo_surface_create_similar()
    ir tada visada paisome jau tik i ta konteksta.
    Kai reikia perpaisyti, naudojame:
    ctx.set_source_surface(self._surface_buffer)
    
    Deja del cairo keisto funkcionavimo sita ideja neveikia - visada po zoominimo gaunamas isblurintas vaizdelis
    net jeigu vietoje create_similar, naudoju SVG - efektas tas pats...
    tiesiog Cairo scale() keicia tik tai kaip bus interpretuojamos i ji perdadamos koordinates bet ne pati vaizdeli
    (teoriskai su SVG, PDF  -tai turetu veikti - bet deja...)
    
    Tai yra bugas, kai vektorinis surface kopijuojamas i fiksuoto dyzdzio image surface:
    http://lists.freedesktop.org/archives/cairo/2011-March/021810.html
    
    """
    def __init__(self):
        super(CopyScreen,self).__init__()
        self._surface_buffer = None
        self._context = None
        self._zoom_level = 1
    
    def expose(self, ctx, area):
        if(self._surface_buffer == None):
            #self._surface_buffer = ctx.get_target().create_similar(cairo.CONTENT_COLOR_ALPHA, 4000, 6000)
            #self._surface_buffer = cairo.SVGSurface("xxx.svg", area.width, area.height)
            self._surface_buffer = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (0,0, area.width, area.height))
            self._context = cairo.Context(self._surface_buffer)
            super(CopyScreen,self).expose(self._context, area)
            print "first expose"
            
        print "next expose"
        ctx.save()
        if self._zoom_level != 1:
            print "scale context"
            ctx.scale(self._zoom_level, self._zoom_level)
            
        ctx.set_source_surface(self._surface_buffer)
        #/* To avoid getting the edge pixels blended with 0 alpha, which would 
        #     * occur with the default EXTEND_NONE. Use EXTEND_PAD for 1.2 or newer (2)
        #     */
        #cairo_pattern_set_extend (cairo_get_source(cr), CAIRO_EXTEND_REFLECT); 
        pat = ctx.get_source()
        #pat.set_filter(5)
        pat.set_extend(cairo.EXTEND_PAD)
        # Replace the destination with the source instead of overlaying 
        ctx.set_operator(cairo.OPERATOR_SOURCE)        
        
        
        ctx.paint()
        ctx.restore()
        self.draw_screen_overlays(ctx)
        
    def zoom(self, direction):
        #ctx.scale(ratio, ratio)
        if direction == -1:
            self._zoom_level = self._zoom_level / 2.0
        else:
            self._zoom_level = self._zoom_level * 2
        print "new zoom level: ", self._zoom_level
        self.redraw()

        
class DragScreen(Screen):
    """Perpaisome tik naujus po draginimo regionus"""
    #def __init__(self):
    #    super(DragScreen,self).__init__()

    def init(self):
        super(DragScreen,self).init()
        #print "init drag screen"
        self._redraw_regions = [] # regionai kuriuos reikia perpaisyti
        self._surface_buffer = None # draginant perpaisysime tik jo dali, o kita tik pastumsime!
        
    def clear_surface_buffer(self):
        self._surface_buffer = None
    
    def invalidate(self, area):
        self._redraw_regions.append(area)

    def draw_invalid_regions(self, surface):
        for region in self._redraw_regions:
            "draw_invalid_regions: ", region
            context = cairo.Context(surface)
            self._canvas.draw(context, region)
        self._redraw_regions = []
        
    def invalidate_drag_regions(self, area, offset):
        # virsus/apacia:
        if offset.y != 0: # ivyko poslinkis vertikalioje asyje
            width = area.width
            height = abs(offset.y)
            startx = starty = 0
            
            if offset.y < 0:
                starty = area.height - height
                
            self.invalidate(Area(startx, starty, width,  height))
        
        # sonas kairys/desinys:
        if offset.x !=0: # poslinkis horizontalioje asyje
            width = abs(offset.x)
            startx = 0
            starty = abs(offset.y)
            height = area.height - starty # cia height yra "virsaus" aukstis - kuri jau perpaisem
            
            #print "offset: ", self._offset.x, self._offset.y
            if offset.x < 0:
                startx = area.width - width
            if offset.y < 0:
                starty = 0

            self.invalidate(Area(startx, starty, width,  height))

    
    def update_surface_buffer(self, area, offset=Point(0, 0)):
        """update self._surface_buffer"""
        #self._surface_buffer = None
        if not self._surface_buffer:
            self._surface_buffer = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.width,  area.height)
            #self._surface_buffer = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (0,0, area.width, area.height))

            context = cairo.Context(self._surface_buffer)
            timer.start("expose full redraw")
            self._canvas.draw(context, area)
            timer.end("expose full redraw")
        else: # reikia paslinkti arba tiesiog perpaisyti is buferio
            #print "expose buffer"
            # nupaisome buferi (jeigu reikia su postumiu)
            merged_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.width, area.height)
            #merged_surface = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (0,0, area.width, area.height))
            merged_ctx = cairo.Context(merged_surface)

            merged_ctx.set_source_surface(self._surface_buffer, offset.x, offset.y)
            merged_ctx.paint()
            # pridejome sena padraginta gabala
            
            # dabar pridesime papildomus gabalus, jeigu atliktas dragas
            self.invalidate_drag_regions(area, offset) # paskaiciuojame ka reikia perpaisyti po draginimo virsuje/apacioje/sonuose
            self.draw_invalid_regions(merged_surface) # perpaisome viska, kas buvo irasyra i self._redraw_regions = []
            self._surface_buffer = merged_surface
        
            
    def expose(self, ctx, area):
        self.ctx = ctx # reikalingas control pointu draginimo testavimui in_context
        self._canvas.drag2(self._offset) #jeigu pradetas draginimas tai reikia pastumti ir canvas'a - darome tai cia kadangi kartais ivyksta keli "tusti" motion_notify

        #self._surface_buffer = None
        self.update_surface_buffer(area, self._offset)

        self._offset = Point(0, 0) # reikia cia nunulinti - kadangi kartais vyksta keli motion_notify()
    
        ctx.save()
        ctx.set_source_surface(self._surface_buffer)
        ctx.paint()
        ctx.restore()
        self.draw_screen_overlays(ctx)
    
    
    def resize(self, area):
        if self._device_area:
            if area.width > self._device_area.width:
                self.invalidate(Area(self._device_area.width, 0, area.width - self._device_area.width,  self._device_area.height))
                #print "update rigth side!"
            if area.height > self._device_area.height:
                self.invalidate(Area(0, self._device_area.height, area.width,  area.height-self._device_area.height))
                #print "update bottom side!"
                
        self._device_area = area
        self._canvas.set_device_area(area)

        
    def redraw(self, regions=False):
        if regions:
            if not isinstance(regions, list): regions = [regions]
            for area in regions:
                self.invalidate(area) # perpaisysime sita regiona
        else:
            self.clear_surface_buffer() # perpaisysime viska

        self.ui_redraw()
        

        
class BufferScreen(DragScreen):
    """Buferis kuris leidzia laisvai draginti 3x3 dydzio paveiksliuka neiskvieciant draw (jis iskvieciamas tik drag_end metu)
    """
    #def __init__(self):
    #    super(BufferScreen,self).__init__()
    
    def init(self):
        """ atskiras init, tam kad butu galima atskirai is naujo inicializuoti clear() metu"""
        super(BufferScreen,self).init()
        #print "init buffer screen"
        self._buffer_offset = Point(0,0) # buferio poslinkis draginimo metu
        self._zoom = False # expose vykdomas po zoom paspaudimo 
        
        
    def drag_start(self, point):
        super(BufferScreen,self).drag_start(point)
        self._buffer_offset = Point(0,0)
        
        #self._offset = Point(0, 0)
    def drag_end(self, point):
        super(BufferScreen,self).drag_end(point)
        #self._canvas.drag2(self._buffer_offset) # cia draginti negerai, nes paisomi objektai naudojasi user koordinatemis
        self.paint_buffer()
        self._buffer_offset = Point(0,0)

        
    def paint_buffer(self, zoom=0):
        """zoom:0, tai atliekam iprasta perpaisyma (zoom nebuvo paspaustas)
            zoom:1 - pradinis perpaisymas po zoom paspaudimo, nupaisome tik vartotojui matoma dali
            zoom:2 - perpaisymas po expose ivykdymo, dapaisome likusia buferio dali
        """
        #print "paint_buffer :", zoom
        self.ui_set_cursor("wait_arrow")
        area = self._device_area
        self._canvas.drag2(Point(area.width, area.height)) #pastumiam canvas, kuri paskui atstumsime atgal
        if not zoom:
            #timer.start("update 3x3")
            #self._surface_buffer = None - pilnai perpiesti draginimo metu apsimoka tik kartais, kai zoomlevelis pats maziausias - nes tada
            # ta pati figura patenka tiek i kaire tiek ir i desine drago puse ir yra perpaisoma du kartus
            self.update_surface_buffer(Area(0, 0, area.width*3, area.height*3),  self._buffer_offset)
            #timer.end("update 3x3")
        elif zoom == 1: # perpaisome po zoom paspaudimo virsutine kaire dali
            #self._surface_buffer = None
            timer.start("update 2x2")
            self.update_surface_buffer(Area(0, 0, area.width*2, area.height*2)) 
            timer.end("update 2x2")
            self._zoom = True # po expose 
        elif zoom == 2: # perpaisysime likusia dali
            timer.start("update invalid")
            self.invalidate(Area(area.width*2, 0, area.width, area.height*2)) # invaliduojame buferio desini sona
            self.invalidate(Area(0, area.height*2, area.width*3, area.height)) # invaliduojame buferio apacia
            self.update_surface_buffer(Area(0, 0, area.width*3, area.height*3))
            timer.end("update invalid")
            self._zoom = False

        self._canvas.drag2(Point(-area.width, -area.height))
        self.ui_reset_cursor()
            

    
    def redraw(self, regions=False, zoom=0):
        if regions:
            if not isinstance(regions, list): regions = [regions]
            for area in regions:
                buffer_area = Area(self._device_area.width + area.x, self._device_area.height + area.y, area.width, area.height)
                self.invalidate(buffer_area) # perpaisysime sita regiona
        else:
            self.clear_surface_buffer() # perpaisysime viska

        self.paint_buffer(zoom)
        
        self.ui_redraw()
        
    def zoom(self, direction):
        if self._canvas.zoom(direction):
            self.redraw(zoom=1)
        
    def resize(self, area):
        """Resizeinant tenka dapaisineti buferi visomis kryptimis,
         kaireje ir virsuje invaliduos invalidate_drag_regions(), update_surface metu
         desineje ir apacioje reikia invaliduoti cia"""
        x, y = 0, 0
        if self._device_area:
            x = area.width - self._device_area.width
            y = area.height-self._device_area.height
            if x > 0:
                # reikia invaliduoti desineje
                y_drag = (y>0 and y or 0)
                self.invalidate(Area(area.width*3-2*x, y_drag, 2*x, area.height*3-y_drag))
                #print "update rigth side!"
            if y > 0:
                # reikia invaliduoti apacioje
                x_drag = (x>0 and x or 0)
                self.invalidate(Area(x_drag, area.height*3-2*y, area.width*3-x_drag, 2*y))
                #print "update bottom side!"
            # kaireje ir virsuje invaliduos invalidate_drag_regions(), update_surface metu
            
        self._buffer_offset = Point(x, y) # perstumsime sena buferi
        #print "resize offset: ", self._buffer_offset
        self._device_area = area
        self._canvas.set_device_area(area)
        self.paint_buffer()
        self._buffer_offset = Point(0, 0)

        
    def expose(self, ctx, area):
        #print "buffer screen sxpose!"
        #timer.start("buffer expose")
        self.ctx = ctx # reikalingas control pointu draginimo testavimui in_context
        self._canvas.drag2(self._offset)      
        
        ctx.save()
        self._buffer_offset = Point(self._buffer_offset.x + self._offset.x, self._buffer_offset.y + self._offset.y)
        ctx.set_source_surface(self._surface_buffer, -area.width+self._buffer_offset.x, -area.height+self._buffer_offset.y)
        self._offset = Point(0, 0) # reikia cia nunulinti - kadangi kartais vyksta keli motion_notify()
        ctx.paint()
        ctx.restore()
        self.draw_screen_overlays(ctx)
        
        if self._zoom:
            self.ui_timeout(10, self.update_buffer_after_zoom)
        #timer.end("buffer expose")
        
        
    def update_buffer_after_zoom(self):
        self.paint_buffer(zoom=2)
        return False

        
class GisGTK2Screen(BufferScreen):
    def __init__(self, draw_area):
        super(GisGTK2Screen,self).__init__()
        self.draw_area = draw_area
        self._cursor = None
        self._previous_cursor = None

    def ui_redraw(self):
        self.draw_area.queue_draw()

    def ui_timeout(self, time, callback):
        gobject.timeout_add(time, callback)

    def ui_reset_cursor(self):
        """Return to previous cursor"""
        self.ui_set_cursor(self._previous_cursor)
        
    def ui_set_cursor(self, cursor_name=None):
        if cursor_name == self._cursor: return

        #print "ui_set_cursor: ", cursor_name
        cursor = None
        if cursor_name == "wait_arrow":
            if self._cursor == "cross":
                cursor = WAIT_CROSS
            else:
                cursor = WAIT_ARROW
        elif cursor_name ==  "wait":
            cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
        elif cursor_name ==  "cross":
            cursor = gtk.gdk.Cursor(gtk.gdk.TCROSS)
            
        self.draw_area.window.set_cursor(cursor)
        self._previous_cursor = self._cursor
        self._cursor = cursor_name
    
    def ui_open_file(self): # dialog
        from Tkinter import Tk
        import tkFileDialog
 
        master = Tk()
        master.withdraw() #hiding tkinter window
        file_path = tkFileDialog.askopenfilename(title="Open file", filetypes=[("All files",".*"), ("shape file",".shp"), ("ocad file",".ocd")])
        master.destroy()
        
        if file_path != "":
            self.open_file(str(file_path))
            
        """
        d = gtk.FileChooserDialog(title="Select a file", parent=self.main_window, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=("OK",True,"Cancel",False))
        ok = d.run()        
        if ok:
            file_path = d.get_filename()
            self.canvas.load_shapefile(file_path)
            print "filename: ", file_path
        d.destroy() 
        """
        
class SceenOverlay(object):
    # places for screen overlays
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4
    CENTER = 5

    def __init__(self, corner=1, offset=(0,0)):
        self._corner = corner
        self._offset = Point(offset[0], offset[1])
        #self._width = width
        #self._height = height
        
        
    # graziname vieta kur reikia patalpinti sita 
    def get_xy(self, area):
        x, y = area.x + self._offset.x, area.y + self._offset.y # TOP_LEFT
        if self._corner == SceenOverlay.TOP_RIGHT:
            x = x + area.width
        elif self._corner == SceenOverlay.BOTTOM_LEFT:
            y = y + area.height
        elif self._corner == SceenOverlay.BOTTOM_RIGHT:
            x , y = x + area.width, y + area.height
        elif self._corner ==  SceenOverlay.CENTER:
            x, y = x + (area.width/2), y + (area.height/2)
        return Point(x, y)
 
    # every sublass must implement:
    def draw(self, ctx, screen):
        pass 


class ScreenSelectedObject(SceenOverlay):
    def __init__(self, shape_id=None, corner=1, offset=(0,0)):
        super(ScreenSelectedObject,self).__init__(corner, offset)
        #self._handles = handles
        self._shape_id = shape_id

    def draw(self, ctx, screen):
        shape = screen.get_canvas().get_shape_by_id(self._shape_id)
        if shape:
            shape.draw_handlers(ctx, screen.get_canvas(), offset=self._offset)
        
        """
        if not len(self._handles): return
        
        canvas = screen.get_canvas()
        handles = [canvas.user_to_device(point) for point in self._handles]
        
        for point in handles:
            draw_point(ctx, point.x, point.y, 0.5)
        """



        
class ScreenLine(SceenOverlay):
    def __init__(self, line=[], corner=1, offset=(0,0)):
        super(ScreenLine,self).__init__(corner, offset)
        self._line = line
 
    def draw(self, ctx, screen):
        if not len(self._line): return
        
        canvas = screen.get_canvas()
        line = [canvas.user_to_device(point) for point in self._line]

        ctx.save()
        ctx.set_line_width(1.0)
        #ctx.set_dash([2, 2], 0)
        ctx.set_source_rgb(0, 0, 0)
        
        ctx.move_to(line[0].x+0.5, line[0].y+0.5)
        for i in xrange(1, len(line)):
            x, y = line[i].x+0.5, line[i].y+0.5
            ctx.line_to(x, y)
            #draw_point(ctx, x, y, 0.5)

        ctx.stroke()
        draw_point(ctx, line[-1].x, line[-1].y, 0.5)
            
        ctx.restore()
    

    
class ScreenCurve(SceenOverlay):
    def __init__(self, curve=[], active_controls=2, corner=1, offset=(0,0)):
        super(ScreenCurve,self).__init__(corner, offset)
        self._curve = curve
        self._active_controls = active_controls # number of active (control) points from the end of the line

    def to_device(self, canvas):
        device_curve = []
        for point in self._curve:
            c1 = canvas.user_to_device(point[0])
            xy = canvas.user_to_device(point[1])
            c2 = canvas.user_to_device(point[2])
            device_curve.append((c1.x, c1.y, xy.x, xy.y, c2.x, c2.y))
        return device_curve
        
 
    def draw(self, ctx, screen):
        if not len(self._curve): return
        
        curve = self.to_device(screen.get_canvas())
        
        ctx.save()

        ctx.set_line_width(1)
        debug_points(ctx, curve[-self._active_controls:])
        ctx.set_line_width(1.5)
        poly_curve(ctx, curve)
        ctx.set_source_rgb(0, 0, 0)

        ctx.stroke()
        ctx.restore()
    

class ScreenText(SceenOverlay):
    def __init__(self, text, corner=1, offset=(0,0)):
        super(ScreenText,self).__init__(corner, offset)
        self._text = text

    def draw(self, ctx, screen):
        # draw text
        ctx.select_font_face('Sans')
        ctx.set_font_size(10) # em-square height is 90 pixels
        
        start = self.get_xy(screen.get_area())
        #print "draw: ", start
        ctx.move_to(start.x, start.y) # move to point (x, y) = (10, 90)
        ctx.set_source_rgb(0, 0, 0) # yellow
        ctx.show_text(self._text)
        ctx.stroke()

        
class ScreenCrosshair(SceenOverlay):
    def draw(self, ctx, screen):
        # draw text
        width = 13
        start = self.get_xy(screen.get_area())
        #print "draw: ", start
        ctx.set_line_width(1.0)
        ctx.set_source_rgba(0, 0, 0, 0.5)
        x = start.x + 1
        ctx.move_to(x-(width+1)/2, start.y+0.5)
        ctx.line_to(x+(width-1)/2, start.y+0.5)
        ctx.move_to(x-0.5, start.y-(width-1)/2)
        ctx.line_to(x-0.5, start.y+(width+1)/2)
        ctx.set_line_width(1)
        #print "line width: ", ctx.get_line_width() 
        ctx.stroke()
    
