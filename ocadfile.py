from struct import pack, unpack, calcsize, error
from collections import namedtuple

from ocad_structures import Structure, StringIndexType #, OCADColor

import os

OCAD_FILE_MAGIC = 0x0CAD
MAX_KNOWN_VERSION = 10

Point = 1
Line = 2
Area = 3
UnformattedText = 4
FormattedText = 5
# OCAD 9 only
LineText = 6
RectangleO = 7



class OcadfileException(Exception):
    """An exception to handle ocad file specific problems."""
    pass

class Reader:
    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            if isinstance(args[0], str):
                #self.StringsStorage = None # kad kelis kartus nenuskaitineti.
                self.load(args[0])
                return
        else:
            raise OcadfileException("Ocadfile Reader requires a ocadfile or file-like object.")
    
    # --- Strings ---
    def FirstString(self):
        self._idxStriPos = self.hdr.FirstStringBlk
        #print "fisr string start: ", self._idxStriPos
        self._idxStri = 0
        if self.hdr.FirstStringBlk == 0:
            return False
        return self.GetStringBlock()

    def GetStringBlock(self):
        self.ocad.seek(self._idxStriPos)
        self.stri_block.ReadItself(self.ocad)
        return True

    def GetString(self): # ,TStrings *stri
        if self._idxStriPos == 0: return False # EOF
        while self.stri_block.IsDeleted(self._idxStri):
            if not NextString(): return False
        
        self.ocad.seek(self.stri_block.Pos(self._idxStri))
        stri = Strings(self.stri_block.SLen(self._idxStri))
        stri.ReadItself(self.ocad)

        #fseek(f, stri_block.Pos(idxStri), SEEK_SET);
        #stri->ReadItself( f );
        return stri
        
    def NextString(self):
        self._idxStri += 1
        if self._idxStri >= 256:
            self._idxStriPos = self.stri_block.NextBlock()
            if self._idxStriPos == 0: return False # EOF
            self.GetStringBlock()
            self._idxStri = 0
        return True        
        
    # --- Simboliai ---
    def FirstSymbol(self):
        self._idxSymbPos = self.hdr.FirstSymBlk
        self._idxSymb = 0
        return self.GetSymbBlock()

    def GetSymbBlock(self):
        self.ocad.seek(self._idxSymbPos)
        self.sym_block.ReadItself(self.ocad)
    
        #fseek(f, idxSymbPos, SEEK_SET);
        #sym_block.ReadItself(f);
        return True

    def GetSymbol(self): # TSymbol
        if self._idxSymbPos == 0: return False # EOF
    
        while self.sym_block.Pos(self._idxSymb) == 0:
            if not self.NextSymbol(): return False
    
        self.ocad.seek(self.sym_block.Pos(self._idxSymb))
        symb = Symbol(self.hdr.Version)
        symb.ReadItself(self.ocad)
        
        return symb

    def NextSymbol(self):
        self._idxSymb += 1
        if self._idxSymb >= 256:
            self._idxSymbPos = self.sym_block.NextBlock()
            if self._idxSymbPos == 0: return False # EOF
            self.GetSymbBlock()
            self._idxSymb = 0
        return True
        
        #fprintf(stderr, "Sym pos=0x%08lx type=%d sym=%s\n", sym_block.Pos(idxSymb), symb->Otp(), Osymbol::Print(symb->Sym) );


    # --- Elementai ----
    # viename elemente yra 256 blockai
    def FirstElement(self):
        self._idxElemPos = self.hdr.FirstIdxBlk
        self._idxElem = 0;
        return self.GetElemBlock()

    def NextElement(self):
        self._idxElem += 1
        if  self._idxElem >= 256:
            self._idxElemPos = self.block.NextBlock()
            if self._idxElemPos == 0: return False # EOF
            self.GetElemBlock()
            self._idxElem = 0
        return True
        
    # vienas ish 256 Elemento blocku 
    def GetElemBlock(self):
        self.ocad.seek(self._idxElemPos)
        self.block.ReadItself(self.ocad)
        #print "GetElemBlock from: ", self._idxElemPos, "Sym[0]: ", Osymbol.Print(self.block.Sym(0))
        return True

    def GetElement(self): # TElement *elem
        if self._idxElemPos == 0: return False # EOF
        if self.hdr.Version >= 10 and self.block.IsEncrypted(self._idxElem):
            raise OcadfileException("Encrypted maps unsupported!")

        while (self.block.IsDeleted(self._idxElem)): # Deleted symbols are not processed at all
            if not self.NextElement(): return False # kol -1

        self.ocad.seek(self.block.Pos(self._idxElem))
        elem = Element(self.hdr.Version)
        elem.ReadItself(self.ocad)

        #fprintf(stderr, "Elem pos=0x%08lx sym=%s\n", block->Pos(idxElem), Osymbol::Print(block->Sym(idxElem)) );
        return elem
                
    def load(self, ocadfile=None):
        """Opens a shapefile from a filename or file-like
        object. Normally this method would be called by the
        constructor with the file object or file name as an
        argument."""
        if ocadfile:
            (ocadName, ext) = os.path.splitext(ocadfile)
            self.ocadName = ocadName
        else:
            raise OcadfileException("File not specified!")
        
        try:
            self.__open()
            self.block = None
            self.syhdr = None
            self.StringsStorage = None
            
            if self.ocad:
                self.__ocadHeader()
                self.__symbolsHeader() # Version <= 8
                self.__setup() # Version <= 8
        
        finally:    
            self.__close()
            

    def __open(self):
        if not hasattr(self, '_opened') or self._opened == False:
            try:
                self.ocad = open("%s.ocd" % self.ocadName, "rb")
                self._opened = True
            except IOError:
                self._opened = False
                raise OcadfileException("Unable to open %s.ocd" % ocadName)
            
    def __close(self):
        if self._opened:
            self.ocad.close()
            self._opened = False

    def strings(self):
        if self.StringsStorage == None:
            self.StringsStorage = {} # pagal TStringIndex.RecType
        else:
            return self.StringsStorage
            
        try:
            self.__open()
            if self.hdr.Version >= 8:
                
                self.stri_block = StringIndexBlock()
            
                print "Reading Strings..."
               
                if self.FirstString(): # Read all OCAD strings into memory storage;
                    #TStrings *psi; new TStrings(stri_block.SLen(idxStri));
                    while True:
                        psi = self.GetString()#new TStrings(stri_block.SLen(idxStri));
                        if psi and len(psi.Data()):
                            RecType = self.stri_block.SType(self._idxStri)
                            if not RecType in self.StringsStorage:
                                self.StringsStorage[RecType] = []
                            
                            self.StringsStorage[RecType].append(psi)
                        if not self.NextString():
                            break
        finally:                    
            self.__close()
        return self.StringsStorage

    def colors(self):
        parsed_data = []
        if self.hdr.Version > 8:
            colors_data = self.strings().get(StringIndexType.get("si_Color"))
            for data in colors_data:
                #data_array = data.Data()
                #cmyk = (float(data_array[4]), float(data_array[6]), float(data_array[8]), float(data_array[10]))
               #parsed_data[int(data_array[2])] = OCADColor(data_array[0], cmyk, data_array[12])
                hash = data.Dict()
                
                #print "Color: ", data._data, data.Data(), data.Dict()
                cmyk_100 = (float(hash.get("c", 0)), float(hash.get("m", 0)), float(hash.get("y", 0)), float(hash.get("k", 0)))
                #cmyk_255 = tuple(map(lambda x: int(round(x*255/100.0)), cmyk_100))
                parsed_data.append((int(hash.get("n")), cmyk_100))
        else:
            for color_info in self.syhdr.aColorInfo[:self.syhdr.nColors]:
                #print "color: ", color_info.ColorNum, color_info.Color
                parsed_data.append((color_info.ColorNum, tuple(map(lambda x: x/2.0, color_info.Color))))
            
        return parsed_data
        
    def map_scale(self):
        if self.hdr.Version <= 8:
            return self.setup.MapScale
        else:
            scale_str = self.strings().get(StringIndexType["si_ScalePar"], None)
            if scale_str and len(scale_str):
                return float(scale_str[0].Dict().get("m"))
        return None
        
         
    def symbols(self):
        try:
            self.__open()
            SymbolsStorage = {}
            self.sym_block = SymbolBlock()
            
            if self.FirstSymbol(): # Read all OCAD symbols into memory storage;
                while True:
                    ps = self.GetSymbol()
                    if ps:
                        #print "name: ", Osymbol.Print(ps.Sym)
                        SymbolsStorage[Osymbol.Print(ps.Sym)] = ps
                    if not self.NextSymbol():
                        break
        finally:
            self.__close()
        return SymbolsStorage


    def elements(self):
        try:
            self.__open()
            if self.hdr.Version >= 9:
                self.block = IndexBlock9()
            else:
                self.block = IndexBlock8()
        
            ElementsStorage = []
            
            if self.FirstElement(): # Read all OCAD elements into memory storage;
                #print "yahooo!"
                while True:
                    pt = self.GetElement()
                    if pt:
                        #print "Points: ", [Cord(tcord) for tcord in pt.Poly]
                        ElementsStorage.append(pt)
                    
                    if not self.NextElement():
                        break
        finally:
            self.__close()
        return ElementsStorage
        
    
    def __setup(self):
        if self.hdr.Version <= 8:
            #print "setup... Version <= 8"
            self.ocad.seek(self.hdr.SetupPos)
            
            default = []
            if self.hdr.Version < 7:
                default = [0, "", 0, 0, 0, 0, 0] # paskutines TStp strukturos reiksmes, kuriu nebuvo ocad6
                
            self.setup =  Structure.read('TStp', self.ocad, default=default)
            #print "Setup: ", self.setup
            
            real_setup_size = self.ocad.tell() - self.hdr.SetupPos
            if real_setup_size != self.hdr.SetupSize:
                print "Error: Setup size mismatch!", real_setup_size, "!=", self.hdr.SetupSize
    
       
    def __symbolsHeader(self):
        """in OCAD 9 colors table moved to strings with type 9"""
        print "Reading symbols header..."
      	if self.hdr.Version <= 8:
            self.ocad.seek(48)
            self.syhdr =  Structure.read('TSymHeader', self.ocad)
            #print "TSymHeader: ", self.syhdr

            
    def __ocadHeader(self):
        """Reads the header information from a .ocad file."""
        if not self.ocad:
            raise OcadfileException("Ocadfile Reader requires a ocadfile or file-like object. (no ocad file found")
        
        #print "Reading header..."
        ocad = self.ocad
        ocad.seek(0)

        hdr = Structure.read('TFileHeader', ocad)
        #print "header: ", hdr

      	if hdr.OCADMark != OCAD_FILE_MAGIC:
            print "!WARNING!: Possible not OCAD file(%04X) !\n" % OCADMark

        #print "OCAD version = %d." % hdr.Version
        if hdr.Version >= 9:
            print "OCAD version = %d, subversion = %0d.%-d\n" % (hdr.Version, hdr.Subversion % 256, hdr.Subversion / 256)
        elif hdr.Version == 8:
            print "OCAD version = %d, subversion = %02d\n" % (hdr.Version, hdr.Subversion)
        elif hdr.Version == 7:
            print "OCAD version = %d, subversion = %02d.%0d\n" % (hdr.Version, hdr.Subversion / 256, hdr.Subversion % 256)
        else:   # Older versions
            print "OCAD version = %d, subversion = %02d\n" % (hdr.Version, hdr.Subversion & 0x000F)

        if hdr.Version < 6:
            raise OcadfileException("Unsupported version!");
        if hdr.Version > MAX_KNOWN_VERSION:
            print "!WARNING!: Later version of OCAD than known(%d.x) !\n" % MAX_KNOWN_VERSION

        self.hdr = hdr    


