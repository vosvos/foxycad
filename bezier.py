import cairo
from math import pi, sqrt
from vec2d import Vec2d

width = 500
height = 500
graph_data = [
(0, 10),(20, 50),(40, 80),(60, 5),(80, 10),(100, 20),
(120, 30),(140, 60),(160, 95),(180, 30),(200, 50),
(220, 70),(240, 80),(260, 10),(280, 60),(300, 30),
(320, 90),(340, 95),(360, 30),(380, 10),(400, 5),
(420, 20),(440, 80),(460, 70),(480, 20),(500, 40),
(490, 0), (450, 20), (420, 40), (495, 60), (490, 80),
(480, 100), (470, 120), (440, 140), (405, 160), 
(470, 180), (450, 200), (430, 220), (420, 240),
(490, 260), (440, 280), (470, 300), (410, 320),
(405, 340), (470, 360), (490, 380), (495, 400), 
(480, 420), (420, 440), (430, 460), (480, 480), (460, 500),
(500, 490), (480, 450), (460, 420), (440, 495), (420, 490), 
(400, 480), (380, 470), (360, 440), (340, 405), (320, 470), 
(300, 450), (280, 430), (260, 420), (240, 490), (220, 440), 
(200, 470), (180, 410), (160, 405), (140, 470), (120, 490), 
(100, 495), (80, 480), (60, 420), (40, 430), (20, 480), (0, 460)
]



#def update_c2(curve, index, point, control=2):

def update_c2(curve, c2, control=2):
    # control: (0, Point()), 0-xy, 1-c1, 2-c2, point - press point

    last_point = curve[-1]
    #reikia rasti taska priesingoje puseje!
    x, y = last_point[0] #, last_point[1]
    
    if control:
        cur_point = Vec2d(x, y)
        hadle = Vec2d(c2.x, c2.y)
        
        vect = (hadle - cur_point) #/ 2.0 # randam poslinki (vektoriu)
        vect.rotate(180) # apsukam

        if len(curve) > 1:
            cpoint = cur_point + vect # gaunam priesingoje puseje esanti taska
            last_point[(control == 1) and 2 or 1] = cpoint
        last_point[control] = c2
    else:
        previous = Vec2d(x, y)
        new = Vec2d(c2)
        diff = new - previous
        
        last_point[0] = new
        last_point[1] = Vec2d(last_point[1]) + diff
        last_point[2] = Vec2d(last_point[2]) + diff
        


    

def prepare_curve_data(graph_data):
    prepared_data = []
    for i in range(len(graph_data)):
        x, y = graph_data[i][0], graph_data[i][1]
        cur_point = Vec2d(graph_data[i][0], graph_data[i][1]) # taskas
        
        
        if (i != 0) and (i != len(graph_data) - 1):
            back_point = Vec2d(graph_data[i - 1][0], graph_data[i - 1][1]) # pries tai buves taskas
            forw_point = Vec2d(graph_data[i + 1][0], graph_data[i + 1][1]) # priekyje esantis taskas
                        
            back_vect = back_point - cur_point # vektorius - matematiskai apraso kaip is vieno tasko patekti i kita
            forw_vect = forw_point - cur_point
            back_vect_proj = back_vect / 2.0
            forw_vect_proj = forw_vect / 2.0
            
            angle_between = back_vect.get_angle_between(forw_vect) / 2.0          
            
            back_vect.rotate(angle_between - 90)
            forw_vect.rotate(90 - angle_between)
            
            print "back point:", back_point, " back vect:", back_vect, "cur_point:", cur_point, " forw point:", forw_point, " forw vect:", forw_vect
            print "back_vect_proj:", back_vect_proj, " forw:", forw_vect_proj
            print "angle: ", angle_between
            print "after rotate:", back_vect, forw_vect
            
            
            back_vect = back_vect_proj.projection(back_vect)
            forw_vect = forw_vect_proj.projection(forw_vect)
            
            print "proj: ", back_vect, forw_vect
            
            back_cpoint = cur_point + back_vect
            forw_cpoint = cur_point + forw_vect
            
            print "c1, c2: ", back_cpoint, forw_cpoint
            
            cx1, cy1 = back_cpoint[0], back_cpoint[1]
            cx2, cy2 = forw_cpoint[0], forw_cpoint[1]
        
        else:
           cx1, cy1, cx2, cy2 = x, y, x, y 
        
        prepared_data.append((x, y, cx1, cy1, cx2, cy2))
        
    return prepared_data

def draw_point(cr, x, y, opacity, stroke=True, color=(0,0,1)):
    cr.move_to(x+3, y)
    cr.arc(x, y, 3, 0, 2 * pi)
    cr.set_source_rgba(color[0], color[1], color[2], opacity)

    if stroke:
        cr.stroke()
    
    cr.arc(x, y, 2, 0, 2 * pi)
    cr.set_source_rgba(1, 1, 1, 1.0)
    
    if stroke:
        cr.stroke()

def debug_points(cr, prepared_data):
    for i in range(0, len(prepared_data)):
        x, y = prepared_data[i][2] +0.5, prepared_data[i][3] +0.5
        cx1, cy1 = prepared_data[i][0] +0.5, prepared_data[i][1] +0.5
        cx2, cy2 = prepared_data[i][4] +0.5, prepared_data[i][5] +0.5

        draw_point(cr, x, y, 1)
        if cx1 != x or cy1 != y:
            draw_point(cr, cx1, cy1, 0.5)
            cr.move_to(x, y)
            cr.line_to(cx1, cy1)
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.stroke()

        if cx2 != x or cy2 != y:
            draw_point(cr, cx2, cy2, 0.5)
            cr.move_to(x, y)
            cr.line_to(cx2, cy2)
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.stroke()

def poly_curve(cr, prepared_data):
    for i in range(0, len(prepared_data) - 1):
        x, y = prepared_data[i][2], prepared_data[i][3]
        cx1, cy1 = prepared_data[i][4], prepared_data[i][5]
        cx2, cy2 = prepared_data[i + 1][0], prepared_data[i + 1][1]
        x2, y2 = prepared_data[i + 1][2], prepared_data[i + 1][3]
        cr.move_to(x, y)
        cr.curve_to(cx1, cy1, cx2, cy2, x2, y2)

def main(graph_data):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    cr.set_line_width(1)
    cr.set_source_rgb(1, 1, 1)
    cr.set_operator (cairo.OPERATOR_SOURCE)
    cr.paint()

    prepared_data = prepare_curve_data(graph_data)
    debug_points(cr, prepared_data)

    cr.set_line_width(2)
    poly_curve(cr, prepared_data)
    cr.set_source_rgb(0, 0, 0)
    cr.stroke()

    surface.write_to_png('curve.png')

if __name__ == "__main__":
    main(graph_data)
