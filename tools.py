from screen import SceenOverlay, ScreenLine, ScreenCurve, ScreenSelectedObject
from fshape import Shape
from vec2d import Vec2d
from utils import Point, timer
from history import Invoker

import geometry

class Tools:
    def __init__(self, screen):
        self.screen = screen
        #self.drawing_interface = drawing_interface
        
        self._factory = {"add_point": AddPointTool, 
                                "detect_point": DetectPointTool, 
                                "add_line": AddLineTool, 
                                "add_curve": AddCurveTool,
                                "move_shape": MoveShapeTool
                                }
        self._tools = {} #toolsu egzemplioriai. sukursime, kai pirma karta paspaus
        self._active_tool = None

    def is_active(self, tool_name):
        return self._active_tool == tool_name
        
    def run(self, tool_name):
        if self.is_active(tool_name): return 
        
        self.remove() #remove active

        tool = self._tools.get(tool_name)
        
        if not tool:
            tool = self.create(tool_name)
            self._tools[tool_name] = tool
            
        self._active_tool = tool_name
        tool.run(self.screen)
    
    def create(self, tool_name):
        return self._factory[tool_name]()
        
    def press(self, point):
        if self._active_tool:
            tool = self._tools.get(self._active_tool)
            return tool.press(self.screen, point)

    def drag(self, point):
        if self._active_tool:
            tool = self._tools.get(self._active_tool)
            return tool.drag(self.screen, point)

    def move(self, point):
        if self._active_tool:
            tool = self._tools.get(self._active_tool)
            return tool.move(self.screen, point)

    def release(self, point):
        if self._active_tool:
            tool = self._tools.get(self._active_tool)
            return tool.release(self.screen, point)
            
    def remove(self):
        if self._active_tool:
            self._tools[self._active_tool].stop(self.screen)
            self._active_tool = None


class Tool:
    def run(self, screen):
        pass
        #print "Tool run..."

    def stop(self, screen):
        pass
        #print "Tool stop..."

    def drag(self, screen, point):
        pass

    def move(self, screen, point):
        pass
     
    def release(self, screen, point):
        pass

    def press(self, screen, point):
        pass
        #print "Tool press...", canvas, widget, event
    
        
class MoveShapeCommand:
    def __init__(self, tool, screen, shape_id, offset):
        self._tool = tool
        self._screen = screen
        self._shape_id = shape_id
        self._offset = offset
     
    def execute(self):
        self._screen.move_shape(self._shape_id, self._offset)
        self._tool.show_handlers(self._screen, ScreenSelectedObject(self._shape_id))
        return True
    
    def undo(self):
        self._screen.move_shape(self._shape_id, (-self._offset[0], -self._offset[1])) # move back
        self._tool.show_handlers(self._screen, ScreenSelectedObject(self._shape_id))
        self._tool.select_shape(self._shape_id) # tam kad galetume ja iskarto draginti

        
