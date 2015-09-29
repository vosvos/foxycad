from struct import pack, unpack, calcsize, error
from collections import namedtuple


class Structure:
    data_type = {
        "Byte": "B",
        "LongInt": "i",
        "SmallInt": "h",
        "WordBool": "H",
        "Word": "H",
        "Double": "d"
    }
    structure = {}

    @staticmethod
    def add(struct_name, parameters):
        Structure.structure[struct_name] = (parameters, namedtuple(struct_name, " ".join([name for name, value in parameters])))
        # 0 - parametrai, 1 - class'e (tStruct)

    @staticmethod
    def create(struct_name, args):
        return Structure.structure[struct_name][1]._make(args)

        
    @staticmethod
    def update(struct_name, structure, attribute, value):
        """sukuria nauja su pakeista reiksme"""
        parameters, factory = Structure.structure[struct_name]
        args = []
        for i in xrange(len(parameters)):
            attr, type = parameters[i]
            
            if attr == attribute:
                args.append(value)
            else:
                args.append(structure[i])
        
        return factory._make(args)
        
    @staticmethod
    def calcsize(delphi_type):
        if delphi_type in Structure.data_type: # Byte,...
            fmt = "<" + Structure.data_type[delphi_type]
            return calcsize(fmt)
        elif isinstance(delphi_type, tuple): # array or String
            otype, size = delphi_type
            if otype == "String":
                fmt = "<B%ss" % str(size)
                return calcsize(fmt)
            else: # (LongInt, 15)
                return size * Structure.calcsize(otype)
        else: # TStructure
            parameters, tStruct = Structure.structure[delphi_type]
            # ocad 6 nebuve papildomi laukai praleidziami
            values = [Structure.calcsize(otype) for name, otype in parameters]
            return sum(values) 
        
        
    @staticmethod
    def read(delphi_type, file, default=[]): 
        """default - kai reikia nuskaityti nepilna struktura, (reiksmes kuriomis uzpildysim, tai ko nenuskaitom)"""
        if delphi_type in Structure.data_type: # Byte,...
            fmt = "<" + Structure.data_type[delphi_type]
            data = file.read(calcsize(fmt))
            
            #if calcsize(fmt) != len(data):
            #    print "fmt: ", fmt, data, calcsize(fmt), len(data)
            #    return ()
                
            return unpack(fmt, data)[0]
        elif isinstance(delphi_type, tuple): # array or String
            otype, size = delphi_type
            if otype == "String":
                fmt = "<B%ss" % str(size)
                string = unpack(fmt, file.read(calcsize(fmt)))
                return string[1][:string[0]]
            else: # (LongInt, 15)
                return [Structure.read(otype, file) for i in xrange(size)]
        else: # TStructure
            parameters, tStruct = Structure.structure[delphi_type]
            # ocad 6 nebuve papildomi laukai praleidziami
            values = [Structure.read(otype, file) for name, otype in parameters[:len(parameters) - len(default)]]

            for value in default: # pridedame defaultines reikmes OCAD6 ju nebuvo strukturoje
                values.append(value)

            return tStruct._make(values) 

        
Structure.add("TCord", [
  ('x', 'LongInt'),
            # lower four bits:
			# 1: this point is the first bezier curve point
			# 2: this point is the second bezier curve point
			# 4: for double lines: there is no left line between this point and the next point
			# 8: (OCAD 9) this point is a area border line or a virtual line gap
  ('y', 'LongInt') 
            # lower four bits:
            # 1: this point is a corner point
            # 2: this point is the first point of a hole in an area
            # 4: for double lines: there is no right line between this point and the next point
            # 8: (OCAD 7-9) this point is a dash point
])


Structure.add("TFileHeader", [
   ('OCADMark', 'SmallInt'), # 3245 (hex 0cad)
   ('SectionMark', 'SmallInt'), # OCAD 6: 0
                        #        OCAD 7: 7
                        #        OCAD 8: 2 for normal files
                        #                3 for course setting files
                        #        OCAD 9: 0 for normal map
                        #                1 for course setting project
    ('Version', 'SmallInt'),     #    6 for OCAD 6, 7 for OCAD 7, etc.
    ('Subversion', 'SmallInt'),  #    number of subversion (0 for 6.00,
                        #       1 for 6.01 etc.)
    ('FirstSymBlk', 'LongInt'),  #    file position of the first symbol block
    ('FirstIdxBlk', 'LongInt'),  #   file position of the first index block
    ('SetupPos', 'LongInt'), #   OCAD 6,7,8: file position of the setup record; OCAD 9: Not used
    ('SetupSize', 'LongInt'), #  OCAD 6,7,8: size (in bytes) of the setup record; OCAD 9: Not used
    ('InfoPos', 'LongInt'), #  OCAD 6,7,8: file position of the file
                        #       information. The file information is
                        #       stored as a zero-terminated string with
                        #       up to 32767 characters + terminating  zero
                        #       OCAD 9: Not used
    ('InfoSize', 'LongInt'),     #    OCAD 6,7,8: size (in bytes) of the file information; OCAD 9: Not used
    ('FirstStringBlk', 'LongInt'), #  OCAD 8,9 only. file position of the first string index block
    ('FileNamePos', 'LongInt'),  #    OCAD 9: file position of file name, used for temporary files only
    ('FileNameSize', 'LongInt'), #    OCAD 9: size of the file name, used for temporary files only
    ('FileLicenseNumber', 'LongInt') #    OCAD 10: license number
])  


Structure.add("TCmyk", [
    ('cyan', 'Byte'), # 2 times the cyan value as it appears in the Define Color dialog box (to allow half percents)
    ('magenta', 'Byte'), # dito for magenta
    ('yellow', 'Byte'), # dito for yellow
    ('black', 'Byte') # dito for black
])


Structure.add("TColorInfo", [
    ('ColorNum', 'SmallInt'), # Color number. This number is
                              #  used in the symbols when referring a color.
    ('Reserved', 'SmallInt'),
    ('Color', 'TCmyk'), # Color value. The structure is explained below.
    ('ColorName', ('String', 31)),   # Description of the color
    ('SepPercentage', ('Byte', 32))
                              # Definition how the color appears in the different spot
                              # color separations. 0..200: 2 times the separation
                              # percentage as it appears in the Color dialog box (to allow half percents) 255: the color does not
                              # appear in the corresponding color separation (empty field in the color dialog box)
])


Structure.add("TColorSep", [
    ('SepName', ("String", 15)), # Name of the color separation
    ('Color', 'TCmyk'), # 0 in OCAD 6, CMYK value of the separation in OCAD 7.
                                 # This value is only used in the AI (Adobe Illustrator) export
    ('RasterFreq', 'SmallInt'), # 10 times the halfton frequency as it appears in the Color Separation dialog box.
    ('RasterAngle', 'SmallInt') # 10 times the halftone angle as it appears in the Color Separation dialog box.
])


