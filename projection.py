from utils import Point

class GisProjection:
    """
    Konvertuosime gauto zemelapio koordinates i user koordinates
    |
    |
    0_____ koordinates cia cartesian
    """
    def __init__(self, bbox=False, map_scale=1):
        #self.canvas = canvas
        self.top = [0, 0] #[-inf, -inf] # top rigth corner
        self.bottom = [0, 0] #[inf, inf] # bottom left corner
        #self.map_area = Area(0,0,0,0)
        self.map_scale = map_scale
        print "GisProjection map scale: ", self.map_scale
        
        #self.scale = 1
        
        if bbox:
            self.bottom[0], self.bottom[1], self.top[0], self.top[1] = bbox
            #self.map_area = Area(self.bottom[0], self.bottom[1], self.top[0]-self.bottom[0], self.top[1]-self.bottom[1])
            #self.scale = self.map_area.height / (self.canvas._device_area.height * self.canvas._ratio_index[-4])
        
    #def extend_with_point(self, point):
    #    if point.x > self.top[0]: self.top[0] = point.x
    #    if point.x < self.bottom[0]: self.bottom[0] = point.x
    #    if point.y > self.top[1]: self.top[1] = point.y
    #    if point.y < self.bottom[1]: self.bottom[1] = point.y
        
    #    #self.map_area = Area(self.bottom[0], self.bottom[1], self.top[0]-self.bottom[0], self.top[1]-self.bottom[1])
    #    #self.scale = self.map_area.height / (self.canvas._device_area.height * self.canvas._ratio_index[-4])
    #    #man reikia kad scale butu toks kad didziausiam zoom levelyje butu pilnai rodomas zemelapis
        
    #    #self.scale = 1
    #    #self.bottom = [0, 0]
    #    #self.top = [0, 0]
        
    def get_center(self):
        center = Point((self.bottom[0] + self.top[0])/2 * self.map_scale, (self.bottom[1] + self.top[1])/2 * self.map_scale)
        return center
    
    def map_to_user(self, point):
        scale = 1
        p = Point((point[0]-self.bottom[0])/scale*self.map_scale, -(point[1]-self.bottom[1])/scale*self.map_scale)
        return p
    
    def user_to_map(self, point):
        scale = 1
        p = Point(point.x * scale / self.map_scale + self.bottom[0], (-point.y * scale)/self.map_scale+self.bottom[1])
        return p
