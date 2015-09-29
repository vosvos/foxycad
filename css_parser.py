from string import whitespace

class ParsingError(Exception):
    def __init__(self, message, file_position):
        # Call the base class constructor with the parameters it needs
        Exception.__init__(self, message)
        self.file_position = file_position

def inline_parse(txt, decode=None):
    style = {}
    if txt == "": return style
    i = 0
    
    #try:
    if True:
        txt = txt.strip()[1:-1].strip() # skip {} ir tada dar praleidziame visa likusi tuscia plota, kad nepridetume veltui ";"
        if txt[-1] != ";": txt = "".join((txt, ";")) # pridedame kabliataski, nes jo gali nebuti - o reikia parsinimui
        length = len(txt)
        while i < length: # {text:"a:;b";angle:12}
            index = txt.index(":", i)
            key = txt[i:index].strip()
            i += (index - i + 1) # +1, nes praleidziam ":"
            
            while txt[i] in whitespace: # skip whitespace iki pirmo simbolio
                i += 1
            
            if txt[i: i+3] == "\"\"\"": # multiline data, whitespace is stripped
                i += 3
                start = i
                while txt[i: i+3] != "\"\"\"":
                    i+=1
                style[key] = map(lambda x:x.strip(), txt[start:i].strip().splitlines()) # multiline data tegu buna 'list' kad atskirti nuo paprasto teksto
                if decode:
                    style[key] = decode(key, style[key])
                #print style[key]
                i+=3
                while txt[i] in whitespace: # skip whitespace iki ";"
                    i += 1
            elif txt[i] == "\"": # tekstas
                i += 1 # praleidziam atidarancia kabute
                char = txt[i]
                value = []
                while char != "\"":
                    if char == "\\":
                        i += 1 # praleidziam pirma \
                        char = txt[i]
                        if char == "u":
                            value.append(unichr(int(txt[i+1:i+5], 16)))
                            i += 4 # praleidziam 4 simbolius
                        elif char == "\"":
                            value.append("\"")
                        elif char == "\\":
                            value.append("\\")
                        elif char == "/":
                            value.append("/")
                        elif char == "t":
                            value.append("\t")
                        elif char == "n":
                            value.append("\n")
                        elif char == "b":
                            value.append("\b")
                        elif char == "f":
                            value.append("\f")
                        elif char == "r":
                            value.append("\r")
                        else:
                            value.append(char)
                    else:
                        value.append(char)
                    i += 1 # praleidziam nuskaityta simboli
                    char = "\"" if i >= length else txt[i]
                i += 1 # praleidziam paskutine uzdarancia kabute
                style[key] = "".join(value)
                if decode:
                    style[key] = decode(key, style[key])
                
                while txt[i] in whitespace: # skip whitespace iki ";"
                    i += 1

            else: # ne tekstas o kazkokia verte
                index = txt.index(";", i)
                style[key] = txt[i:index].strip()
                if decode:
                    style[key] = decode(key, style[key])
                
                i += (index - i)
            i += 1 # praleidziam ";"
    #except:
    #    raise ParsingError("Inline parser error", i)
            
    return style

def remove_comments(txt):
    #/* */
    new_txt = []
    
    i, length = 0, len(txt)
    begin = 0
    while i < length:
        if txt[i] == "/" and txt[i+1] == "*":
            new_txt.append(txt[begin:i]) # idedame dali iki komentaro
            start = i
            i += 2 # praleidziam /*
            while (txt[i] != "*" and txt[i+1] != "/"): # praleidziame komentara...
                i += 1
            i += 1 # paleidziame "/"
            begin = i+1
            comment = txt[start:i+1]
            # tam kad butu galima nustatyti pradine klaidos eilute:pozicija vietoje komentaru idedame " "
            empty = "\n".join(map(lambda x:" " * len(x), comment.splitlines())) 
            new_txt.append(empty)
            #print "komentaras:", txt[start:i+1], "*"
        i += 1 #pereiname prie sekancio simbolio
    new_txt.append(txt[begin:])
    
    return "".join(new_txt)

    
def get_position(filestring, position):
    """ returns (line number, position in line) """
    lines = filestring.split("\n")
    line_number, place, count = 0, 0, 0
    #print "Number of lines: ", len(lines)
    
    while line_number < len(lines):
        line = lines[line_number]
        new_count = count + len(line) #+ 1 # +1 nes dar newline pridedame
        if position <= new_count:
            place = position - count
            break
        count = new_count # +1 nes dar newline pridedame
        line_number += 1
        
    print "\n".join(["%s:%s" % (("===> " if i==line_number else "") + str(i), lines[i]) for i in xrange(len(lines))])
    return (line_number, place)

    