Structure.add("TSymHeader", [
    ('nColors', 'SmallInt'),         # Number of colors defined
    ('nColorSep', 'SmallInt'),       # Number or color separations defined
    ('CyanFreq', 'SmallInt'),        # Halftone frequency of the
                              #  Cyan color separation. This
                              #  is 10 times the value entered
                              #  in the CMYK Separations dialog box.
    ('CyanAng', 'SmallInt'),         # Halftone angle of the cyan
                              #  color separation. This is 10 times
                              #  the value entered in the CMYK
                              #  separations dialog box.
    ('MagentaFreq', 'SmallInt'),     # dito for magenta
    ('MagentaAng', 'SmallInt'),      # dito for magenta
    ('YellowFreq', 'SmallInt'),     # dito for yellow
    ('YellowAng', 'SmallInt'),      # dito for yellow
    ('BlackFreq', 'SmallInt'),       # dito for black
    ('BlackAng', 'SmallInt'),        # dito for black
    ('Res1', 'SmallInt'),
    ('Res2', 'SmallInt'),
    ('aColorInfo', ('TColorInfo', 256)), # the TColorInfo structure is explained below
    ('aColorSep', ('TColorSep', 32)) # the TColorSep structure is
                              #  explained below. Note that only
                              #  24 color separations are allowed.
                              #  The rest is reserved for future use.
])
    

Structure.add("TGpsAdjPoint", [
  ('lpMap', 'TCord'), #        Point on the map. All flag bits are set to 0
  ('Lat', 'Double'),      #        Latitude reported by the GPS receiver in this point (degrees)
  ('Long', 'Double'),     #        Longitude reported by the GPS receiver in this point (degrees)
  ('Name' , ('String', 15))  #        name of the adjustment point as it appears in the Adjust GPS dialog box
])

Structure.add("TZoomRec", [
  ('Zoom', 'Double'), #   Zoom magnification as it appears in the View menu and in the status bar
  ('Offset', 'TCord'),  #  of the center of the screen. All flag bits are set to 0
])

    
Structure.add("TStp", [
  ('Offset', 'TCord'),    #         Coordinate of the center
                   #            of the screen when the file was
                   #            last saved. All flag bits
                   #            are set to 0
  ('rGridDist', 'Double'),  #         Grid distance for paper paper coordinates in mm
  ('WorkMode', 'SmallInt'), #       Mode when last the file was
                     #          last saved
                     #            5: freehand
                     #            6: straight
                     #            7: rectangular
                     #            8: circle
                     #            9: ellipse
                     #            10: curve
                     #            11: edit point
                     #            12: edit object
  ('LineMode', 'SmallInt'), #       drawing mode when the file was
                     #          last saved
                     #            5: freehand
                     #            6: straight
                     #            7: rectangular
                     #            8: circle
                     #            9: ellipse
                     #            10: curve
  ('EditMode', 'SmallInt'), #       edit mode when the file was
                     #          last saved
                     #            11: edit point
                     #            12: edit object
  ('ActSym', 'SmallInt'),   #       selected symbol the file was
                     #          last saved
  ('MapScale', 'Double'),   #       Map scale

  ('RealWorldOfsX', 'Double'),  #    Horizontal offset of real
                         #      world coordinates in meters
  ('RealWorldOfsY', 'Double'),  #    Vertical offset of real
                         #      world coordinates in meters
  ('RealWorldAngle', 'Double'), #    Angle of real world coordinates
                         #      in degrees
  ('RealWorldGrid', 'Double'),  #    Grid distance of real world
                         #      coordinates in meters
  ('GpsAngle', 'Double'),       #    Angle of the GPS adjustment as
                         #      displayed in the Adjust GPS
                         #      dialog box
  ('aGpsAdjust', ('TGpsAdjPoint', 12)),                         #    GPS adjustment points, this
                         #     structure is defined below
  ('nGpsAdjust', 'LongInt'),    #   number of GPS adjustment points
  ('DraftScaleX', 'Double'),    #   Horizontal draft scale, not used in OCAD 8
  ('DraftScaleY', 'Double'),    #   Vertical draft scale, not uses in OCAD 8
  ('TempOffset', 'TCord'),     #   Template offset. This defines
                         #    the coordinates where the center
                         #    of the template is displayed, not used in OCAD 8
  ('TemplateFileName', ('String', 255)),
                         #   file name of the template, not used in OCAD 8
  ('TemplateEnabled', 'WordBool'), # true if a template is opened, not used in OCAD 8
  ('TempResol', 'SmallInt'),    #   resolution of the template file
                         #    in DPI, not used in OCAD 8
  ('rTempAng', 'Double'),       #   Angle of the adjusted template, 
                         #    not used in OCAD 8
  ('Reserved1', 'TCord'),

  ('Reserved2', 'Double'),

  ('PrLowerLeft', 'TCord'),     #   lower left corner of the print
                         #      window. All Flag bits are set
                         #      to 0
  ('PrUpperRight', 'TCord'),    #   upper right corner of the print
                         #      window. All Flag bits are set
                         #      to 0
  ('PrGrid', 'WordBool'),       #   true if Print grid is activated
                         #      in the Print dialog box
  ('PrGridColor', 'SmallInt'),  #   Grid color selected in the
                         #      Print dialog box
  ('PrOverlapX', 'SmallInt'),   #   Horizontal overlap as defined
                         #      in the Print Window dialog box
                         #      unit is 0.01 mm
  ('PrOverlapY', 'SmallInt'),   #   Vertical overlap as defined
                         #      in the Print Window dialog box
                         #      unit is 0.01 mm
  ('PrintScale', 'Double'),     #   Print scale
  ('PrIntensity', 'SmallInt'),  #   Intensity as defined in the
                         #      Printing Options dialog box
  ('PrLineWidth', 'SmallInt'),  #   Line Width as defined in the
                         #      Printing Options dialog box
  ('PrReserved', 'WordBool'),
  ('PrStdFonts', 'WordBool'),   #   OCAD 6: true if Standard fonts as
                         #         PostScript fonts is activated
                         #         in the EPS Properties dialog box
                         #   OCAD 7/8: not used
  ('PrReserved2', 'WordBool'),
  ('PrReserved3', 'WordBool'),

  ('PartialLowerLeft', 'TCord'),#   lower left corner of Export
                         #      Partial map window. All flag bits
                         #      are set to 0
  ('PartialUpperRight', 'TCord'),#  upper right corner of the Export
                         #      Partial map window. All flag bits
                         #      are set to 0
  ('Zoom', 'Double'),           #   Zoom magnification as it appears
                         #      in the View menu and in the
                         #      status bar
  ('ZoomHist', ('TZoomRec', 9)),                         #   Last 8 Zoom magnification for use
                         #      in the Zoom out command. TZoomRec
                         #      is explained below.
  ('nZoomHist', 'LongInt'),     #   number of magnificiations in
                         #      ZoomHist
#---------------------------------------------------------------------
#                               OCAD 6: the setup ends here
#                               the following fields exist
#                               in OCAD 7,8 only
#---------------------------------------------------------------------
    ('RealWorldCord', 'WordBool'),#   true if real world coordinates
                         #      are to be displayed
    ('FileName', ('String', 255)),#   used internally in temporary files.
                         #      The name of the original file
                         #      is stored here
    ('HatchAreas', 'WordBool'), #     true if Hatch areas is active
    ('DimTemp', 'WordBool'),    #     true if Dim template is active
    ('HideTemp', 'WordBool'),   #     true if Hide template is active

    ('TempMode', 'SmallInt'),   #     template mode
                         #        0: in the background
                         #        1: above a color
    ('TempColor', 'SmallInt')  #     the color if template mode is 1
])