class ElementDescriptor(object):
    def __init__(self):
        self.E = None

    def Otp(self):
        return self.E.Otp
        
    def nItem(self):
        return self.E.nItem
        
    def nText(self):
        return self.E.nText

        
class ElementDescriptor8(ElementDescriptor):
    def Load(self, file):
        self.E = Structure.read('TElementDescriptor8', file)
        
    def Sym(self):
        return Osymbol.From8(self.E.Symb)
        
    def Unicode(self):
        return (self.E.Unicode == 1)

class ElementDescriptor9(ElementDescriptor):
    def Load(self, file):
        self.E = Structure.read('TElementDescriptor9', file)
        
    def Sym(self):
        return Osymbol.From9(self.E.Symb)
        
    def Unicode(self):
        return True
    
        
class Element:
    def __init__(self, _ver):
        self._Descr = None # Saugo viska kas nuskaityta is failo
        self.Poly = [] # TCord, {OCAD 8: array[0..32767]    
                            # coordinates of the object followed by a zero-terminated string if nText > 0
        self.Visible = True
        
        if _ver >= 9:
            self._Descr = ElementDescriptor9()
        else:
            self._Descr = ElementDescriptor8()
        
        self.Sym = Osymbol()

        self.PlainPoints = [] # agg::pod_bvector<point_t> PlainPoints;  // I sita masyva muskaitomos bezier kreives.
        self.PlainFirstPoints = [] # std::vector<int> PlainFirstPoints;	//  Sarasas pirmuju ("pertraukianciu") tasku polilinijos/poligono
        self.LabelReference = None # TElement* LabelReference; // nuoroda i elementa, kuris zymi einamaji.

    def ReadItself(self, file):
        """Nuskaitome visa TElement isskyrus TCord masyva"""
        self._Descr.Load(file) # reikia pciam implementuoti vietoje semiau esanciu
        self.Sym = self._Descr.Sym()
        self.Poly = Structure.read(('TCord', self.nItem() + self.nText()), file)
        
        self.Visible = True
        self.LabelReference = None
        return 0
   
    def symbol(self):
        return Osymbol.Print(self.Sym)
        
    def points(self):
        return [Cord(tcord) for tcord in self.Poly[:self.nItem()]] # skip points that encode coordinates
    
    def DrawPlainPoints(_aprox_scale=10.0, _angle_tolerance=1.0):
        print "Not implemented! Bezier curve draw..."
    
    def Range(aCheckedPoint, aNearestPoint):
        print "Not implemented! Bezier curve range..."
        
    def InPolygon(aCheckedPoint):
        print "Not implemented! Bezier inPolygon..."
        
    #Element accessors
    def Otp(self):
        return self._Descr.Otp()
    
    def nItem(self):
        return self._Descr.nItem()

    def nText(self):
        return self._Descr.nText()

    def Angle(self):
        return self._Descr.E.Ang

    def Unicode(self):
        return self._Descr.Unicode()
   
    def Text(self):
        if self.nText() == 0: # not text
            return None
            
        data_format = "HHHH" # One TCord - 4 unicode chars (2bytes)
        if not self.Unicode():
            data_format = "BBBBBBBB" # One TCord - 8 ascii chars (1byte)
            
        char_array = []
        for tcord in self.Poly[self.nItem():]:
            chars = unpack(data_format, pack("ii", tcord.x, tcord.y)) # 4 - unicode characters
            if 0 in chars: # endline
                char_array.extend(chars[:chars.index(0)])
                break
            else:
                char_array.extend(chars)

        text = "".join([unichr(c) for c in char_array])
        return text #.replace("\t", " ")
        

        
        
