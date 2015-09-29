import cairo
from math import pi, cos, sin, atan2, sqrt
from vec2d import Vec2d


bezier_points = []
"""
http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect/563240#563240
// Returns 1 if the lines intersect, otherwise 0. In addition, if the lines 
// intersect the intersection point may be stored in the floats i_x and i_y.
"""
def get_line_intersection(p0_x, p0_y, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y):
    #float s1_x, s1_y, s2_x, s2_y;
    s1_x = p1_x - p0_x
    s1_y = p1_y - p0_y
    s2_x = p3_x - p2_x
    s2_y = p3_y - p2_y

    deliminator = (-s2_x * s1_y + s1_x * s2_y)
    if deliminator == 0:
        return None
    
    s = (-s1_y * (p0_x - p2_x) + s1_x * (p0_y - p2_y)) / deliminator
    t = ( s2_x * (p0_y - p2_y) - s2_y * (p0_x - p2_x)) / deliminator

    if s >= 0 and s <= 1 and t >= 0 and t <= 1:
        # Collision detected
        return (p0_x + (t * s1_x), p0_y + (t * s1_y))

    return None # No collision


# nanaudojamas - kaip neefektyvus ir nepatikimas    
def find_path_intersections(path, skip_cups=False):
    intersections = [] # (line_index1, line_index2, intersection_point) 
    length = len(path)
    i = 0
    
    #print "Length: ", len(path)
    while i < length:
        segment = path[i]
        x = i + 2 # praleidziame sekancia linija einancia po jos 
        while x < length and x < i + 20: # pasalinsime tik mazas kilpas - galima pasinudoti atkarpu skaiciumi - kad islaikyti proporcijas zoominant
            n = path[x] # other segment
            
            intersection = get_line_intersection(segment[0], segment[1], segment[2], segment[3], n[0], n[1], n[2], n[3])
            if intersection:
                #intersections.append((i, x, intersection, find_path_intersections(path[i:x])))
                intersections.append((i, x, intersection))
                if skip_cups:
                    i = x
            x += 1
        i += 1
    return intersections
    

# nanaudojamas - kaip neefektyvus ir nepatikimas    
def remove_path_intersections(path):
    intersections = find_path_intersections(path, skip_cups=True)

    new_path = []
    start = 0
    #print "start:"
    for intersection in intersections:
        #print "intersection: ", intersection
        i, x, point = intersection
        
        new_path.extend(path[start:i])
        new_path.append([path[i][0], path[i][1], point[0], point[1]])
        new_path.append([point[0], point[1], path[x][2], path[x][3]])
        start = x
    new_path.extend(path[start:len(path)])
    
    if len(new_path):
        return new_path
    
    return path
    
        
    
def cairo_path_offset(path, distance):
    #1. Offset Line Segments
    #2. Merge/Clip Intersections
    new_path = []
    
    current_point = None
    for type, point in path:
        if type == cairo.PATH_LINE_TO:
            
            parallel_line = create_parrallel_line([current_point[0], current_point[1], point[0], point[1]], distance)
            intersection = False
            if len(new_path):
                top = new_path.pop()
                intersection = get_line_intersection(top[0], top[1], top[2], top[3], parallel_line[0], parallel_line[1], parallel_line[2], parallel_line[3])
                if intersection:
                    new_path.append([top[0], top[1], intersection[0], intersection[1]])
                    new_path.append([intersection[0], intersection[1], parallel_line[2], parallel_line[3]])
                else:
                    new_path.append(top)
                    new_path.append(parallel_line)
            else:
                new_path.append(parallel_line)
        current_point = point
    
    #return remove_path_intersections(new_path)
    return new_path
   

def cairo_path_offset2(path, distance):
    #1. Offset Line Segments
    #2. Merge/Clip Intersections
    new_path = []
    
    current_point = None
    for type, point in path:
        if type == cairo.PATH_LINE_TO:
            
            parallel_line = create_parrallel_line([current_point[0], current_point[1], point[0], point[1]], distance)
            intersection = False
            if len(new_path):
                #intersection = get_line_intersection(top[0], top[1], top[2], top[3], parallel_line[0], parallel_line[1], parallel_line[2], parallel_line[3])
                intersection = get_line_intersection(new_path[-4], new_path[-3], new_path[-2], new_path[-1], parallel_line[0], parallel_line[1], parallel_line[2], parallel_line[3])
                
                if intersection:
                    new_path[-2] = intersection[0]
                    new_path[-1] = intersection[1]
                    new_path.append(parallel_line[2])
                    new_path.append(parallel_line[3])
                else:
                    new_path.extend(parallel_line)
            else:
                new_path = parallel_line
                #new_path.append(parallel_line)
        current_point = point
    
    #return remove_path_intersections(new_path)
    return new_path
   