Structure.add("TIndex8", [
  ('LowerLeft', 'TCord'), # {lower left corner of a rectangle covering the entire object. All flag bits are set to 0}
  ('UpperRight', 'TCord'), # {upper right corner of a rectangle covering the entire object. All flag bits are set to 0}
  ('Pos', 'LongInt'), # {file position of the object} - TElementDescriptor8
  ('Len', 'SmallInt'), # {OCAD 6 and 7: size of the object in the file in bytes
                   #            OCAD 8: number of coordinate pairs, the size of
                   #              the object in the file is then calculated by:
                   #                 32 + 8*Len
                   #            Note: this is reserved space in the file, the
                   #              effective length of the object may be shorter}
  ('Sym', 'SmallInt')    #         {10 times the symbol number. Deleted objects are marked with Sym=0}
])


Structure.add("TIndex9", [
  ('LowerLeft', 'TCord'), # {lower left corner of a rectangle covering the entire object. All flag bits are set to 0}
  ('UpperRight', 'TCord'),  # {upper right corner of a rectangle covering the entire object. All flag bits are set to 0}
  ('Pos', 'LongInt'), # file position of the object -> TElement
  ('Len', 'LongInt'),
  ('Sym', 'LongInt'),
  ('ObjType', 'Byte'), # 1 = Point object
                     # 2 = Line object
                     # 3 = Area object
                     # 4 = Unformatted text
                     # 5 = Formatted text
                     # 6 = Line text
                     # 7 = Rectangle object
  ('EncryptedMode', 'Byte'), # OCAD10 only
  ('Status', 'Byte'),  # 0 = deleted (not undo) (eg from symbol editor or cs)
                     # 1 = normal
                     # 2 = hidden
                     # 3 = deleted for undo
  ('ViewType', 'Byte'),    # 0 = normal object
                     # 1 = course setting object
                     # 2 = modified preview object
                     # 3 = unmodified preview object
                     # 4 = temporary object (symbol editor or control description)
                     # 10 = DXF import, GPS import
  ('Color', 'SmallInt'),  # symbolized objects: color number
                # graphic object: color number
	            # image object: CYMK color of object
  ('Res1', 'SmallInt'),
  ('ImpLayer', 'SmallInt'), # Layer number of imported objects; 0 means no layer number
  ('Res2', 'SmallInt')
])

  
Structure.add("TElementDescriptor8", [
  ('Symb', 'SmallInt'), # 10 times the symbol number
                      # image object= -3 (imported from ai or pdf,
                      # no symbol assigned)
                      # graphic object = -2 (OCAD objects converted to
                      # graphics)
                      # imported object = -1 (imported, no symbol assigned)
  ('Otp', 'Byte'),  #         object type
                      #           1: point object
                      #           2: line or line text object
                      #           3: area object
                      #           4: unformatted text object
                      #           5: formatted text object
                      #              or rectangle object
  ('Unicode', 'Byte'),       #      OCAD 6/7: must be 0
                      #          OCAD 8: 1 if the text is Unicode
  ('nItem', 'SmallInt'),     #      number of coordinates in the Poly array
  ('nText', 'SmallInt'),     #      number of coordinates in the
                      #         Poly array used for storing text
                      #         nText is > 0 for
                      #           - line text objects
                      #           - unformatted text objects
                      #           - formatted text objects
                      #         for all other objects it is 0
  ('Ang', 'SmallInt'),       #      Angle, unit is 0.1 degrees
                      #         used for
                      #           - point object
                      #           - area objects with structure
                      #           - unformatted and formatted
                      #             text objects
                      #           - rectangle objects
  ('Res1', 'SmallInt'),
  ('ResHeight', 'LongInt'),  #      reserved for future use to store a height information
  ('ResId', ('String', 15))  #    reserved
 ])

 
Structure.add("TElementDescriptor9", [
   ('Symb', 'LongInt'),	      # Symbol number. This is 1000 times the integer part of
		      #  the number + the fractional part
                      #   image object= -3 (imported from ai or pdf,
                      #   no symbol assigned)
                      #   graphic object = -2 (OCAD objects converted to
                      #   graphics)
                      #   imported object = -1 (imported, no symbol assigned)
  ('Otp', 'Byte'),           # Object type
                      #           1: point object
                      #           2: line or line text object
                      #           3: area object
                      #           4: unformatted text object
                      #           6: Line text symbol
                      #           7: Rectangle symbol
  ('Res0', 'Byte'),          #  { OCAD 9: reserved for Firebird 
  ('Ang', 'SmallInt'),       #  Angle, unit is 0.1 degrees
                      #         used for
                      #           - point object
                      #           - area objects with structure
                      #           - unformatted and formatted
                      #             text objects
                      #           - rectangle objects
  ('nItem', 'LongInt'),      #  number of coordinates in the Poly array
  ('nText', 'SmallInt'),     #  number of coordinates in the
                      #         Poly array used for storing text
                      #         nText is > 0 for
                      #           - line text objects
                      #           - unformatted text objects
                      #           - formatted text objects
                      #         for all other objects it is 0
  ('Res1', 'SmallInt'),
  ('Col', 'LongInt'),        # image object: CYMK color of object
                      # graphic object: color number
  ('LineWidth', 'SmallInt'), # line with for image and graphic object
  ('DiamFlags', 'SmallInt'), # flages: LineStyle by lines
  ('Res2', 'Double'),        # not used
  ('Mark', 'Byte'),          # OCAD10: Internal used
  ('Res3', 'Byte'),          # not used
  ('Res4', 'SmallInt'),     # not used
  ('Height', 'LongInt')     # OCAD10: Height [mm] (only for point, line and area objects)
])