class IndexBlock(object):
    def __init__(self):
        self._NextBlock = 0 # LongInt, file position of the next block; 0 if this is the last bloc
        self.IndexArr = [] # TIndex8[256] or TIndex9, TIndex as defined below

    def NextBlock(self):
        return self._NextBlock
        
    def Pos(self, idx):
        return self.IndexArr[idx].Pos

        
class IndexBlock8(IndexBlock):
    def Sym(self, idx):
        return Osymbol.From8(self.IndexArr[idx].Sym)
        
    def IsDeleted(self, idx):
        return (self.IndexArr[idx].Sym == 0)
        
    def IsEncrypted(self, idx):
        return False
        
    def ReadItself(self, file):
        self._NextBlock = Structure.read('LongInt', file)
        self.IndexArr = Structure.read(('TIndex8', 256), file)
        #print "TIndexBlock8, ReadItself __NextBlock: ", self._NextBlock, self.IndexArr[0]


class IndexBlock9(IndexBlock):
    def Sym(self, idx):
        return Osymbol.From9(self.IndexArr[idx].Sym)
        
    def IsDeleted(self, idx):
        return ((self.IndexArr[idx].Status == 0) or (self.IndexArr[idx].Status == 3));
        
    def IsEncrypted(self, idx):
        return (self.IndexArr[idx].EncryptedMode != 0)
        
    def ReadItself(self, file):
        self._NextBlock = Structure.read('LongInt', file)
        self.IndexArr = Structure.read(('TIndex9', 256), file)
        #print "TIndexBlock8, ReadItself __NextBlock: ", self._NextBlock, self.IndexArr[0]
        
    