def parse(text, decode=None):
    style = {}
    if text == "": return style
    txt = remove_comments(text).rstrip()
    
    i, length = 0, len(txt)
    try:
        while i < length: # {text:"a:;b";angle:12}
            # nuskaitome rakta (.box) iki "{",
            try:
                index = txt.index("{", i)
            except ValueError:
                raise ParsingError("\"{\" - not found", i)
            
            selector = txt[i:index].strip()
            i += (index - i + 1) # +1, nes praleidziam "{"
            while txt[i] != "}": # ieskome uzdarymo "}":
                if txt[i] == "\"":
                    i += 1 # praleidziam atidarancia kabute
                    while txt[i] != "\"": # praleidziame teksta...
                        i += 1 
                        if txt[i] == "\"" and txt[i-1] == "\\": #praleidziam kabutes tekste
                            i += 1
                i += 1 #pereiname prie sekancio simbolio
            i += 1 # praleidziame uzdarancia "}"
            #print "value: ", txt[index:i]
            try:
                style[selector] = inline_parse(txt[index:i], decode)
            except ParsingError as e:
                raise ParsingError(e.args[0], index + e.file_position)
    #except IndexError:
    #    print "Out of Bounds..."
    except ParsingError as e:
        line_number, place = get_position(text, e.file_position)
        print "Parsing Error: %s; Line:%i, Place:%i" % (e.args[0], line_number, place)

    return style

data = """
            /* comment0 
            bla bla
            adsad
            dsdsd
            sdds
            */
            .bbox    {
                color: (202, 108, 40);
                line-cap:0;
                z-index:54; /* comment1 */
                line-join:1;
                line-width:2.1;
                text: "12";
           }
            /* comment2 */
           a   { height: 12px;
             /* comment3 */
           }
           c {text:"Sch\u00f6nried\r\nSaanenm\u00f6ser\r\nSaanen"}
           d {text:"Ver. 111008.23:15"}
           e {text:"Bil:s;di\u0161k\u0117s e\u017e.";angle:12}
           f {text:"\\"\\/\\\\\\b\\f\\n\\r\\t\\u000A\\u1001"}
           g {angle : 947; banasasasasasgle:9asasass47;zangle:947;hangle:947;ranglasasase:947;jangle:"947";vangle:98098080847;text:"Sch\u00f6nried\r\nSaanenm\u00f6ser\r\nSaanen"}
           h {text:"Bil:s;di\u0161k\u0117s e\u017e.";angle:12}
           i {color:(202, 108, 40);line-cap:0;z-index:54;line-join:1;line-width:2.1;}
            /* comment4 */"""

data2 = """
            .bbox    {
                color:(202, 108, 40);
                line-cap:0;
                z-index:54; /* comment1 */
                line-join:1;
                line-width:2.1;            /* comment2 */

                text: "12";
                data: \"\"\" 
		6,,{color:(46, 48, 146);z-index:28},-12.6,-14.85,-12.6,-14.85,-12.6,-14.85,12.225,-14.85,12.225,-14.85,13.725,-14.85,14.85,-12.225,14.85,-13.725,14.85,-12.225,14.85,12.6,14.85,12.6,14.85,13.95,12.225,15.15,13.725,15.15,12.225,15.15,-12.6,15.15,-12.6,15.15,-14.1,15.15,-15.15,12.6,-15.15,13.95,-15.15,12.6,-15.15,-12.225,-15.15,-12.225,-15.15,-13.725,-12.6,-14.85,-14.1,-14.85,-12.6,-14.85
		6,,{color:(255, 255, 255);z-index:35},-1.65,-6.45,-1.65,-6.45,-1.65,-6.45,-1.65,6.75,-1.65,6.75,-1.65,6.75,4.275,6.75,4.275,6.75,4.275,6.75,0.3,-6.45,0.3,-6.45,0.3,-6.45,-1.65,-6.45,-1.65,-6.45,-1.65,-6.45,-1.65,-6.45,-1.65,-6.45,-1.65,-6.45
                \"\"\"
           }
           a   { height: 12px;
             /* comment3 */
           }
           c {
                text:    "Sch\u00f6nried\r\nSaanenm\u00f6ser\r\nSaanen"
           }
           d {text: "Ver. 111008.23:15"  }
           e {
                text:  "Bil:s;di\u0161k\u0117s e\u017e.";
                angle:12 }
           f {text:"\\"\\/\\\\\\b\\f\\n\\r\\t\\u000A\\u1001"}
           g {angle : 947; banasasasasasgle:9asasass47;
               zangle:947  ;  hangle:947;
               ranglasasase:947;jangle:"947";  
               vangle:98098080847;  
               text:"Sch\u00f6nried\r\nSaanenm\u00f6ser\r\nSaanen"
           }
           h {
                text : "Bil:s;di\u0161k\u0117s e\u017e." ;
                angle:12;
                }
                
         i {color:(202, 108, 40);
                line-cap:0;z-index:54;/* comment4 */
                line-join:1;line-width:2.1}
            """
            
#a1 = str(parse(data2))
#print a1
"""
a2 = str(parse(data2))
print a1 == a2
"""