Structure.add("TBaseSym8", [
    ('Size', 'SmallInt'),             # Size of the symbol in bytes. This
                               # depends on the type and the
                               # number of subsymbols.
    ('Sym', 'SmallInt'),             # Symbol number.
    ('Otp', 'SmallInt'),              # Object type.
    ('SymTp', 'Byte'),                # Symbol type
                               #  1: for Line text and text
                               #     symbols
                               #  0: for all other symbols}
    ('Flags', 'Byte'),                # OCAD 6/7: must be 0
                               # OCAD 8: bit flags
                               #   1: not oriented to north (inverted for
                               #      better compatibility)
                               #   2: Icon is compressed}
    ('Extent', 'SmallInt'),           # Extent how much the rendered
                               #  symbols can reach outside the
                               #  coordinates of an object with
                               #  this symbol.
                               #  For a point object it tells
                               #  how far away from the coordinates
                               #  of the object anything of the
                               #  point symbol can appear.
    ('Selected', 'Byte'),             # Symbol is selected in the symbol
                               #  box
    ('Status', 'Byte'),               # Status of the symbol
                               #  0: Normal
                               #  1: Protected
                               #  2: Hidden
    ('Res2', 'SmallInt'),
    ('Res3', 'SmallInt'),
    ('FilePos', 'LongInt'),           # File position, not used in the
                               #  file, only when loaded in
                               #  memory. Value in the file is
                               #  not defined.
    ('Cols', ('Byte', 32)),             # Set of the colors used in this
                               #  symbol.
                               # TColors is an array of
                               #  32 bytes, where each bit
                               #  represents 1 of the 256 colors.
                               #    TColors = set of 0..255;
                               # The color with the number 0 in
                               #  the color table appears as the
                               #  lowest bit in the first ('', 'Byte'),of
                               #  the structure.
    ('Description', ('String', 31)),  # The description of the symbol
    ('IconBits', ('Byte', 264))        # the icon can be uncompressed (16-bit colors)
                               #  or compressed (256 color palette) depending
                               #  on the Flags field.
                               #  In OCAD 6/7 it is always uncompressed
])


"""
Structure.add("TSymU8", [
  ('P', 'TPointSym8'),
  ('L', 'TLineSym8'),
  ('LT', 'TLTextSym8'),
  ('A', 'TAreaSym8'),
  ('T', 'TTextSym8'),
  ('R', 'TRectSym8')
])
"""

Structure.add("TPointSym8", [
    ('DataSize', 'SmallInt'),           # number of coordinates (each 8 bytes)
                               # which follow this structure,
                               # each object header counts as
                               # 2 Coordinates (16 bytes).
                               # The maximum value is 512}
    ('Reserved', 'SmallInt')
]) # TPointSym8


Structure.add("TLineSym8", [
    ('LineColor', 'SmallInt'),       # Line color
    ('LineWidth', 'SmallInt'),       # Line width
    ('LineEnds', 'WordBool'),        # true if Round line ends is checked
    ('DistFromStart', 'SmallInt'),   # Distance from start
    ('DistToEnd', 'SmallInt'),       # Distance to the end
    ('MainLength', 'SmallInt'),      # Main length a
    ('EndLength', 'SmallInt'),       # End length b
    ('MainGap', 'SmallInt'),         # Main gap C
    ('SecGap', 'SmallInt'),          # Gap D
    ('EndGap', 'SmallInt'),          # Gap E
    ('MinSym', 'SmallInt'),          # -1: at least 0 gaps/symbols
                              #  0: at least 1 gap/symbol
                              #  1: at least 2 gaps/symbols
                              #  etc.
                              #  for OCAD 6 only the values 0 and 1 are
                              #  allowed
    ('nPrimSym', 'SmallInt'),        # No. of symbols
    ('PrimSymDist', 'SmallInt'),     # Distance
    ('DblMode', 'Word'),             # Mode (Double line page)
    ('DblFlags', 'Word'),            # low order bit is set if
                              # Fill is checked
    ('DblFillColor', 'SmallInt'),    # Fill color
    ('DblLeftColor', 'SmallInt'),    # Left line/Color
    ('DblRightColor', 'SmallInt'),   # Right line/Color
    ('DblWidth', 'SmallInt'),        # Width
    ('DblLeftWidth', 'SmallInt'),    # Left line/Line width
    ('DblRightWidth', 'SmallInt'),   # Right line/Line width
    ('DblLength', 'SmallInt'),       # Dashed/Distance a
    ('DblGap', 'SmallInt'),          # Dashed/Gap
    ('DblRes', ('SmallInt', 3)),
    ('DecMode', 'Word'),             # Decrease mode
                              #   0: off
                              #   1: decreasing towards the end
                              #   2: decreasing towards both ends
    ('DecLast', 'SmallInt'),         # Last symbol
    ('DecRes', 'SmallInt'),          # Reserved
    ('FrColor', 'SmallInt'),         # OCAD 6: reserved
                              # OCAD 7/8: color of the framing line
    ('FrWidth', 'SmallInt'),         # OCAD 6: reserved
                              # OCAD 7/8: Line width of the framing line
    ('FrStyle', 'SmallInt'),         # OCAD 6: reserved
                              # OCAD 7/8: Line style of the framing line
                              #   0: flat cap/bevel join
                              #   1: round cap/round join
                              #   4: flat cap/miter join
    ('PrimDSize', 'SmallInt'),       # number or coordinates (8 bytes)
                              # for the Main symbol A which
                              # follow this structure
                              # Each symbol header counts as
                              # 2 coordinates (16 bytes).
                              # The maximum value is 512.
    ('SecDSize', 'SmallInt'),        # number or coordinates (8 bytes)
                              # for the Secondary symbol which
                              # follow the Main symbol A
                              # Each symbol header counts as
                              # 2 coordinates (16 bytes).
                              # The maximum value is 512.
    ('CornerDSize', 'SmallInt'),     # number or coordinates (8 bytes)
                              # for the Corner symbol which
                              # follow the Secondary symbol
                              # Each symbol header counts as
                              # 2 coordinates (16 bytes).
                              # The maximum value is 512.
    ('StartDSize', 'SmallInt'),      # number or coordinates (8 bytes)
                              # for the Start symbol C which
                              # follow the Corner symbol
                              # Each symbol header counts as
                              # 2 coordinates (16 bytes).
                              # The maximum value is 512.
    ('EndDSize', 'SmallInt'),        # number or coordinates (8 bytes)
                              # for the End symbol D which
                              # follow the Start symbol C
                              # Each symbol header counts as
                              # 2 coordinates (16 bytes).
                              # The maximum value is 512.
    ('Reserved', 'SmallInt')
])


Structure.add("TLTextSym8", [
    ('FontName', ('String', 31)), # TrueType font
    ('FontColor', 'SmallInt'),    # Color
    ('FontSize', 'SmallInt'),     # 10 times the value entered in Size
    ('Weight', 'SmallInt'),       # Bold as used in the Windows GDI
                              #  400: normal
                              #  700: bold
    ('Italic', 'Byte'),           # true if Italic is checked
    ('CharSet', 'Byte'),          # OCAD 6/7: must be 0
                              # OCAD 8: CharSet of the text, if the text is
                              #   not Unicode
    ('CharSpace', 'SmallInt'),    # Char. spacing
    ('WordSpace', 'SmallInt'),    # Word spacing
    ('Alignment', 'SmallInt'),    # Alignment
                              #  0: Left
                              #  1: Center
                              #  2: Right
                              #  3: All line
    ('FrMode', 'SmallInt'),       # Framing mode
                              #  0: no framing
                              #  1: framing with a framing font
                              #  2: OCAD 7/8 only: framing with a line
                              # Note this feature is called
                              # "Second font" in OCAD 6 but
                              # "Framing" in OCAD 7
    ('FrName', ('String', 31)),   # OCAD 6/7: TrueType font (Second/Framing font)
                              # OCAD 8: not used
    ('FrColor', 'SmallInt'),      # Color (Second/Framing font)
    ('FrSize', 'SmallInt'),       # OCAD 6/7: Size (Second/Framing font)
                              # OCAD 8: Framing width
    ('FrWeight', 'SmallInt'),     # OCAD 6/7: Bold (Second/Framing font)
                              #  as used in the Windows GDI
                              #    400: normal
                              #    700: bold
                              #  OCAD 8: not used
    ('FrItalic', 'WordBool'),     # OCAD 6/7: true if Italic is checked
                              #  (Second/Framing font)
                              # OCAD 8: not used
    ('FrOfX', 'SmallInt'),        # OCAD 6/7: Horizontal offset
                              # OCAD 8: not used
    ('FrOfY', 'SmallInt')        # OCAD 6/7: Vertical offset
                              # OCAD 8: not used
])