class Osymbol:
    def __init__(self, wh=None, fract=None):
        if wh == None:
            self.Sym = 0
        elif isinstance(wh, int) and fract == None:
            self.Sym = wh
        elif isinstance(wh, str):
            is_fraction = False
            Fract = 0
            self.Sym = 0
            
            for i in xrange(len(aArg)):
                if aArg[i] >='0' and aArg[i]<='9':
                    if is_fraction:
                        Fract = Fract*10 + (ord(aArg[i])-ord('0'))
                    else:
                        Sym = Sym*10 + (ord(aArg[i])-ord('0'))
                elif aArg[i]=='.' and not is_fraction:
                    is_fraction = True;
                else:
                    raise OcadfileException("Osymbol._init_from_string: %s" % aArg)
            self.Sym = Sym*1000 + Fract
        else:
            self.Sym = wh*1000 + fract 

    @staticmethod
    def From(_ver, s): # SmallInt
        if _ver <= 8:
            return Osymbol.From8(s)
        else:
            return Osymbol.From9(s)
            
    @staticmethod
    def To(_ver, s): # SmallInt
        if _ver <= 8:
            return Osymbol.To8(s)
        else:
            return Osymbol.To9(s)
            
    @staticmethod
    def From8(s8): # SmallInt
        return Osymbol(s8/10, s8%10)

    @staticmethod
    def To8(s):
        return (s.Sym/1000)*10 + (s.Sym%1000)

    @staticmethod
    def From9(s9): # LongInt
        return Osymbol(s9)

    @staticmethod
    def To9(s):
        return s.Sym

    @staticmethod
    def Print(o):
        if o.Sym == -2:
            return "graphics"
            
        return "%d.%d" % (o.Sym/1000, o.Sym%1000)

        