class MoveShapeTool(Tool):
    def __init__(self):
        self._handlers_overlay_id = None
        self.clear(None)

    def show_handlers(self, screen, handlers_overlay):
        if self._handlers_overlay_id != None:
            screen.replace(self._handlers_overlay_id, handlers_overlay)
        else:
            self._handlers_overlay_id = screen.add(handlers_overlay)

    def clear(self, screen): # tai nera Tool iskvieciamas metodas
        self._selected_objects = None
        self._object_index = None
        self._handlers = []
        self._drag_object_id = None
        
        if self._handlers_overlay_id != None:
            screen.remove(self._handlers_overlay_id)
            self._handlers_overlay_id = None
            
        self._drag_object_id = None # start dragging object
        self._drag_object_point = None # start of the dragging

        
    def stop(self, screen):
        # reikia kursoriu atstatyti pries tai buvusi
        self.clear(screen)
            
    def drag(self, screen, point):
        upoint = screen.get_canvas().device_to_user(point)
        
        if self._drag_object_id:
            offset = (point.x - self._drag_object_point.x, point.y - self._drag_object_point.y)
            self.show_handlers(screen, ScreenSelectedObject(self._drag_object_id, offset=offset))
            print "dragging :", self._drag_object_id, offset

    def select_shape(self, id):
        """po undo"""
        self._selected_objects = [id]
        self._object_index = 0
            
    def press(self, screen, point):
        timer.start("press")
        if self._object_index != None:
            id = self._selected_objects[self._object_index]
            found = list(reversed(screen.get_canvas().find_objects_at_position(point))) # apverciame kad pirmi eitu tie kuriuos nupaiseme veliausiai
            if id in found:
                self._drag_object_id = id # start dragging object
                self._drag_object_point = point # start of the dragging
            else:
                self._drag_object_id = None
        timer.end("press")
        
    def get_next(self, screen, point):
        """returns object id's of shapes under the point (in sequence)"""
        found = list(reversed(screen.get_canvas().find_objects_at_position(point)))
        previous_id = None
        if self._object_index != None:
            previous_id = self._selected_objects[self._object_index] # previously selected id
        
        length = len(found)
        if not length:
            self.clear(screen)
        elif str(self._selected_objects) != str(found): # naujas paspaudimas su rezultatu
            self._object_index = 0
            self._selected_objects = found

            if previous_id != None and length > 1 and found[0] == previous_id:
                self._object_index = 1 # neimame tokio paties objekto jeigu jis yra pirmas naujame rinkinyje po paspaudimo
        else: # toks pat rezultatas
            self._object_index += 1
            if self._object_index == len(self._selected_objects):
                self._object_index = 0
                
        if length:
            return self._selected_objects[self._object_index]
        return None
            
    
    def release(self, screen, point):
        timer.start("release")
        if self._drag_object_id != None: # object drag end
            offset = (point.x - self._drag_object_point.x, point.y - self._drag_object_point.y)
            if offset != (0,0):
                Invoker.execute(MoveShapeCommand(self, screen, self._drag_object_id, offset))
                text = "Object %i was moved." % self._drag_object_id
                self._drag_object_id = None
                return text

        shape_id = self.get_next(screen, point)
        
        if shape_id != None:
            self.show_handlers(screen, ScreenSelectedObject(shape_id))
            timer.end("release")
            return "%i:%i of %i" % (self._object_index, shape_id, len(self._selected_objects))
        else: 
            timer.end("release")
            return "No objects found"
            
            
        
        
class DetectPointTool(Tool):
    def __init__(self):
        self._curve_id = None

    def press(self, screen, point):
        #print "DetectPointTool press...", widget, event
        #print "find_objects_at_position: ", point
        
        found = screen.get_canvas().find_objects_at_position(point)
        
        #print "Found: ", found
        
        def test(obj, tool):
            if obj[0] == 4:
                #data = Shape.decompress(obj).get_data()
                #data1 = geometry.curve2ocad(data)
                #data2 = geometry.triplets2bezier(data)
                
                geometry.bezier_points = []
                
                timer.start("BezierLength") # praleidziama pirma ir paskutines koordinates
                length = geometry.bezier_length(obj[3:], maxdepth=4, distance_tolerance=0.25)
                # bent dvigubai greiciau nei, kai distance_tolerance=None, panasu kai maxdepth=3
                # reikia apsispresti kas geriau (maxdepth=4, distance_tolerance=0.25), ar (maxdepth=3, distance_tolerance=None)
                # panasu, kad maxdepth=3 - duoda daugiau tasku
                # maxdepth=3 - rezultatas mane tenkina, ar galima pagreitinti pridejus distance_tolerance?
                timer.end("BezierLength")
                print "bezier length: ", length
                
                timer.start("CairoLength")
                length2 = geometry.cairo_curve_length(obj[3:])
                timer.end("CairoLength")
                print "cairo length: ", length2
                
                
                if tool._curve_id:
                    screen.replace(tool._curve_id, ScreenLine(geometry.bezier_points))
                else:
                    tool._curve_id = screen.add(ScreenLine(geometry.bezier_points))

                #timer.start("BezierLength22")
                #print "lnegth: ", geometry.bezier_length(data2, maxdepth=4, distance_tolerance=None)
                #timer.end("BezierLength22")
                
                return "Length: " + str(length)
            else:
                return str(obj[1]) + " - z-index: " + str(screen.get_canvas().get_styler().get_style(obj).get("z-index", "?")) #obj[1]
        
        
        return str([str(test(screen.get_canvas().get_object_by_id(id), self)) for id in found])

        
class AddPointCommand:
    def __init__(self, screen, point):
        self._screen = screen
        self._point = point
        self._shape_id = None
     
    def execute(self):
        if self._shape_id == None: # user action (not redo)
            self._shape_id = self._screen.add_shape(Shape(1, self._point, symbol="graphics")) # screen atomatiskai perpaisys ta plota
        else: # redo
            self._screen.replace_shape(self._shape_id, Shape(1, self._point, symbol="graphics"))
        return True
    
    def undo(self):
        #print "remove point: ", self._shape_id
        self._screen.remove_shape(self._shape_id)


