from sys import float_info

import cairo
import fshape
import geometry

from vec2d import Vec2d

class Stroker:
    def __init__(self, painter, ctx, style):
        self.painter = painter
        self.ctx = ctx
        self.style = style
        
        self._zindex = style.get("z-index", -1)
        self._zindex_list = style.get("z-index-list", [self._zindex]) # nulineje pozicijoje turi buti tas kuri paisome pati pirma! kiti - likusios spalvos
        
        self._line_width = style.get("line-width", 0)
        self._double_width = style.get("double-width", 0)
        self._double_zindex = style.get("double-z-index", -1) # gali buti, kad width yra - bet paisyti nereikia - tada z-index
        
        if self._double_width: # jeigu linija su krastais...
            self._double_left_width = style.get("double-left-width")
            #print "self._double_left_width: ", self._double_left_width, style
            self._double_right_width = style.get("double-right-width")
            self._double_left_zindex = style.get("double-left-z-index", -1)
            self._double_right_zindex = style.get("double-right-z-index", -1)
            self._double_color = style.get("double-color")
            self._double_left_color = style.get("double-left-color")
            self._double_right_color = style.get("double-right-color")

        self._symbol_data = style.get("symbol-data", None)
        
        self._dash_points = style.get("dash-points", [])
        self._corner_points = style.get("corner-points", [])
    
        self._main_length = style.get("length-main", 0.0)
        self._left_end_length = style.get("length-end", 0.0)
        self._right_end_length = self._left_end_length #style.get("length-end", 0.0)
        self._main_gap = style.get("length-gap", 0.0)
        
        self._symbol_repeat = style.get("symbol-repeat", 1)
        self._symbol_distance = style.get("symbol-distance", 0.0)
        
        self._dash_pattern =  self._main_length and self._main_gap
        
        self._dash_index = self.create_dash_index()
        #print "self._dash_index", self._dash_index, self._corner_points
        
        self._previous_path_index = 0 # geometry.cairo_path_length() - kviesime ne visai atkarpai o tik nuo praejusio dash_point indexo
        self._path_length = 0 # pridesime po kiekvieno dash pointo

        self._special_points = [] # (atkarpos ilgis, tasko tipas)
    

    def create_dash_index(self):
        if (self._dash_pattern or self._symbol_data) and (self._dash_points or self._corner_points):
            dash_points = map(lambda x:(2*x-2, 1), self._dash_points) # x*2 - nes (x,y), -2 - nes praleidziame pati pirma; - 1 dash point; 2 - corner point
            corner_points = map(lambda x:(2*x-2, 2), self._corner_points) #2 - corner point
            
            dash_index = dict(dash_points)
            dash_index.update(dict(corner_points))

            if dash_index.has_key(0): # praleidizam pirma, dar nebent galetume ideti left_end = dash_half
                del dash_index[0]
            return dash_index
        else:
            return []

            
    def check_special_point(self, index):
        """ man reikia atkarpu ilgio... ir tasko tipo, o ne indexu:
        jeigu taskas yra special point tai issisaugome jo index'a islygintame (flat) path'e"""
        
        if index in self._dash_index:
            path = list(self.ctx.copy_path_flat())
            segment_length = geometry.cairo_path_length(path, self._previous_path_index)
            self._path_length += segment_length

            dash_type = self._dash_index[index]
            
            path_index = len(path)
            self._special_points.append((path_index, segment_length, dash_type))
            self._previous_path_index = path_index #len(path)
            
            #self._path_index.append((len(path),  self._dash_index[index])) # ar nereikia -1?
    
    def finish(self, path):
        """jeigu buvo dashingas, tai reikia ideti paskutine atkarpa ir pasaiciuoti galutini ilgi"""
        #path = list(self.ctx.copy_path_flat())
        
        if self._dash_index: # paskutine dash atkarpa...
            segment_length = geometry.cairo_path_length(path, self._previous_path_index)
            self._path_length += segment_length
            self._special_points.append((len(path), segment_length, 0)) # 1-dash, 2-corner, 0-end
        
    
    def get_path_length(self, path=None):
        if self._path_length == 0 and path != None: # pirma karta bus 0 - jeigu nebuvo dash/corner tasku
            #print "!!!path:", path
            self._path_length = geometry.cairo_path_length(path)
            
        return self._path_length
            

    def draw(self, fill_or_stroke=True, id=None):
        path = list(self.ctx.copy_path_flat())
        self.finish(path)
        
        # paisome dvigubos linijos viduri - jeigu duotas jos plotis ir fill_on
        if self._double_width and self._double_zindex != -1:
            # gali buti kad nupaiseme krastus - bet reikia nupaisyti viduri pagal line-width duomenis
            new_style = {"paint": "stroke",
                                  "z-index": self._double_zindex,
                                  "color": self._double_color,
                                  "line-width": self._double_width
                                }
            if self._double_zindex == self._zindex_list[0]: # piesiame vidine linija
                self.painter.styler.setup_style(self.ctx, fshape.CURVE, new_style)
                self.painter.callContextListeners(self.ctx, id, fshape.STROKE)
                
                if fill_or_stroke:
                    self.ctx.stroke()
            else: # linijos su krastais vidaus paisyma atidesime veliau
                self.painter.draw_later(self._double_zindex, ([fshape.CURVE, None, {}, self.ctx.copy_path()], new_style, id)) # padarome galimybe piesti ne tik elementa bet ir jau paruosta path'a

        # paisome paprasta linija
        elif self._line_width: # and not (self._double_zindex == -1 and self._double_width != 0): # reikia perdaryti, kad butu None - nes -1 tai normalus zindex'as
            # gali buti atveju, kai linijos simboliniai taskai tures aukstesni z-index'a - tada pagrindine linija reiketu atideti veliasniam paisymui...
            dash_pattern = self.get_path_pattern(self.get_path_length(path)) # jeigu nera dashingo tai grazins ()
            
            if self._zindex == self._zindex_list[0]: 
                self.ctx.set_dash(dash_pattern, 0)
                self.painter.callContextListeners(self.ctx, id, fshape.STROKE)
                
                if fill_or_stroke:
                    self.ctx.stroke()
            else: # gali buti kad pradzioje reikia nupiesti pagal linija einancius simbolius!
                self.style["symbol-data"] = None # kad nepiestume antra karta...
                self.style["z-index-list"] = [self.style.get("z-index")] # kad neimtume atidedineti
                self.style["dash-pattern"] = dash_pattern # jeigu stiliuje yra dash-pattern - tai jis naudojamas tiesiogiai set_dash() ir neskaiciuojamas per nauja
                
                self.painter.draw_later(self._zindex, ([fshape.CURVE, None, {}, self.ctx.copy_path()], self.style, id)) # padarome galimybe piesti ne tik elementa bet ir jau paruosta path'a
            
        self.ctx.new_path() # isvalome turima path'a nes arba jau nupaiseme - arba nusiunteme ji velesniam paisymui
        
            
        # paisome kairi krasta
        if self._double_width and self._double_left_width: # and self._double_left_zindex != -1:
            #print "stroke left line"
            line = geometry.cairo_path_offset2(path, (self._double_width+self._double_left_width)/2)
            new_style = {"paint": "stroke",
                                  "z-index": self._double_left_zindex,
                                  "color": self._double_left_color,
                                  "line-width": self._double_left_width
                                }
            if self._double_left_zindex == self._zindex_list[0]: # piesiame iskarto
                self.painter.styler.setup_style(self.ctx, fshape.POLYLINE, new_style)
                self.painter.draw_line(self.ctx, line, {}, fill_or_stroke, id)
                #self.ctx.stroke()
            else: # kairio krasto paisyma atidesime veliau...
                #print "widt/color/zindex", self._double_left_width, self._double_left_color, self._double_left_zindex
                self.painter.draw_later(self._double_left_zindex, ([fshape.POLYLINE, None, {}] + line, new_style, id))
                
       # paisome desini krasta
        if self._double_width and self._double_right_width: # self._double_right_zindex != -1:
            #print "stroke right line"
            line = geometry.cairo_path_offset2(path, -(self._double_width+self._double_right_width)/2)
            new_style = {"paint": "stroke",
                                  "z-index": self._double_right_zindex,
                                  "color": self._double_right_color,
                                  "line-width": self._double_right_width
                                }
            if self._double_right_zindex == self._zindex_list[0]: # piesiame iskarto
                self.painter.styler.setup_style(self.ctx, fshape.POLYLINE, new_style)
                self.painter.draw_line(self.ctx, line, {}, fill_or_stroke, id)
                #self.ctx.stroke()
            else: # desinio krasto paisyma atidesime veliau...
                self.painter.draw_later(self._double_right_zindex, ([fshape.POLYLINE, None, {}] + line, new_style, id))

            
        if self._symbol_data: # rekia paisyti simbolius palei linija
            #print "self._special_points", self._special_points
            if len(self._special_points):
                start_from = 0
                for path_index, segment_length, dash_type in self._special_points:
                    self.draw_symbol_pattern(path[start_from:path_index], segment_length, fill_or_stroke, id)
                    start_from = path_index-1
            else:
                self.draw_symbol_pattern(path, self.get_path_length(path) , fill_or_stroke, id)
     

     
    def draw_symbol_pattern(self, path, path_length, fill_or_stroke=True, id=None):
        if not path_length or not self._main_length:
            print "print return empty..."
            return
        
        #print "draw_symbol_pattern", path_length, self._left_end_length, 0, self._main_length, self._right_end_length
        (left_end, gap, main_length, right_end) = self.interpolate_line_pattern(path_length, self._left_end_length, 0, self._main_length, self._right_end_length)
        rest = 0 # kiek turime mm likusiu nuo praejusio/iu segmento/u
        #print "interpolate result:", left_end, gap, main_length, right_end

        previous_point = None
        previous_type = None
        xpoint = None # taskas kuriame nupaiseme paskutini simboli
        
        symbol_repeat = (self._symbol_repeat-1)
        if symbol_repeat:
            gap = self._symbol_distance*symbol_repeat # fiksuoto ilgio gabaliukas su simboliais
            #print "path_length", path_length, gap
            if path_length < gap: # trumpa atkarpa kurioje netelpa fiksuoto ilgio gabaliukas
                return
            (left_end, gap, main_length, right_end) = self.interpolate_line_pattern(path_length, self._left_end_length, gap, self._main_length, self._right_end_length)
            #print "symbol_repeat: ", path_length, left_end, gap, main_length, right_end
            # left_end - (*-*-*) simboliu seka - main - (*-*-*) - right_end
            #main_length -= 0.001

        if main_length <= 0: # labai trumpa atkarpa kur nera nupiesti simboli??? ant galu reikes leisti nupiesti
            main_length = right_end # trumpa atkarpa - dedame dash simboli tarp left end ir right end
        
        symbol_repeat_count = 0
        used_length = left_end # iki pirmo simbolio turime nupiesti left_end

        i = 0
        while i < len(path): #used_length < path_length:
            #print "i", i
            
            type, point = path[i]
            point = Vec2d(point)
            
            if i == 0:
                previous_point = point
            else:
                segment = point - previous_point
                length = segment.get_length()
                angle = -segment.get_angle() * 10
                
                if symbol_repeat_count:
                    distance_to_symbol = self._symbol_distance
                elif xpoint == None: # nenupiestas nei viena simbolis - reikia praleisti "_left_end_length"
                    distance_to_symbol = left_end
                else: # tai reiskia kad jau nupaiseme bent viena taska
                    distance_to_symbol = main_length
                
                if rest + length >= distance_to_symbol:
                    previous_distance_to_symbol = distance_to_symbol
                    
                    while length >= distance_to_symbol - rest:
                        #print "while ", length, " >= ", distance_to_symbol - rest, "main_length: ", main_length, "neigiamas?"

                        # jeigu dar tilps "right_end" - tai galiu nupiesti symbol pointa
                        #print "draw? ", used_length <= path_length - right_end, " because: ", used_length, "<=", (path_length+0.001)-right_end
                        if used_length <= path_length - right_end:
                            xpoint = previous_point + (distance_to_symbol -  rest) * segment.normalized()
                            
                            self.ctx.save()
                            self.painter.draw_point2(self.ctx, xpoint, {"angle":angle, "symbol-data":self._symbol_data, "z-index-list":self._zindex_list}, fill_or_stroke, id)
                            self.ctx.restore()
                      
                        previous_distance_to_symbol = distance_to_symbol
                        if symbol_repeat and symbol_repeat_count < symbol_repeat:
                            distance_to_symbol +=  self._symbol_distance
                            used_length += self._symbol_distance
                            symbol_repeat_count += 1
                        else:
                            distance_to_symbol +=  main_length
                            used_length += main_length
                            symbol_repeat_count = 0
                    
                    rest = length - (previous_distance_to_symbol - rest)
                else:
                    rest += length
            
            previous_point = point
            previous_type = type
            i += 1


            
    def interpolate_mainlength(self, length, main, gap):
        """ 
            Man per visa ilgi (length) reikia isdestyti patterna sudaryta is [gap, main, gap]
            left ir right end - dashais cia nesirupinama
            gap - dydzio niekada nekeisime
            taigi yra du variantai - arba sumazinsime(atsiras papildomas gap) main arba padidinsime - uzpildysime laisva plota
            paprasciausi patternai:
            0: gap
            1: gap, main, gap
            2: gap, main, gap, main gap
            
            Juos galiu aprasyti formule:
            0.5gap + i x (0.5gap, main, 0.5gap) + 0.5gap
            i = 0,1,2,...
        """
        #half_gap = 0.5 * gap
        count = (length - gap) / (main + gap) # (length - 0.5gap - 0.5gap) / (0.5gap + main + 0.5gap)
        fits = int(count) # tiek telpa pilnai -  ir tuo paciu tiek yra main
        rest = (length - gap) - fits*(main + gap)
        
        #print "fits: ", fits
        #print "length", length, " main:", main, " gap:", gap, " rest:", rest
           
        if (3 * rest) > main: # sukursime papildoma patterna, jeigu liko laisvo daugiau kaip puse "main" (leidziu ir maziau - todel 3 o ne 2)
            #print "main:", main, " rest:", rest, " fits:", fits, " gap:", gap, " (main+gap) - rest", (main+gap) - rest
            return main - ((main+gap) - rest)/(fits+1)
            
        if fits == 0: # jeigu naujas patternas netepa ir nera kur jo iterpti:
            #print "RETURN@", length - gap
            return length - gap
        
        return main + (rest/fits)
        
        
    def interpolate_line_pattern(self, length, left_end, gap, main, right_end):
        """grazina (left_end, gap, main, right_end)"""
        #print "interpolate_line_pattern: ", length, left_end, gap, main, right_end
        
        if length == 0:
            return (0,0,0,0)
        
        length -= 0.000001 # kat tikrai tilpu paskutinis simbolis
        pattern_length = length - left_end - right_end

        # trumpos atkarpos
        if pattern_length < 0 or (pattern_length - (gap+main)) < 0: # segmente netelpa galai, arba jeigu galai telpa, tai nera kur iterpti tarpo
            #print "zis..."
            end_length = (length - gap)/2
            if (end_length < 0) or (left_end == 0 or right_end == 0): # segmentas trumpesnis uz tarpa yra nustatyta kad nera left_end ir right_end
                #print "ZISQ", end_length, left_end, right_end
                return (0, 0, length, 0) # paisome juoda bruksni - gali buti kad reiktu padatyti atvirksciai gap=length (panasu, kad ocad'e taip)
            elif gap==0 and pattern_length >= 0.5*main and left_end == right_end == main: 
            # likutis yra didesnis uzh 1/2main, ir galai lygus main tada iterpsime tarpa (tik simboliams)
                #print "Dlala3"
                new_main = (length - 2*gap)/3
                return (new_main, gap, new_main, new_main)
            else:
                #print "IZSZ", end_length, gap, 0, end_length
                return (end_length, gap, 0, end_length) # juoda - tarpas - juoda
        
        main_length = self.interpolate_mainlength(pattern_length, main, gap)
        
        # jeigu noresime - tai cia dabar dar galesime perskaiciuoti left_end/right_end ilgius
        if (3 * main_length < main) and (left_end or right_end): 
            # main sutrumpejo tris kartus... tokiu atveju nakiname main o ji isdaliname galams 
            #(tikiuosi kad toks atvejis galimas tik kai linija turi viena main patterna - gal patikrinti?)
            #assert(int(pattern_length / main_length) == 1)
            rest = (main_length + gap)/2
            #print "new main: ", main_length, " main: ", main, " left/right: ",  left_end, right_end, "rest: ", rest, " length:", length
            left_end += rest
            right_end += rest
            main_length = 0 # jeigu main length ==0 , tai get_dash_pattern2 naudoja [left_end, gap, right_end]
        
        #if main_length > 0: # kad tikrai tilptu paskutinis simbolis atkarpoje
        #    main_length -=  0.001
        
        return (left_end, gap, main_length, right_end)

    
    """
    def get_line_pattern(self):
        if self._dash_pattern and not self._line_pattern:
            curve_length = geometry.cairo_path_length(self._final_path)
            # get_dash_pattern - reiketu optimizuoti arba perkelti i C koda (prie bindingu)
            # dash-pattern, (DistFromStart, DistToEnd, MainLength, LeftEndLength, RightEndLength, MainGap, SecGap, EndGap, MinSym)
            #self._line_pattern = self.get_dash_pattern(curve_length, self._main_length, self._main_gap, self._left_end_length, self._right_end_length)
            self._line_pattern = self.get_dash_pattern2(curve_length)
        return self._line_pattern
    """
    
    def get_dash_pattern2(self, length, left_end=None, right_end=None):
        """naudosime interpolate
            jeigus nepateikti left_end/right_end - tai naudosime atitinkamus self._*_length
        """
        if length == 0:
            return []
            
        left_end = left_end or self._left_end_length
        right_end = right_end or self._right_end_length
        
        gap = self._main_gap
        main = self._main_length

        #print "0: get_dash_pattern2", length, left_end, gap, main, right_end
        (left_end, gap, main, right_end) = self.interpolate_line_pattern(length, left_end, gap, main, right_end)
        #print "1: get_dash_pattern2", length, left_end, gap, main, right_end

        pattern_length = length - left_end - right_end
        
        if gap and main:
            dash_count = int(pattern_length/(gap + main)) # dar lieka vienas papildomas dash
            pattern = [gap, main] * dash_count
            pattern.insert(0, left_end)
            pattern.append(gap) # last gap
            pattern.append(right_end)
            return pattern
        elif gap:
            if left_end or right_end:
                return [left_end, gap, right_end] 
            else: # balti galai prasidedantys gapais...
                return [left_end, gap, (pattern_length-2*gap), gap, right_end] 
        else: # gap =0
            return [length]
                

        
        
    def get_path_pattern(self, path_length):
        """paskaiciuoja dash patterna visam pathui kuriame gali buti dash/corner tasku"""
        if not (self._main_length and self._main_gap): # no data for dashing
            return []
        
        if len(self._special_points):
            path_pattern = []
            dash_half = None # reikia cia issisaugoti, kad zinotume ka naudoti paskutineje atkarpoje
        
            for i in xrange(len(self._special_points)):
                path_index, segment_length, dash_type = self._special_points[i]
                
                if dash_type == 1: # dash point
                    dash_half = self._main_length * 0.5
                elif dash_type == 2: # corner point
                    dash_half = self._main_length
                # else - jeigu 0 tai bus paskutine atkara, kuri naudos pries tai buvusi dash_half
                
                if i == 0: # first segment
                    left_end, right_end = self._left_end_length, dash_half
                elif dash_type == 0: # last segment
                    left_end, right_end = dash_half, self._right_end_length  # naudojame anksciau issisaugota dash_half
                else: # inner segment
                    left_end = right_end = dash_half

                segment_pattern = self.get_dash_pattern2(segment_length, left_end=left_end, right_end=right_end)
                    
                if len(path_pattern) and len(segment_pattern):
                    head = path_pattern.pop()
                    head += segment_pattern[0] # kad nesigautu tarpo... apjungiam paskutini pries tai buvusios atkarpos dasha su naujos atkarpos pirmuoju
                    path_pattern.append(head)
                    path_pattern.extend(segment_pattern[1:])
                else: # pirmas segmentas arba grazino tuscia dasha
                    path_pattern.extend(segment_pattern)
            return path_pattern

        else: # dashing - no dash/corner points
            return self.get_dash_pattern2(path_length)
        
                