class SymbolBlock:
    def __init__(self):
        self._NextBlock = 0 #       file position of the next block; 0 if this is the last block
        self._FilePos= [] #   256 file offsets of symbols (LongInt)

    def NextBlock(self):
        return self._NextBlock
        
    def Pos(self, idx):
        return self._FilePos[idx]
        
    def ReadItself(self, file):
        self._NextBlock = Structure.read('LongInt', file)
        self._FilePos = Structure.read(('LongInt', 256), file)
        #print "TIndexBlock8, ReadItself __NextBlock: ", self._NextBlock, self._FilePos[0]

       
class Symbol:
    def __init__(self, _ver):
        self._Descr = None #TSymbolDescriptor 
        self.Sym = None # Osymbol	
        self._Descr = SymbolDescriptor(_ver)

    def ReadItself(self, file):
        # Pirma nuskaitome bazinio simbolio turini
        if not self._Descr.LoadBase(file):
            return False

        self.Sym = self._Descr.Sym()
        
        # dabar galim nuskaityti likusia fiksuota info
        if not self._Descr.LoadFixed(file):
            return False

        # nuskaitome kintamaja dali
        if self._Descr.Length() > self._Descr.BaseSize() + self._Descr.SymSize():
            #print "Readitself: ", self._Descr.Length(), ">", self._Descr.BaseSize(), "+", self._Descr.SymSize(), " diff: ", self._Descr.Length()-(self._Descr.BaseSize() + self._Descr.SymSize())
            if not self._Descr.LoadDynamic(file):
                return False

        return True
        
    # Symbol accessors
    def Otp(self):
        return self._Descr.Otp()

    def Status(self):
        return self._Descr.Status()
        
    def Description(self):
        return self._Descr.Description()

    def BSym(self):
        return self._Descr.B #aseStorage()
        
    def Color(self):
        return self._Descr.Color()

    def Elements(self):
        return self._Descr.Elements

    def ESym(self):
        return self._Descr.S #torage()