class AddPointTool(Tool):
    def press(self, screen, point):
        #print "AddTool press...", widget, event
        upoint = screen.get_canvas().device_to_user(point)
        Invoker.execute(AddPointCommand(screen, upoint))
        #upoint = screen.get_canvas().device_to_user(point)
        #screen.add_shape(Shape(1, upoint, color=16711680)) # screen atomatiskai perpaisys ta plota
    def run(self, screen):
        screen.ui_set_cursor("cross")
    def stop(self, screen):
        screen.ui_set_cursor(None)


class AddLineCommand:
    def __init__(self, screen, line):
        self._screen = screen
        self._line = line
        self._shape_id = None
     
    def execute(self):
        if self._shape_id == None: # user action (not redo)
            self._shape_id = self._screen.add_shape(Shape(3, self._line, symbol="graphics")) # screen atomatiskai perpaisys ta plota
        else: # redo
            self._screen.replace_shape(self._shape_id, Shape(3, self._line, symbol="graphics"))
        return True
    
    def undo(self):
        #print "remove point: ", self._shape_id
        self._screen.remove_shape(self._shape_id)

        
class AddLineTool(Tool):
    def __init__(self):
        self._line= []
        self._line_overlay_id = None
        self._control = None

    def run(self, screen):
        screen.ui_set_cursor("cross")

    def stop(self, screen):
        self._line= []
        if self._line_overlay_id:
            screen.remove(self._line_overlay_id)
            self._line_overlay_id = None
        screen.ui_set_cursor(None)
    
    def get_control_point(self, screen, upoint):
        length = len(self._line)
        if not length: return None
        if screen.is_control(self._line[-1], upoint):
            return (self._line[-1].x-upoint.x, self._line[-1].y-upoint.y)
        return None

    def press(self, screen, point):
        print "Line start point: ", point
        upoint = screen.get_canvas().device_to_user(point)

        if len(self._line):
            self._control =self.get_control_point(screen, upoint)
            if self._control:
                return # galime pradeti draginti controles tashka

        self._line.append(upoint)
        if not self._line_overlay_id:
            self._line_overlay_id = screen.add(ScreenLine(self._line))
    
    def drag(self, screen, point):
        print "Line drag point: ", point
        upoint = screen.get_canvas().device_to_user(point)
        
        if self._control:
            self._line[-1] = Vec2d(upoint.x + self._control[0], upoint.y + self._control[1])
            screen.replace(self._line_overlay_id, ScreenLine(self._line))
            #self.update_control(upoint, self._control)
        else:
            screen.replace(self._line_overlay_id, ScreenLine(self._line + [upoint]))
        
    def move(self, screen, point):
        if len(self._line):
            upoint = screen.get_canvas().device_to_user(point)
            control = self.get_control_point(screen, upoint) # control point data or None
            if control:
                screen.ui_set_cursor(None)
            else:
                screen.ui_set_cursor("cross")

    def release(self, screen, point): # release
        """turetu grazinti liijos ilgi i statusa"""
        print "Line end point: ", point
        upoint = screen.get_canvas().device_to_user(point)

        # jeigu clikas tai baigiam braizyti
        if self._line[-1] == upoint and not self._control:
            self._line.pop()
            if len(self._line) > 1:
                Invoker.execute(AddLineCommand(screen, self._line))
                #screen.add_line(self._line)
            self._line = []
            self._control = None
            screen.remove(self._line_overlay_id)
        elif self._control:
            self._control = None
        else: # kituy atveju braizom toliau
            self._line.append(upoint)
        

#from bezier import update_c2
class AddCurveCommand:
    def __init__(self, screen, curve):
        self._screen = screen
        self._curve = curve
        self._shape_id = None
     
    def execute(self):
        if self._shape_id == None: # user action (not redo)
            self._shape_id = self._screen.add_shape(Shape(4, self._curve, symbol="graphics")) # screen atomatiskai perpaisys ta plota
        else: # redo
            self._screen.replace_shape(self._shape_id, Shape(4, self._curve, symbol="graphics"))
        return True
    
    def undo(self):
        #print "remove point: ", self._shape_id
        self._screen.remove_shape(self._shape_id)

        