Structure.add("TAreaSym8", [
    ('AreaFlags', 'Word'),        # reserved
    ('FillOn', 'WordBool'),       # true if Fill background is
                              # checked
    ('FillColor', 'SmallInt'),    # Fill color
    ('HatchMode', 'SmallInt'),    # Hatch mode
                              #   0: None
                              #   1: Single hatch
                              #   2: Cross hatch
    ('HatchColor', 'SmallInt'),   # Color (Hatch page)
    ('HatchLineWidth', 'SmallInt'),  # Line width
    ('HatchDist', 'SmallInt'),    # Distance
    ('HatchAngle1', 'SmallInt'),  # Angle 1
    ('HatchAngle2', 'SmallInt'),  # Angle 2
    ('HatchRes', 'SmallInt'),
    ('StructMode', 'SmallInt'),   # Structure
                              #   0: None
                              #   1: aligned rows
                              #   2: shifted rows
    ('StructWidth', 'SmallInt'),  # Width
    ('StructHeight', 'SmallInt'), # Height
    ('StructAngle', 'SmallInt'),  # Angle
    ('StructRes', 'SmallInt'),
    ('DataSize', 'SmallInt')     # number of coordinates (each 8 bytes)
                              # which follow this structure,
                              # each object header counts as
                              # 2 Coordinates (16 bytes).
                              # The maximum value is 512.
]) # TAreaSym8


Structure.add("TTextSym8", [
    ('FontName', ('String', 31)),    # TrueType font
    ('FontColor', 'SmallInt'),       # Color
    ('FontSize', 'SmallInt'),        # 10 times the size in pt
    ('Weight', 'SmallInt'),          # Bold as used in the Windows GDI
                              #   400: normal
                              #   700: bold
    ('Italic', 'Byte'),          # true if Italic is checked
    ('CharSet', 'Byte'),             # OCAD 6/7: must be 0
                              # OCAD 8: CharSet of the text, if the text is
                              #   not Unicode
    ('CharSpace', 'SmallInt'),       # Char. spacing
    ('WordSpace', 'SmallInt'),       # Word spacing
    ('Alignment', 'SmallInt'),       # Alignment
                              #   0: Left
                              #   1: Center
                              #   2: Right
                              #   3: Justified
    ('LineSpace', 'SmallInt'),       # Line spacing
    ('ParaSpace', 'SmallInt'),       # Space after Paragraph
    ('IndentFirst', 'SmallInt'),     # Indent first line
    ('IndentOther', 'SmallInt'),     # Indent other lines
    ('nTabs', 'SmallInt'),           # number of Tabulators
    ('Tabs', ('LongInt', 32)),        # Tabulators
    ('LBOn', 'WordBool'),            # true if Line below On is checked
    ('LBColor', 'SmallInt'),         # Line color (Line below)
    ('LBWidth', 'SmallInt'),         # Line width (Line below)
    ('LBDist', 'SmallInt'),          # Distance from text
    ('Res4', 'SmallInt'),
    ('FrMode', 'SmallInt'),          # Framing mode
                              #   0: no framing
                              #   1: framing with a framing font
                              #   2: OCAD 7/8 only: framing with a line
                              # Note this feature is called
                              # "Second font" in OCAD 6 but
                              # "Framing" in OCAD 7/8
    ('FrName', ('String', 31)),      # OCAD 6/7: TrueType font (Second/Framing font)
                              # OCAD 8: not used
    ('FrColor', 'SmallInt'),         # Color (Second/Framing font)
    ('FrSize', 'SmallInt'),          # OCAD 6/7: Size (Second/Framing font)
                              # OCAD 8: framing width
    ('FrWeight', 'SmallInt'),        # OCAD 6/7: Bold (Second/Framing font)
                              #  400: normal
                              #  700: bold
                              # OCAD 8: not used
    ('FrItalic', 'WordBool'),        # true if Second/Framing font Italic
                              # is checked
    ('FrOfX', 'SmallInt'),           # OCAD 6/7: Horizontal offset
                              # OCAD 8: not used
    ('FrOfY', 'SmallInt'),           # OCAD 6/7: Vertical offset
                              # OCAD 8: not used
]) # TTextSym8


Structure.add("TRectSym8", [
    ('LineColor', 'SmallInt'),       # Line color
    ('LineWidth', 'SmallInt'),       # Line width
    ('Radius', 'SmallInt'),          # Corner radius
    ('GridFlags', 'Word'),           # Flags
                              #   1: Grid On
                              #   2: Numbered from the bottom
    ('CellWidth', 'SmallInt'),       # Cell width
    ('CellHeight', 'SmallInt'),      # Cell height
    ('ResGridLineColor', 'SmallInt'),
    ('ResGridLineWidth', 'SmallInt'),
    ('UnnumCells', 'SmallInt'),      # Unnumbered Cells
    ('UnnumText', ('String', 3)),    # Text in unnumbered Cells
    ('GridRes2', 'SmallInt'),
    ('ResFontName', ('String', 31)),
    ('ResFontColor', 'SmallInt'),
    ('ResFontSize', 'SmallInt'),
    ('ResWeight', 'SmallInt'),
    ('ResItalic', 'WordBool'),
    ('ResOfsX', 'SmallInt'),
    ('ResOfsY', 'SmallInt'),
]) # TRectSym8