class SymbolDescriptor(object):        
    def __init__(self, version):
        self.B = None # TBaseSym8/9
        self.S = None # TSymU8/9, viena is TSymU8/9 reiksmiu
        #self.sPoly = [] #  TCord, Coordinates storage
        #self.SymEltHeader = None
        #self.SymElt = [] #None # sudetingo Point simbolio elementai...
        self.Elements = [] # (header, coordinates),...
        
        if version <= 8:
            self._version = 8
        else:
            self._version = 9
            
        self._base_structure = 'TBaseSym%s' % self._version
        self._symbol_structures = {
            Point: 'TPointSym%s' % self._version, 
            Line: 'TLineSym%s' % self._version,
            Area: 'TAreaSym%s' % self._version,
            UnformattedText: 'TTextSym%s' % self._version,
            FormattedText: 'TTextSym%s' % self._version,
            LineText: 'TLTextSym%s' % self._version,
            RectangleO: 'TRectSym%s' % self._version
        }
        
        #for point, value in self._symbol_structures.items():
        #    Structure.calcsize(value)

    def BaseSize(self):
        return Structure.calcsize(self._base_structure)

    def LoadBase(self, file):
        # Pirma nuskaitome bazinio simbolio turini
        self.B = Structure.read(self._base_structure, file)
        return True

    def LoadFixed(self, file):
        # dabar galim nuskaityti likusia fiksuota info
        #if ( !fread( Descr->Storage(), Descr->SymSize(), 1, f ) ) return -1;
        self.S = Structure.read(self._symbol_structures.get(self.B.Otp, 0), file)
        return True

    def LoadDynamic(self, file):
        #TPointSym8/9 -> turintis dinamine dali kurioje aprasomos sudedamosios grafines simbolio dalys
        #self.sPoly = Structure.read(('TCord', self.DataSize()), file)
        i = 0
        while i < self.DataSize(): # viso galime nuskaityti self.DataSize() * 8 baitu
            SymEltHeader = Structure.read('TSymEltHeader', file)
            i += 2 # headeris - 16 baitu
            
            if self._version == 8:
                diamater = SymEltHeader.stDiameter - SymEltHeader.stLineWidth # 8 prie radiuso prideta po SymEltHeader.stLineWidth is abieju pusiu!
                SymEltHeader = Structure.update('TSymEltHeader', SymEltHeader, "stDiameter", diamater)
            
            self.Elements.append((SymEltHeader, [Cord(tcord) for tcord in Structure.read(('TCord', SymEltHeader.stnPoly), file)]))
            i += SymEltHeader.stnPoly # viena koordinate 8 baitai (4,4)
        return True
        
    def SymSize(self):
        return Structure.calcsize(self._symbol_structures[self.B.Otp])

    def DataSize(self):
        if self.B.Otp == Point or self.B.Otp == Area:
            return self.S.DataSize
        elif self.B.Otp == Line:
            return (self.S.PrimDSize+self.S.SecDSize+self.S.CornerDSize+self.S.StartDSize+self.S.EndDSize)
        else:
            return 0 #UnformattedText, FormattedText, LineText, RectangleO, default

    def Length(self):
        return self.B.Size

    def Otp(self):
        return self.B.Otp
  
    def Status(self):
        return self.B.Status
  
    def Description(self):
        return self.B.Description

    def Sym(self):
        return Osymbol.From(self._version, self.B.Sym)
  
    def SetSym(self, _o):
        self.B.Sym = Osymbol.To(self._version, _o)
   
    
    def Color(self):
        if self.B.Otp == Area:
            #print "Area: ", self.S.FillColor, self.S.HatchColor, self.S.FillColor or, self.S.HatchColor
            #print "Sym:", self.Sym(), " colors: ", self.S.FillColor, self.S.HatchColor
            return self.S.FillColor if self.S.FillOn else self.S.HatchColor # su patternais gali netureti FillColor
        elif self.B.Otp == Line:
            return self.S.LineColor# or self.S.DblFillColor # kazkodel su samplemap.ocd 861.x simboliams self.S.LineColor - grazina 0, nors ir nustatyta spalva
            # ??? tai gal tai normalu - gali buti index'as 0
        elif self.B.Otp == RectangleO:
            return self.S.LineColor
        elif self.B.Otp in (UnformattedText, FormattedText, LineText):
            return self.S.FontColor
        elif self._version <= 8: # nezinau kas cia per reiksmes
            return self.B.Cols[0]
        else: # 9,10
            nColors = self.B.nColors # numeris 1-14 # ar tikrai jos naudojamos?
            #print "nColors", nColors
            colors = self.B.Colors # viso galimu 14
            return colors[nColors-1]