class AddCurveTool(Tool):
    def __init__(self):
        self._curve= []
        self._curve_overlay_id = None
        # taskas: (x, y, cx1, cy1, cx2, cy2)
        self._control = None
        self._active_controls = 0 # 0 - jeigu rodyti visus aktyvius, 2 - 2 paskutinius (nuo galo)
        
    def run(self, screen):
        screen.ui_set_cursor("cross")

    def stop(self, screen):
        self._curve= []
        if self._curve_overlay_id:
            screen.remove(self._curve_overlay_id)
            self._curve_overlay_id = None
        screen.ui_set_cursor(None)

        
    def update_control(self, c2, controller=None):
        # control: (0, Point()), 0-xy, 1-c1, 2-c2, point - press point
        index = -1
        control = 2
        hand = (0,0)
        
        if controller:
            index, control, hand = controller
            c2 = Vec2d(c2.x+hand[0], c2.y+hand[1])

        last_point = self._curve[index]
        #reikia rasti taska priesingoje puseje!
        x, y = last_point[1] #, last_point[1]
        
        if control != 1: # handler
            cur_point = Vec2d(x, y)
            handle = Vec2d(c2.x, c2.y)
            
            length = len(self._curve)
            opposite = 2 if (control == 0) else 0
            vect = (handle - cur_point) #/ 2.0 # randam poslinki (vektoriu)
            
            if length > 1 and (index == -1 or index == (length-1)): # judinam priesinga proporcingu atstumu ir tuo paciu kampu
                vect.rotate(180) # apsukam
                last_point[opposite] = cur_point + vect # gaunam priesingoje puseje esanti taska
            elif length > 1: # judinam priesinga tik tuo paciu kampu, atstumo nekeisdami
                opposite_point = Vec2d(last_point[opposite])
                vect2 = (opposite_point - cur_point)
                angle_between = vect.get_angle_between(vect2)
                vect2.rotate(180 - angle_between)
                last_point[opposite] = cur_point + vect2
                #print "angle...: ", angle_between
            
            last_point[control] = c2
        else:
            previous = Vec2d(x, y)
            new = Vec2d(c2)
            diff = new - previous
            
            last_point[0] = Vec2d(last_point[0]) + diff
            last_point[1] = new
            last_point[2] = Vec2d(last_point[2]) + diff
 
    
    def get_control_point(self, screen, point):
        # print "searching for control point under the cursor"
        # return (1, point) 0 - xy, 1 - c1, 2 - c2
        
        length = len(self._curve)
        if not length: return None
            
        visible_controls = range(length)[-self._active_controls:]    
        
        for index in visible_controls:
            last = self._curve[index]
            for i in xrange(0, 3):
                control = last[i]
                #print "Control: ", control
                if screen.is_control(control, point):
                    return (index, i, (control.x-point.x, control.y-point.y))
            
        return None

        
    def press(self, screen, point):
        print "Line start point: ", point
        upoint = screen.get_canvas().device_to_user(point)
        
        if len(self._curve):
            #print "test if it's not control point!", point, self._curve[-1]
            self._control = self.get_control_point(screen, upoint) # control point data or None
            if self._control:
                return # galime pradeti draginti controles tashka
        
        self._curve.append([upoint, upoint, upoint])
        if not self._curve_overlay_id:
            self._curve_overlay_id = screen.add(ScreenCurve(self._curve, self._active_controls)) # kur papaudziu dedamas taskas
    
    def drag(self, screen, point):
        print "Line drag point: ", point
        upoint = screen.get_canvas().device_to_user(point)
        
        if self._control:
            self.update_control(upoint, self._control)
        else:
            self.update_control(upoint)
        
        screen.replace(self._curve_overlay_id, ScreenCurve(self._curve, self._active_controls)) # kur draginu - kampas C2 bezier taskas
        
    def move(self, screen, point):
        if len(self._curve):
            upoint = screen.get_canvas().device_to_user(point)
            control = self.get_control_point(screen, upoint) # control point data or None
            if control:
                screen.ui_set_cursor(None)
            else:
                screen.ui_set_cursor("cross")

    def release(self, screen, point): # release - kampas uzfiksuojamas !
        """turetu grazinti liijos ilgi i statusa"""
        print "Line end point: ", point
        upoint = screen.get_canvas().device_to_user(point)
        
        if self._curve[-1][0] == upoint and not self._control:
            self._curve.pop() # pasaliname pasutini taska...
            if len(self._curve) > 1:
                Invoker.execute(AddCurveCommand(screen, self._curve))
                #screen.add_shape(Shape(4, self._curve, color=16711680)) # screen atomatiskai perpaisys ta plota
            self._curve = []
            self._control = None
            screen.remove(self._curve_overlay_id)
        else: # kitu atveju braizom toliau
            pass
        


