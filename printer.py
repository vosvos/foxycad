from screen import SceenOverlay
from utils import Area, Point
import cairo

class Printer():
    def __init__(self, screen):
        self._screen = screen
        self._formats = {"A4":(210,297)} 
        self._preview_overlay_id = None # id pagal kuri galima pashalinti rodoma staciakampi
        #self._page_area = None # preview staciakampis ekrane
        self._preview_overlay = None # pats staciakampis
        
        self._inch_in_mm = 25.4
        

    def get_page_size_in_points(self, format, orientation, dpi):
        """print "mums reikia scalinti contexta, kad jis butu tokio dydzio: ", page_size
            priklausomai nuo puslapio formato, dpi ir orientation paskaiciuojame kiek tasku 
            mums reikia isvesti, kad uzpildyti lapa. Pagal tai reikes scalinti contexta"""
        size = self._formats.get(format)
        if orientation == 1: #landscape
            size = (size[1], size[0])
    
        return (size[0] / self._inch_in_mm * dpi, size[1] / self._inch_in_mm * dpi)

        
    def get_screen_area(self): 
        """screen area in print rectangle"""
        area = self._screen.get_area()
        center = self._preview_overlay.get_xy(area)
        width, height = self._preview_overlay.get_size()
        
        return  Area(center.x-width/2, center.y-height/2, width, height) # resizeinus langa - ji pasikeicia (centras) - todel reikia perskaiciuoti visada!

        
    def get_canvas_area(self): # grazina canvaso staciakampi kuri norime atspausdinti
        # reikia paskaiciuoti....
        if not self._preview_overlay: return None
        
        canvas = self._screen.get_canvas()
        page_area = self.get_screen_area() #_page_area
        
        x_left, y_left = canvas.device_to_user(Point(page_area.x, page_area.y))
        x_right, y_right = canvas.device_to_user(Point(page_area.x+page_area.width, page_area.y))
        x_bottom, y_bottom = canvas.device_to_user(Point(page_area.x, page_area.y + page_area.height))
        
        return Area(x_left, y_left, int(x_right-x_left), int(y_bottom - y_left))

        
    def print_to_png(self):
        user_area = self.get_canvas_area()
        print "User area:", user_area
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, user_area.width, user_area.height)
        ctx = cairo.Context (surface)
        self._screen.get_canvas().draw_100(ctx, user_area)
        surface.write_to_png("print.png")
        
        
    def print_screen(self, ctx):
        self._screen.get_canvas().draw(ctx, self._screen.get_area())

        
    def print_page(self, ctx, format="A4", orientation=0, dpi=96):
        #self.print_to_png()
    
        print "Printer settings: ", format, orientation, dpi
        if not self._preview_overlay:
            print "Printing current screen..."
            self.print_screen(ctx)
        else:
            print "Printing data in preview rectangle..."
            page_size = self.get_page_size_in_points(format, orientation, dpi)
            print "Page_size with dpi: ", page_size
            canvas_area = self.get_canvas_area()
            print "Canvas area: ", canvas_area
            
            ratio = page_size[1] / canvas_area.height # paskaiciuojame kiek reikia scalinti canvasa, kad jis uzpildyti A4 lapa
            print "Ratio: ", ratio
            
            
            ctx.scale(ratio, ratio)

            self._screen.get_canvas().draw_100(ctx, canvas_area)

        
    def preview(self, format, orientation=None):
        # 0 - portrait, 1 - landscape
        #canvas = self._screen.get_canvas()
        #ctx.rectangle(area.x, area.y, area.width, area.height) 
        #print "preview in fomat: ", format, self._formats.get(format), orientation

        if orientation == None:
            if self._preview_overlay_id and self._preview_overlay:
                self._screen.remove(self._preview_overlay_id)
                self._preview_overlay = None
            return

        area = self._screen.get_area()
        size = self._formats.get(format)
        
        if not size:
            raise NameError("Page size format %s not implemented!" % format)
        
        if orientation:
            size = (size[1], size[0])
            
        height = area.height - 20
        width = size[0] * height / size[1]
        if width > area.width - 20:
             width = area.width - 20
             height = width * size[1] / size[0]
            
        self._preview_overlay  = ScreenPrintPreview(width, height, SceenOverlay.CENTER)
        if self._preview_overlay_id:
            self._screen.replace(self._preview_overlay_id, self._preview_overlay) # nekuriam naujo
        else:
            self._preview_overlay_id = self._screen.add(self._preview_overlay)
        


        
class ScreenPrintPreview(SceenOverlay):
    def __init__(self, width, height, corner=1, offset=(0,0)):
        super(ScreenPrintPreview,self).__init__(corner, offset)
        self._width = width
        self._height = height

    def get_size(self):
        return (self._width, self._height)
     
    def draw(self, ctx, screen):
        # draw text
        center = self.get_xy(screen.get_area())
        #print "draw: ", start
        #ctx.move_to(start.x, start.y) # move to point (x, y) = (10, 90)
        ctx.set_source_rgb(0, 0, 0) # yellow
        ctx.rectangle(center.x-self._width/2, center.y-self._height/2, self._width, self._height) 
        ctx.stroke()

    
    