class StringIndexBlock:
    def __init__(self):
        self._NextBlock = 0  #LongInt, file position of the next StringIndexBlock
                                       # 0 if this is the last StringIndexBlock
        self._Table = []#TStringIndex [256];
        
    def NextBlock(self):
        return self._NextBlock
        
    def Pos(self, idx):
        return self._Table[idx].Pos

    def SLen(self, idx):
        return self._Table[idx].Len

    def SType(self, idx):
        return self._Table[idx].RecType
        
    def IsDeleted(self, idx):
        return (self._Table[idx].RecType < 0)

    #int size()		  { return (sizeof(_NextBlock)+sizeof(Table)); }

    def ReadItself(self, file):
        #print "f.tell(): ", file.tell()
        #print "50: ", file.read(8)
        
        self._NextBlock = Structure.read('LongInt', file)
        #print "StringIndexBlock:_NextBlock ", self._NextBlock
        self._Table = Structure.read(('TStringIndex', 256), file)
        
        #print "NEXT: ", self._NextBlock, self._Table[0]
        
        #fread( &_NextBlock, size(), 1, f );
  

class Strings:
    def __init__(self, _sz=0):
        self._Descr = [] #char* string?
        
        if isinstance(_sz, int):
            self._datalen = _sz
        else: # Copy constructor for use with std::multimap
            self._datalen =_sz._datalen
            self._Descr = _sz._Desc

    def Data(self):
        return self._Descr
        
    def Dict(self):
        hash = {}
        i = 1
        while i+1 < len(self._Descr):
            code = self._Descr[i]
            value = self._Descr[i+1]
            
            if code in hash:
                if isinstance(hash[code], list):
                    hash[code].append(value)
                else:
                    hash[code] = [hash[code], value]
            else:
                hash[code] = value
            i += 2
        return hash
        
    def Name(self):
        return self._Descr[0] # gali ir nebuti
        
	#int size() { return datalen; }
	#const char *Data() { return Descr; }

    def ReadItself(self, file):
        if self._datalen != 0:
            #print "Strings, Read:", self._datalen, " $", file.read(self._datalen), "$"
            characters = Structure.read(('Byte', self._datalen), file)
            self._data = [chr(a) for a in characters]
            #x = [chr(a) for a in characters]
            #if x and x[1] == 'a':
            #print x
            
            data = []
            i = 0
            value = ''
            while i < len(characters):
                char =  chr(characters[i])
                if char == '\t':
                    data.append(value)
                    data.append(chr(characters[i+1])) # po tabo visada eina kodas
                    i += 1 # praleidziam koda
                    value = ''
                elif characters[i] == 0: # End of string
                    data.append(value)
                    break
                else:
                    value += char
                i += 1    
                
            self._Descr = data
        return True

        