def create_parrallel_line(line, distance):
    """Line as [x1, y1, x2, y2]"""
    x1, y1, x2, y2 = line
    lx, ly = x2 - x1, y2 - y1
    
    length = sqrt(lx*lx + ly*ly)
    if length == 0:
        return line
    
    offset_x = (ly * distance)/length
    offset_y = -(lx * distance)/length
    
    return [x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y]
    

def cairo_path_length(path, index_from=0):
    """index_from - index to start counting length from"""
    length = 0
    current_point = None
    
    if index_from != 0:
        current_point = path[index_from - 1][1]
        path = path[index_from:]
    
    for type, point in path:
        #print "type", type, " point", point
        point = Vec2d(point)
        if type == cairo.PATH_LINE_TO:
            length += (point - current_point).get_length()
        current_point = point
            
    return length    


def cairo_curve_length(curve):
    """Calculate cubic beziercurve length. Curve represented as list: 
        [p1, p2(handle1), p3(handle), p4, p5(handle), p6(handle), p7,....]
        Flattens the curve using cairo and adds the length of segments.
    """
    surface = cairo.ImageSurface(cairo.FORMAT_A8, 0,  0)
    ctx = cairo.Context(surface)

    ctx.move_to(curve[0], curve[1])
    for i in xrange(2, len(curve), 6):
        #p1 = Vec2d(curve[i], curve[i+1])
        p2 = Vec2d(curve[i], curve[i+1])
        p3 = Vec2d(curve[i+2], curve[i+3])
        p4 = Vec2d(curve[i+4], curve[i+5])

        ctx.curve_to(p2.x, p2.y, p3.x, p3.y, p4.x, p4.y)

    path = ctx.copy_path_flat()
    
    length = 0
    current_point = None
    for type, point in path:
        point = Vec2d(point)
        if type == 1: # line to
            length += (point - current_point).get_length()
        current_point = point
            
    return length    
        
    #length += curve_length(Vec2d(curve[i], curve[i+1]), Vec2d(curve[i+2], curve[i+3]), Vec2d(curve[i+4], curve[i+5]), Vec2d(curve[i+6], curve[i+7]))

    #bezier_points.append(Vec2d(curve[-2], curve[-1])) # idedame paskutni taska
    #return length
    

def recursive_bezier(p1, p2, p3, p4, distance_tolerance=0.5, maxdepth=4, depth=0):
    """Calculate length of cubic bezierline, increase maxdepth to get better accuracy
        Documentation: https://github.com/vosvos/foxycad/wiki/BezierCurves
        distance_tolerance <= 0.5 in typical screen resolution
    """
    if depth <= maxdepth:
        p12 = 0.5 * (p1 + p2)
        p23 = 0.5 * (p2 + p3)
        p34 = 0.5 * (p3 + p4)
        p123 = 0.5 * (p12 + p23)
        p234 = 0.5 * (p23 + p34)
        p1234 = 0.5 * (p123 + p234)
        
        bezier_points.append(p1)
        #bezier_points.append(p1234)

        curve_is_flat = False
        # enforce subdivision at least one time (depth>0)
        if depth > 0 and distance_tolerance != None:
            # distance between point 1234 and the midpoint of 1-4. Comes close to 0 for flat curve segment.
            distance = (p1234 - 0.5 * (p1 + p4)).get_length()
            curve_is_flat = (distance <= distance_tolerance)
            
        if not curve_is_flat:
            # split curve into two curves until segment is close to flat
            length = recursive_bezier(p1, p12, p123, p1234, distance_tolerance, maxdepth, depth+1)
            length += recursive_bezier(p1234, p234, p34, p4, distance_tolerance, maxdepth, depth+1)
            return length
    
    # end of recursion, return length of the segment
    return (p4 - p1).get_length()

            
    
def bezier_length(curve, distance_tolerance=0.5, maxdepth=4):
    """Calculate cubic beziercurve length. Curve represented as list: 
        [p1, p2(handle1), p3(handle), p4, p5(handle), p6(handle), p7,....]
    """
    length = 0
    for i in xrange(0, len(curve)-2, 6):
        length += recursive_bezier(Vec2d(curve[i], curve[i+1]), Vec2d(curve[i+2], curve[i+3]), Vec2d(curve[i+4], curve[i+5]), Vec2d(curve[i+6], curve[i+7]), distance_tolerance, maxdepth)

    bezier_points.append(Vec2d(curve[-2], curve[-1])) # idedame paskutni taska
    return length

