from utils import timer, Point, Event
from screen import GisGTK2Screen, SceenOverlay, ScreenText, ScreenCrosshair
from tools import Tools
from printer import Printer
from history import Invoker, Command

import time 
import gtk, gobject

class DrawingInterface:
    """
    The GTK interface to the drawing.
    
    This class creates a GTK window, adds a drawing area to it and handles
    GTK's destroy and expose events in order to close the application and
    re-draw the area using Cairo.
    """
    def __init__(self, area):
        self._load_shape_on_init = None #"shapefiles/lt/keliai.shp"

        self._print_orientation = 1 # landscape
        self._print_settings = gtk.PrintSettings()
        try:
            self._print_settings.load_file("printer.settings")
        except:
            pass
        
        self.main_window = gtk.Window()
        
        vbox = gtk.VBox(False, 0)
        self.main_window.add(vbox)
        self.main_window.set_size_request(area.width, area.height)
        vbox.show()
        
        self.main_window.connect("destroy", self.destroy_event)

        self.draw_area = gtk.DrawingArea()
        #self.draw_area.set_size_request(200, 200)
        
        hbox = gtk.HBox(False, 1)
        vbox.pack_start(hbox, True, True, 0)
        hbox.pack_start(self.draw_area, True, True, 0)
        hbox.show()
        self.draw_area.show()
    
        self.draw_area.connect("expose-event", self.expose_event)
        self.draw_area.connect("configure_event", self.configure_event)

        # Event signals
        # http://www.pygtk.org/pygtk2tutorial/sec-EventHandling.html
        self.draw_area.connect("motion_notify_event", self.motion_notify_event)
        self.draw_area.connect("button_press_event", self.button_press_event)
        
        self.draw_area.connect("button_release_event", self.button_release_event)
        
        
        self.main_window.connect("key_press_event", self.key_press_event)

        #self.main_window.connect("leave_notify_event", self.leave_notify_event)
        #self.main_window.connect("enter_notify_event", self.leave_notify_event)
        #self.main_window.set_events(gtk.gdk.LEAVE_NOTIFY_MASK)
        
        self.draw_area.set_events(gtk.gdk.EXPOSURE_MASK
                            | gtk.gdk.BUTTON_PRESS_MASK
                            | gtk.gdk.BUTTON_RELEASE_MASK
                            | gtk.gdk.BUTTON3_MOTION_MASK 
                            | gtk.gdk.POINTER_MOTION_MASK
                            | gtk.gdk.POINTER_MOTION_HINT_MASK
                            #| gtk.gdk.ENTER_NOTIFY_MASK
                            #| gtk.gdk.LEAVE_NOTIFY_MASK
                            #| gtk.gdk.KEY_PRESS_MASK
                            )
                            
        vbox_toolbar = gtk.VBox(False, 1)
        vbox_toolbar.set_size_request(100, 0)
        hbox.pack_start(vbox_toolbar, False, False, 0)
        vbox_toolbar.show()

        zoom_in_button = gtk.Button("ZoomIn")
        vbox_toolbar.pack_start(zoom_in_button, False, False, 0)
        zoom_in_button.connect_object("clicked", self.zoom, 1)
        zoom_in_button.show()

        zoom_out_button = gtk.Button("ZoomOut")
        vbox_toolbar.pack_start(zoom_out_button, False, False, 0)
        zoom_out_button.connect_object("clicked", self.zoom, -1)
        zoom_out_button.show()

        center_button = gtk.Button("Center")
        vbox_toolbar.pack_start(center_button, False, False, 0)
        center_button.connect_object("clicked", self.center, None)
        center_button.show()

        valign0 = gtk.Alignment(0, 1, 0, 0)
        vbox_toolbar.pack_start(valign0)
        valign0.show()

        Invoker.set_button_event("enable", lambda button: button.set_sensitive(1))
        Invoker.set_button_event("disable", lambda button: button.set_sensitive(0))

        undo_button = gtk.Button("Undo")
        Invoker.set_button("undo", undo_button, disable=True)
        vbox_toolbar.pack_start(undo_button, False, False, 0)
        undo_button.connect_object("clicked", self.undo, None)
        undo_button.show()

        redo_button = gtk.Button("Redo")
        Invoker.set_button("redo", redo_button, disable=True)
        vbox_toolbar.pack_start(redo_button, False, False, 0)
        redo_button.connect_object("clicked", self.redo, None)
        redo_button.show()

        #Invoker.execute(Command(1))
        #Invoker.execute(Command(2))
        
        valign1 = gtk.Alignment(0, 1, 0, 0)
        vbox_toolbar.pack_start(valign1)
        valign1.show()
        
        detect_point_button = gtk.Button("Detect Point")
        vbox_toolbar.pack_start(detect_point_button, False, False, 0)
        detect_point_button.connect_object("clicked", self.set_tool, "detect_point")
        detect_point_button.show()

        select_object_button = gtk.Button("Move Shape")
        vbox_toolbar.pack_start(select_object_button, False, False, 0)
        select_object_button.connect_object("clicked", self.set_tool, "move_shape")
        select_object_button.show()
        
        valign2 = gtk.Alignment(0, 1, 0, 0)
        vbox_toolbar.pack_start(valign2)
        valign2.show()

        add_point_button = gtk.Button("Add Point")
        vbox_toolbar.pack_start(add_point_button, False, False, 0)
        add_point_button.connect_object("clicked", self.set_tool, "add_point")
        add_point_button.show()

        add_line_button = gtk.Button("Add Line")
        vbox_toolbar.pack_start(add_line_button, False, False, 0)
        add_line_button.connect_object("clicked", self.set_tool, "add_line")
        add_line_button.show()

        add_curve_button = gtk.Button("Add Curve")
        vbox_toolbar.pack_start(add_curve_button, False, False, 0)
        add_curve_button.connect_object("clicked", self.set_tool, "add_curve")
        add_curve_button.show()

        valign_line = gtk.Alignment(0, 1, 0, 0)
        vbox_toolbar.pack_start(valign_line)
        valign_line.show()
        
        load_file_button = gtk.Button("Load File")
        vbox_toolbar.pack_start(load_file_button, False, False, 0)
        #load_file_button.connect_object("clicked", self.load_file, "shapefiles/lt/gyvenvie.shp")
        #load_file_button.connect_object("clicked", self.load_file, "shapefiles/lt/reljefas.shp")
        #load_file_button.connect_object("clicked", self.load_file, "shapefiles/lt/keliai.shp")
        load_file_button.connect_object("clicked", self.load_file, "")
        #load_file_button.connect_object("clicked", self.load_file, "shapefiles/iceland/cultural_landmark-point.shp")
        load_file_button.show()

        clear_button = gtk.Button("Clear")
        vbox_toolbar.pack_start(clear_button, False, False, 0)
        clear_button.connect_object("clicked", self.clear, None)
        clear_button.show()

        save_button = gtk.Button("Save")
        vbox_toolbar.pack_start(save_button, False, False, 0)
        save_button.connect_object("clicked", self.save, "dump")
        save_button.show()
        
        redraw_button = gtk.Button("Redraw")
        vbox_toolbar.pack_start(redraw_button, False, False, 0)
        redraw_button.connect_object("clicked", self.redraw, "")
        redraw_button.show()

        valign3 = gtk.Alignment(0, 1, 0, 0)
        vbox_toolbar.pack_start(valign3)
        valign3.show()

        print_preview = gtk.Button("Preview A4")
        vbox_toolbar.pack_start(print_preview, False, False, 0)
        print_preview.connect_object("clicked", self.print_preview, "A4")
        print_preview.show()

        print_button = gtk.Button("Print")
        vbox_toolbar.pack_start(print_button, False, False, 0)
        print_button.connect_object("clicked", self.print_dialog, "")
        print_button.show()
        
        self.status_bar = gtk.Statusbar()
        self._status = "Ready"
        self.status_bar.push(1, self._status)
        vbox.pack_start(self.status_bar, False, False, 0)
        self.status_bar.show()
        #self.main_window.add(self.draw_area)
        #self.main_window.set_size_request(area.width, area.height)
        self.screen = GisGTK2Screen(self.draw_area)
        self.screen.add(ScreenText("@ FoxyCAD", SceenOverlay.BOTTOM_RIGHT, (-60, -5)))
        self.screen.add(ScreenCrosshair(SceenOverlay.CENTER))
        
        self.tools = Tools(self.screen) # tools dirbs tik su ekrano koordinatemis
        self.printer = Printer(self.screen) # viskas kas susije su paruosimu spausdinimui
        
        # As durnas, o mano vartotojai dar durnesni, todel viskas turi buti maximaliai aisku ir paprasta
        #self.canvas.setCoordinateCenter(("WGS", 54.7892, 24.7852)) # ten padesime kyziuka
        #self.canvas.setUnit("meters", 1) # rodysime liniuotes kastuose metrus
        #   @----10m----->@ su pelia traukiojma ir matom atstuma metrais
        
        #self.canvas.add_random_points(10000, gtk.gdk.Rectangle(0, 0, 6800, 4000))
        #self.canvas.add_random_points(100000, gtk.gdk.Rectangle(0, 0, 12000, 8000), generator=True) 
        self.main_window.show()   #show_all()
        

    
    def status(self, text):
        self._status = text #"Device: (%i, %i) User: (%i, %i) Map: (%f, %f) " % (point.x, point.y, user.x, user.y, map.x, map.y)
        self.status_bar.remove_all(1)
        self.status_bar.push(1, self._status)
    
    def destroy_event(self, widget):
        gtk.main_quit()

    
    def set_tool(self, tool_name):
        self.tools.run(tool_name)

    def save(self, file_name="dump"):
        self.screen.get_canvas().save(file_name)

    def clear(self, file_path=None):
        self.tools.remove() # stop active
        self.screen.clear()
        self.screen.redraw()
        
    def center(self, point):
        self.screen.get_canvas().center(point)
        self.screen.redraw()
        
    def load_file(self, file_path=None):
        if file_path:
            self.screen.open_file(file_path)
        else:
            self.screen.ui_open_file()
            
    def undo(self, arg):
        Invoker.undo()
        #print "ui undo"
            
    def redo(self, arg):
        Invoker.redo()
        #print "ui redo"

    def redraw(self, fakearg):
        self.screen.redraw()
        
    def print_preview(self, format="A4"):
        #print "preview draggable A4 rectangle"
        self.printer.preview(format, self._print_orientation)
        
        if self._print_orientation == 1:
            self._print_settings.set_orientation(gtk.PAGE_ORIENTATION_LANDSCAPE)
            self._print_orientation = 0
        elif self._print_orientation == 0:
            self._print_settings.set_orientation(gtk.PAGE_ORIENTATION_PORTRAIT)
            self._print_orientation = None
        else:
            self._print_orientation = 1
        
            

    def print_dialog(self, fakearg):
        self._print_operation = gtk.PrintOperation()
        self._print_operation.set_print_settings(self._print_settings)
        self._print_operation.set_n_pages(1)
        
        page_setup = gtk.PageSetup()
        page_setup.set_orientation(self._print_settings.get_orientation())
        page_setup.set_left_margin(0, gtk.UNIT_INCH)
        page_setup.set_top_margin(0, gtk.UNIT_INCH)
        self._print_operation.set_default_page_setup(page_setup)
        
        self._print_operation.connect("draw_page", self.print_graphics)

        res = self._print_operation.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, self.main_window)
        
        if res == gtk.PRINT_OPERATION_RESULT_ERROR:
            error_dialog = gtk.MessageDialog(self.main_window, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, "Error printing file:\n")
            error_dialog.connect("response", lambda w,id: w.destroy())
            error_dialog.show()
        elif res == gtk.PRINT_OPERATION_RESULT_APPLY:
            self._print_settings = self._print_operation.get_print_settings()
            self._print_settings.to_file("printer.settings")
        
        #page_setup = print_op.get_default_page_setup()
        #if page_setup:
        #    print "page setup: ", page_setup.get_paper_size(),  page_setup.get_left_margin(gtk.UNIT_PIXEL)

        
    def print_text(self, operation=None, context=None, page_nr=None):
        self.pangolayout = context.create_pango_layout()
        self.format_text()
        cairo_context = context.get_cairo_context()
        cairo_context.show_layout(self.pangolayout)
        return

        
    def print_graphics(self, operation=None, context=None, page_nr=None):
        cairo_context = context.get_cairo_context()
        
        orientation = 0
        if self._print_orientation == 0: 
            orientation = 1 # nes jau busime pakeite...
        
        dpi = self._print_operation.get_print_settings().get("win32-print-quality")
        self.printer.print_page(cairo_context, "A4", orientation, int(dpi))
        return

        
    def format_text(self):
        self.pangolayout.set_text(unicode("""
            Dies ist ein Text-Test. Er funktioniert gut und zeigt, dass auch PyGTK
            das drucken kann, was man auf eine DrawingArea geschrieben hat.
            Anwendungen dafibt es genug! 
            """, "latin-1"))
        
    def configure_event(self, widget, event):
        area = widget.get_allocation()
        self.screen.resize(area)
        



    def expose_event(self, widget, event):
        #timer.start("expose_event")

        area = widget.get_allocation()
        ctx = widget.window.cairo_create()
        self.screen.expose(ctx, area)

        #timer.end("expose_event")
        
        if self._load_shape_on_init:
            self.screen.open_file(self._load_shape_on_init)
            self._load_shape_on_init = False

        return False

        
    def key_press_event(self, widget, event):
    
        keyname = gtk.gdk.keyval_name(event.keyval).lower()
        if keyname == "c" and event.state & gtk.gdk.CONTROL_MASK:
            print "copy status to clipboard!"
            from Tkinter import Tk
            r = Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(self._status)
            r.destroy()
        #print "Key %s (%d) was pressed" % (keyname, event.keyval)

        
    def button_press_event(self, widget, event):
        print "button_press_event", event.button, event.x, event.y
        point = Point(event.x, event.y)

        if event.button == 1:
            status = self.tools.press(point)
            if status:
                 self.status(status)
        
        if event.button == 3:
            self.screen.drag_start(point)
            
        self._drag_start = True # jeigu draginimo metu pele yra atleidizama uz ekrano ribu, tai nera gaunamas button_release_event
        gobject.timeout_add(100, self.mouse_leave_test, widget, event.button) # todel as ji cia simuliuoju (Tai aktualu BufferScreenui, kadangi jis perpaiso on_drag_end)
    

    def mouse_leave_test(self, widget, button):
        area = widget.get_allocation()
        x, y = self.main_window.get_pointer()
        
        if x < area.x or y < area.y or x > area.width or y > area.height:
            if x < area.x: x = 0
            if x > area.width: x = area.width
            if y < area.y: y = 0
            if y > area.height: y = area.height
            event = Event(x, y, button) # fake event
            self.button_release_event(widget, event)
            return False
        elif not self._drag_start:
            return False
        return True

        
    def leave_notify_event(self, widget, event):
        print "leave: ", event.x, event.y
    
    def button_release_event(self, widget, event):
        print "button_release_event", event.button, event.x, event.y
        area = widget.get_allocation()
        point = Point(min(event.x, area.width), min(event.y, area.height))

        self._drag_start = False
        if event.button == 3:
            self.screen.drag_end(point)
        elif event.button == 1:
            status = self.tools.release(point)
            if status:
                 self.status(status)
            
            
    def motion_notify_event(self, widget, event):
        #print "motion_notify_event", event
        area = widget.get_allocation()
        point = Point(min(event.x, area.width), min(event.y, area.height))
        #point = Point(event.x, event.y)
        
        if event.state & gtk.gdk.BUTTON3_MASK: # nuspaustas desinys mygtukas
            self.screen.drag(point)
        elif event.state & gtk.gdk.BUTTON1_MASK: # nuspaustas kairys mygtukas
            self.tools.drag(point)
        else:
            status = self.screen.mouse_move(point)
            if status:
                self.status(status)
            
            self.tools.move(point)
            #self.draw_area.queue_draw_area(0, 0, 200, 200)


    def zoom(self, direction):
        cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
        self.main_window.window.set_cursor(cursor)
        self.screen.zoom(direction)
        self.main_window.window.set_cursor(None)

      
def main():
    area = gtk.gdk.Rectangle(0, 0, 600, 500)
    DrawingInterface(area)
    gtk.main()
    #profile.run('gtk.main()')