Structure.add("TBaseSym9", [
    ('Size', 'LongInt'),              # Size of the symbol in bytes. This depends on the type.
                               # Coordinates following the symbol are included.
    ('Sym', 'LongInt'),               # Symbol number. This is 1000 times the integer part of
                               # the number + the fractional part "right adjusted"
                               # examples:
                               #   101.5 is stored as 101005
                               #   203.45 is stored as 203045
                               #   203.145 is stored as 203145
    ('Otp', 'Byte'),                  # Object type
                               #   1: Point symbol
                               #   2: Line symbol
                               #   3: Area symbol
                               #   4: Text symbol
                               #   6: Line text symbol
                               #   7: Rectangle symbol
    ('Flags', 'Byte'),                # 1: rotatable symbol (not oriented to north)
                               # 4: belongs to favorites
    ('Selected', 'Byte'),             # Symbol is selected in the symbol box
    ('Status', 'Byte'),               # Status of the symbol
                               #   0: Normal
                               #   1: Protected
                               #   2: Hidden
                               #  16: selected
    ('DrawingTool', 'Byte'),          # Preferred drawing tool
                               #   0: off
                               #   1: Curve mode
                               #   2: Ellipse mode
                               #   3: Circle mode
                               #   4: Rectangular line mode
                               #   5: Rectangular area mode
                               #   6: Straight line mode
                               #   7: Freehand mode
                               #   8: Numeric mode
    ('CsMode', 'Byte'),               # Course setting mode
                               #   0: Not used for course setting
                               #   1: course symbol
                               #   2: control description symbol
    ('CsObjType', 'Byte'),            # Course setting object type
                               #   0: Start symbol (Point symbol)
                               #   1: Control symbol (Point symbol)
                               #   2: Finish symbol (Point symbol)
                               #   3: Marked route (Line symbol)
                               #   4: Control description symbol (Point symbol)
                               #   5: Course Titel (Text symbol)
                               #   6: Start Number (Text symbol)
                               #   7: Variant (Text symbol)
                               #   8: Text block (Text symbol)
    ('CsCdFlags', 'Byte'),            # Course setting control description flags
                               #   a combination of the flags
			       #   64: available in column B
                               #   32: available in column C
                               #   16: available in column D
                               #   8: available in column E
                               #   4: available in column F
                               #   2: available in column G
                               #   1: available in column H
    ('Extent', 'LongInt'),            # Extent how much the rendered symbols can reach outside the
                               # coordinates of an object with this symbol. For a point
                               # object it tells how far away from the coordinates of the
                               # object anything of the point symbol can appear.
    ('FilePos', 'LongInt'),           # Used internally. Value in the file is not defined.
    ('Group', 'SmallInt'),            # Group ID in the symbol tree. Lower and higher 8 bit are 
                               # used for 2 different symbol trees.
    ('nColors', 'SmallInt'),          # Number of colors of the symbol max. 14
                               #   -1: the number of colors is > 14
    ('Colors', ('SmallInt', 14)),       # number of colors of the symbol
    ('Description', ('String', 31)),  # Description text
    ('IconBits', ('Byte', 484))        # Each ('', 'Byte'),represents a pixel of the icon in a
                               # 256 color palette (icon 22x22 pixels)
]) # class TBaseSym9


Structure.add("TAreaSym9", [
    ('BorderSym', 'LongInt'),        # Symbolnumber  for border line activated if BorderOn is true
    ('FillColor', 'SmallInt'),       # Fill color activated if FillOn is true
    ('HatchMode', 'SmallInt'),       # Hatch mode
                              #   0: None
                              #   1: Single hatch
                              #   2: Cross hatch
    ('HatchColor', 'SmallInt'),      # Color (Hatch page)
    ('HatchLineWidth', 'SmallInt'),  # Line width
    ('HatchDist', 'SmallInt'),       # Distance
    ('HatchAngle1', 'SmallInt'),     # Angle 1
    ('HatchAngle2', 'SmallInt'),     # Angle 2
    ('FillOn', 'Byte'),              # Fill is activated
    ('BorderOn', 'Byte'),            # Border line is activated
    ('StructMode', 'SmallInt'),      # Structure
                              #   0: None
                              #   1: aligned rows
                              #   2: shifted rows
    ('StructWidth', 'SmallInt'),     # Width
    ('StructHeight', 'SmallInt'),    # Height
    ('StructAngle', 'SmallInt'),     # Angle
    ('Res', 'SmallInt'),             # Not used
    ('DataSize', 'Word')            # number of coordinates (each 8 bytes) which follow this
                              # structure, each object header counts as 2 Coordinates
                              # (16 bytes)
]) # TAreaSym9


Structure.add("TLineSym9", [
   ('LineColor', 'SmallInt'),       # Line color
   ('LineWidth', 'SmallInt'),       # Line width
   ('LineStyle', 'SmallInt'),       # Line style
                              #   0: Bevel joins/flat caps
                              #   1: Round joins/round caps
                              #   4: Miter joins/flat caps
   ('DistFromStart', 'SmallInt'),   # Distance from start
   ('DistToEnd', 'SmallInt'),       # Distance to the end
   ('MainLength', 'SmallInt'),      # Main length a
   ('EndLength', 'SmallInt'),       # End length b
   ('MainGap', 'SmallInt'),         # Main gap C
   ('SecGap', 'SmallInt'),          # Gap D
   ('EndGap', 'SmallInt'),          # Gap E
   ('MinSym', 'SmallInt'),          # -1: At least 0 gaps/symbols
                              #  0: At least 1 gap/symbol
                              #  1: At least 2 gaps/symbols
                              #  etc.
   ('nPrimSym', 'SmallInt'),        # Number of symbols
   ('PrimSymDist', 'SmallInt'),     # Distance
   ('DblMode', 'Word'),            # Mode (Double line page)
   ('DblFlags', 'Word'),            # Double line flags
                              #    1: Fill color on
                              #    2: Background color on
   ('DblFillColor', 'SmallInt'),    # Fill color
   ('DblLeftColor', 'SmallInt'),    # Left line/Color
   ('DblRightColor', 'SmallInt'),   # Right line/Color
   ('DblWidth', 'SmallInt'),        # Width
   ('DblLeftWidth', 'SmallInt'),    # Left line/Line width
   ('DblRightWidth', 'SmallInt'),   # Right line/Line width
   ('DblLength', 'SmallInt'),       # Dashed/Distance a
   ('DblGap', 'SmallInt'),          # Dashed/Gap
   ('Res0', 'SmallInt'),     	      # Not used
   ('Res1', ('SmallInt', 2)),         # Not used
   ('DecMode', 'Word'),             # Decrease mode
                              #   0: Off
                              #   1: Decreasing towards the end
                              #   2: Decreasing towards both ends
   ('DecLast', 'SmallInt'),         # Last symbol
   ('Res', 'SmallInt'),             # Not used
   ('FrColor', 'SmallInt'),         # Color of the framing line
   ('FrWidth', 'SmallInt'),         # Line width of the framing line
   ('FrStyle', 'SmallInt'),         # Line style of the framing line
                              #   0: Bevel joins/flat caps
                              #   1: Round joins/round caps
                              #   4: Miter joins/flat caps
                              # PointedEnd := LineStyle and 2 > 0;
    ('PrimDSize', 'Word'),           # Number or coordinates (8 bytes) for the Main symbol A which
                               # follow this structure.
                               # Each symbol header counts as 2 coordinates (16 bytes).
    ('SecDSize', 'Word'),            # Number or coordinates (8 bytes) for the Secondary symbol
                               # which follow the Main symbol A.
                               # Each symbol header counts as 2 coordinates (16 bytes).
    ('CornerDSize', 'Word'),         # Number or coordinates (8 bytes) for the Corner symbol
                               # which follow the Secondary symbol.
                               # Each symbol header counts as 2 coordinates (16 bytes).
    ('StartDSize', 'Word'),          # Number or coordinates (8 bytes) for the Start symbol C
                               # which follow the Corner symbol.
                               # Each symbol header counts as 2 coordinates (16 bytes).
    ('EndDSize', 'Word'),            # Number or coordinates (8 bytes) for the End symbol D
                               # which follow the Start symbol C.
                               # Each symbol header counts as 2 coordinates (16 bytes).
   ('Reserved', 'SmallInt')        # Not used
]) # TLineSym9