class Cord(object):
    """.__x; lower four bits (longint):
        1: this point is the first bezier curve point
        2: this point is the second bezier curve point
        4: for double lines: there is no left line between this point and the next point
        8: (OCAD 9) this point is a area border line or a virtual line gap
        .__y; lower four bits:
        1: this point is a corner point
        2: this point is the first point of a hole in an area
        4: for double lines: there is no right line between this point and the next point
        8: (OCAD 7-9) this point is a dash point
    """            
    __slots__ = ['__x', '__y', 'x', 'y']
    def __init__(self, __x_or_pair, __y = None):
        if __y == None:
            self.__x = __x_or_pair[0]
            self.__y = __x_or_pair[1]
        else:
            self.__x = __x_or_pair
            self.__y = __y
            
        self.x = Cord.cord2Double(self.__x)
        self.y = Cord.cord2Double(self.__y)
 
    def __len__(self):
        return 2
 
    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError("Invalid subscript "+str(key)+" to TCord")
 
    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Invalid subscript "+str(key)+" to TCord")
 
    # String representaion (for debugging)
    def __repr__(self):
        return 'TCord(%s, %s)' % (self.x, self.y)
 
    # Comparison
    def __eq__(self, other):
        if hasattr(other, "__getitem__") and len(other) == 2:
            return self.x == other[0] and self.y == other[1]
        else:
            return False
 
    def __ne__(self, other):
        if hasattr(other, "__getitem__") and len(other) == 2:
            return self.x != other[0] or self.y != other[1]
        else:
            return True
 
    def __nonzero__(self):
        return bool(self.x or self.y)
    
    @staticmethod
    def cord2Double(z):
        return ((z >> 8) / 100) + ((z >> 8) % 100) / 100.0
    
    def IsUsual(self):
        return ((self.__x & 0x0F) == 0)
        
    def IsFirstCurve(self):
        return ((self.__x & 0x01) == 1)
        
    def IsSecondCurve(self):
        return ((self.__x & 0x02) == 2)

    def IsNoLeftDouble(self):
        return ((self.__x & 0x04) == 4)

    def IsAreaBorderGap(self): 
        return ((self.__x & 0x08) == 8)

    def IsCornerPoint(self): 
        return ((self.__y & 0x01) == 1)

    def IsFirstInHole(self):
        return ((self.__y & 0x02) == 2)
        
    def IsNoRightDouble(self):
        return ((self.__y & 0x04) == 4)
  
    def IsDashPoint(self):
        return ((self.__y & 0x08) == 8)

    def SetPoint(self, point):
        self.x, self.y = point
        PreResult = (self.x * 100)<<8;
        self.__x = (0 & 0x0F) | PreResult;

        PreResult = (self.y * 100)<<8;
        self.__y = (0 & 0x0F) | PreResult;



if __name__ == "__main__":
    #omap = Reader("samples/ocd/ocad6.ocd")
    #omap = Reader("samples/ocd/senasalisdvir15.ocd") # 8
    #omap = Reader("samples/ocd/lavoriskes.ocd") # 8
    omap = Reader("samples/ocd/example2.ocd") # 9
    #omap = Reader("samples/ocd/ocad10.ocd")
    
    elements = omap.elements()
    print "Loaded elements = %d\n" % len(elements)
    
    for i in range(len(elements)):
        element = elements[i]
        otp = element.Otp()
        if otp == UnformattedText:
            print "text: ", element.Text()

    symbols = omap.symbols()
    print "Loaded symbols = %d\n" % len(symbols.items()) # symbols["50.0"]
    
    strings = omap.strings()
    #print "0 data: ", strings[1026][0].Data()
    
    #for parameter, value in strings.items():
    #    print parameter, len(value)
    #    print value[0].Data()
    
    print "Loaded strings = %d\n" % len(strings.items())

def get_text():
    omap = Reader("samples/ocd/text_testas.ocd") # 9
    elements = omap.elements()
    #return elements[1005]
    return elements[0]

    
    