Structure.add("TPointSym9", [
    ('DataSize', 'Word'),             # number of coordinates (each 8 bytes) which
                               # follow this structure, each object header
                               # counts as 2 Coordinates (16 bytes)
    ('Reserved', 'SmallInt')         # Not used
]) # TPointSym9


"""Same structure for 8-10, only max size of stPoly differ"""
Structure.add("TSymEltHeader", [
    ('stType', 'SmallInt'),           # type of the symbol element
                               #   1: line
                               #   2: area
                               #   3: circle
                               #   4: dot (filled circle)
    ('stFlags', 'Word'),              # Flags
                               #   1: line with round ends
    ('stColor', 'SmallInt'),          # color of the object. This is the number which appears in
                               # the colors dialog box
    ('stLineWidth', 'SmallInt'),      # line width for lines and circles unit 0.01 mm
    ('stDiameter', 'SmallInt'),       # Diameter for circles and dots. The line width is included
                               # one time in this dimension for circles.
    ('stnPoly', 'SmallInt'),          # number of coordinates
    ('stRes1', 'SmallInt'),           # Not used
    ('stRes2', 'SmallInt')           # Not used
    #, ('stPoly', ('TCord', 32768))       # coordinates of the symbol element, Ocad <= 8 - The maximum value is 512 (real size is determined by .stnPoly)
])


Structure.add("TTextSym9", [
    ('FontName', ('String', 31)),    # TrueType font
    ('FontColor', 'SmallInt'),      # Color
    ('FontSize', 'SmallInt'),       # 10 times the size in pt
    ('Weight', 'SmallInt'),         # Bold as used in the Windows GDI
                              #   400: normal
                              #   700: bold
    ('Italic', 'Byte'),             # true if Italic is checked
    ('Res0', 'Byte'),               # not used
    ('CharSpace', 'SmallInt'),      # Character spacing
    ('WordSpace', 'SmallInt'),      # Word spacing
    ('Alignment', 'SmallInt'),      # Alignment
			      #   0: Bottom Left        # until OCAD9: Left
                              #   1: Bottom Center      # until OCAD9: Center
                              #   2: Bottom Right       # until OCAD9: Right
                              #   3: Bottom Justified   # until OCAD9: Justified
                              #   4: Middle Left
                              #   5: Middle Center
                              #   6: Middle Right
                              #   8: Top Left
                              #   9: Top Center
                              #  10: Top Right
    ('LineSpace', 'SmallInt'),      # Line spacing
    ('ParaSpace', 'SmallInt'),      # Space after Paragraph
    ('IndentFirst', 'SmallInt'),    # Indent first line
    ('IndentOther', 'SmallInt'),    # Indent other lines
    ('nTabs', 'SmallInt'),          # number of tabulators for text symbol
    ('Tabs', ('LongInt', 32)),        # Tabulators
    ('LBOn', 'WordBool'),            # true if Line below On is checked
    ('LBColor', 'SmallInt'),        # Line color (Line below)
    ('LBWidth', 'SmallInt'),        # Line width (Line below)
    ('LBDist', 'SmallInt'),         # Distance from text
    ('Res1', 'SmallInt'),
    ('FrMode', 'Byte'),             # Framing mode
                              #   0: no framing
                              #   1: shadow framing
                              #   2: line framing
                              #   3: rectangle framing
    ('FrLineStyle', 'Byte'),        # Framing line style                             
                              #   0: default OCAD 8 Miter
                              #   2: ps_Join_Bevel
                              #   1: ps_Join_Round
                              #   4: ps_Join_Miter    	
    ('PointSymOn', 'Byte'),         # OCAD10: Point symbol is activated
    ('PointSym', 'LongInt'),         # OCAD10: Point Symbol for text symbol
                              #  activated if PointSymOn is true
    ('Res2', ('String', 18)),        # not used
    ('FrLeft', 'SmallInt'),         # Left border for rectangle framing
    ('FrBottom', 'SmallInt'),       # Bottom border for rectangle framing
    ('FrRight', 'SmallInt'),        # Right border for rectangle framing
    ('FrTop', 'SmallInt'),          # Top border for rectangle framing
    ('FrColor', 'SmallInt'),        # Framing color
    ('FrWidth', 'SmallInt'),        # Framing width for line framing
    ('Res3', 'SmallInt'),           # not used
    ('Res4', 'WordBool'),            # not used
    ('FrOfX', 'SmallInt'),          # Horizontal offset for shadow framing
    ('FrOfY', 'SmallInt')          # Vertical offset for shadow framing
]) # TTextSym9


Structure.add("TRectSym9", [
    ('LineColor', 'SmallInt'),       # Line color
    ('LineWidth', 'SmallInt'),       # Line width
    ('Radius', 'SmallInt'),          # Corner radius
    ('GridFlags', 'Word'),           # A combination of the flags
                              #   1: Grid On
                              #   2: Numbering On
                              #   4: Numbered from the bottom
    ('CellWidth', 'SmallInt'),       # Cell width
    ('CellHeight', 'SmallInt'),      # Cell height
    ('Res0', 'SmallInt'),            # Not used
    ('Res1', 'SmallInt'),            # Not used
    ('UnnumCells', 'SmallInt'),      # Unnumbered cells
    ('UnnumText', ('String', 3)),     # Text in unnumbered cells
    ('Res2', 'SmallInt'),       	  # Not used
    ('Res3', ('String', 31)),        # Not used
    ('Res4', 'SmallInt'),            # Not used
    ('FontSize', 'SmallInt'),        # OCAD10: Font size
    ('Res6', 'SmallInt'),            # Not used
    ('Res7', 'WordBool'),            # Not used
    ('Res8', 'SmallInt'),            # Not used
    ('Res9', 'SmallInt')            # Not used
]) # TRectSym9


Structure.add("TLTextSym9", [
    ('FontName', ('String', 31)),    # TrueType font
    ('FontColor', 'SmallInt'),       # Color
    ('FontSize', 'SmallInt'),        # 10 times the value entered in Size
    ('Weight', 'SmallInt'),          # Bold as used in the Windows GDI
                              #   400: normal
                              #   700: bold
    ('Italic', 'Byte'),              # True if Italic is checked
    ('Res0', 'Byte'),                # Not used
    ('CharSpace', 'SmallInt'),       # Character spacing
    ('WordSpace', 'SmallInt'),       # Word spacing
    ('Alignment', 'SmallInt'),       # Alignment
                              #   0: Bottom Left        # until OCAD9: Left
                              #   1: Bottom Center      # until OCAD9: Center
                              #   2: Bottom Right       # until OCAD9: Right
                              #   3: Bottom All line    # until OCAD9: Justified
                              #   4: Middle Left
                              #   5: Middle Center
                              #   6: Middle Right
                              #   7: Middle All line
                              #   8: Top Left
                              #   9: Top Center
                              #  10: Top Right
                              #  11: Top All line
    ('FrMode', 'Byte'),             # Framing mode
                              #   0: no framing
                              #   1: shadow framing
                              #   2: line framing
    ('Res1', 'Byte'),                # Not used
    ('Res2', ('String', 31)),        # Not used
    ('FrColor', 'SmallInt'),         # Framing color
    ('FrWidth', 'SmallInt'),         # Framing width for line framing
    ('Res3', 'SmallInt'),            # Not used
    ('Res4', 'WordBool'),            # Not used
    ('FrOfX', 'SmallInt'),           # Horizontal offset for shadow framing
    ('FrOfY', 'SmallInt')           # Vertical offset for shadow framing
]) # TLTextSym9


Structure.add("TStringIndex", [
    ('Pos', 'LongInt'),                        # file position of string
    ('Len', 'LongInt'),                        # length reserved for the string
    ('RecType', 'LongInt'),                # string typ number, if < 0 then deleted string
    ('ObjIndex', 'LongInt')                   # number of the object
]) # TStringIndex


StringIndexType = {
  "si_CsObject":1,		#course setting object
  "si_Course": 2,		#course
  "si_CsClass": 3,		#class. e.g. H12
  "si_DataSet": 4,		#dataset
  "si_DbObject": 5,		#object linked to a database
  "si_OimFile": 6,		# (OCAD Internet Maps file)
  "si_PrevObj": 7,		#(course preview)
  "si_Template": 8,		#template
  "si_Color": 9,			#(colors)
  "si_SpotColor": 10,		#(spot colors)
  "si_FileInfo": 11, 		#(file informations)
  "si_Zoom": 12,
  "si_ImpLayer": 13, 		#(imported dxf layer)
  "si_OimFind": 14, 		#(OCAD Internet Maps find settings)
  "si_SymTree": 15, 		#(symbol tree)
  "si_DisplayPar": 1024, 	#(display setting)
  "si_OimPar": 1025,		#(OCAD Internet Maps )
  "si_PrintPar": 1026,     	#Print parameters
  "si_CdPrintPar": 1027,   	#course description print parameters
  "si_TemplatePar": 1028,	#template parameters
  "si_EpsPar": 1029,		#EPS export parameters
  "si_ViewPar": 1030,		#(view settings)
  "si_CoursePar": 1031,		#course options
  "si_TiffPar": 1032,		#TIFF export parameters
  "si_TilesPar": 1033,		#parameters for exporting tiles
  "si_DbPar": 1034,		#database parameters
  "si_ExportPar": 1035,		#(export settings)
  "si_CourseSelPar": 1036,	# Not used
  "si_ExpCsTextPar": 1037,	#(export control description text)
  "si_ExpCsStatPar": 1038,	#(export control description)
  "si_ScalePar": 1039,		#(scales settings)
  "si_DbCreateObjPar": 1040,
  "si_XmlScriptPar": 1042
}

OGridsType = { # As in OCAD 9.6.3      |   Datum        |    Ellipsoid
  "og_None": 0,
  "og_Unknown": 1,
  "og_Albanian": 35,	# Albanian Grid, Zone 4   | Albanian 1987  | Krassovsky 1940
  "og_Australia": 20,	# Map Grid Australia 1994 | geocentric     |     GRS 1980
  "og_Austria":  3,	# Austria Bundesmeldenetz |    MGI         |  Bessel 1841
  "og_Belgium":  4,	# Belge Lambert 1972      | Belge 1972     | Hayford 1909
  "og_Bosnia": 36,	# Bosnia & Hertzegovina   |   ETRS89       |     GRS 1980
  "og_British":  5,	# British National        | OSGB 1936      |    Airy 1830
  "og_Bulgaria": 37,	# Bulgaria                |   ETRS89       |     GRS 1980
  "og_Croatia": 31,	# Croatia                 |  Croatia       |  Bessel 1841
  "og_Cyprus": 32,	# Cyprus                  |   ED50         | Hayford 1909
  "og_Czech": 46,	# Czech Republic          | S-JTSK/S-42    |  Bessel 1841/Krassovsky 1940
  "og_Denmark": 21,	# Denmark                 | ED50/ETRS89    | Hayford 1909/GRS 1980
  "og_Estonia": 27,
  "og_Finland":  6,	# Finnish grid            |  KKJ/ETRS89    | Hayford 1909/GRS 1980
  "og_FrLambert":  7,	# France Lamber           |    NTF         |  Clarke 1880
  "og_Germany":  8,	# German grid             | Potsdam/ETRS89 |  Bessel 1841/GRS 1980
  "og_Greek": 29,	# Greek grid              |   EGSA87       |     GRS 1980
  "og_Iceland": 38,	# Iceland HJ1955          |   ETRS89       | Hayford 1909
  "og_Irish":  9,	# Irish National grid     | 1965/1975 geo  | Airy Modified
  "og_Italy": 16,	# Italy                   | Rome 1940/ED50 | Hayford 1909
  "og_Japan": 11,	# Japan                   | Tokyo/JGD2000  |  Bessel 1841/GRS 1980
  "og_Latvia": 28,
  "og_Lithuania": 26,
  "og_Luxemburg": 33,
  "og_Malta": 39,
  "og_Monako": 40,
  "og_Netherlands": 41,	# Netherlands             |Amersfoort/ED50 |  Bessel 1841/Hayford 1909
  "og_NewZealand49": 24, # New Zealand grid 1949   |New Zealand 1949| Hayford 1909
  "og_NewZealand00": 19, # New Zealand grid 2000   |New Zealand 2000|     GRS 1980
  "og_NIreland": 34,
  "og_Norway": 12,	# Norway                  | NGO1948/ED50   |Bessel Modified/Hayford 1909
  "og_Poland": 48,
  "og_Portugal": 42,	# Portugal                | Datum 73/ED50  | Hayford 1909
  "og_Romania": 43,	# Romania                 |      S42       | Krassovsky 1940
  "og_SanMarino": 44,
  "og_Slovak": 47,	# Slovak Republic         | S-JTSK/S-42    |  Bessel 1841/Krassovsky 1940
  "og_Slovenia": 15,
  "og_SouthAfrica": 18,	# South Africa
  "og_SouthAfricaR": 23, # South Africa rotated
  "og_Spain": 30,	# Spain                   |  ED50(EST99)   | Hayford 1909
  "og_Sweden": 13,	# Sweden                  | RT90/SWEREF99  |  Bessel 1841/GRS 1980
  "og_SwedenREF99": 25,	# Sweden SWEREF99        !! Obsolete in 9.6
  "og_Turkey": 17,
  "og_Swiss": 14,	# Swiss grid              |  CH 1903       |  Bessel 1841
  "og_UTM":  2	# UTM                     |   WGS84        |     WGS 1984
}

#OGridsType = namedtuple("OGridsType", " ".join([key for key, value in OGridsType_data]))._make()


#OCADColor = namedtuple('OCADColor', ['name', 'cmyk', 'o'])
