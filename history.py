#======================Command pattern====================START==============
class Command:
    def __init__(self, x):
        self.x = x
        
    def execute(self):
        print "command execute! %i" % self.x
        return True

    def undo(self):
        print "command undo! %i" % self.x

        
class Invoker:
    head = 0 #rodo ta vieta i kur reiks ideti sekanchia komanda // arba i pirmaja kuria galima redo()
    stack = [] #new Array;
    
    button = {"undo":None, "redo": None}
    button_event = {"enable": lambda x:x, "disable": lambda x:x}
    
    @staticmethod
    def execute(command, arg=None):
        """jeigu pasikeicia irankis - tai reiketu iskviesti stop() pries tai buvusiam irankiui - ar run() naujam"""
        if arg != None:
            succ = command.execute(arg)
        else:
            succ = command.execute()
        
        if succ: 
            #Invoker.stack.splice(Invoker.head, Invoker.stack.length-Invoker.head+1); // pashaliname viska ka butu galima tuo metu redo
            Invoker.stack = Invoker.stack[:Invoker.head] # pashaliname viska ka butu galima tuo metu redo
            Invoker.stack.append(command)
            Invoker.head += 1
        
            Invoker.button_event["enable"](Invoker.button["undo"])
            Invoker.button_event["disable"](Invoker.button["redo"])
            #document.getElementById("undo").src="../images/icons/undo.gif";
            #document.getElementById("redo").src="../images/icons/redod.gif";
        #print "after execute, head: ", Invoker.head, " stack: ", Invoker.stack

    @staticmethod
    def undo():
        #Tool.run(); # mousedown iskvietimas/imitavimas
        if Invoker.head > 0:
            command = Invoker.stack[Invoker.head-1]
            command.undo()
            Invoker.head -= 1

            Invoker.button_event["enable"](Invoker.button["redo"])
            if Invoker.head <= 0:
                Invoker.button_event["disable"](Invoker.button["undo"])
                
            #    document.getElementById("undo").src="../images/icons/undod.gif";
            #document.getElementById("redo").src="../images/icons/redo.gif";
            #if (Invoker.head <= 0) {
            #    document.getElementById("undo").src="../images/icons/undod.gif";
        #print "after undo, head: ", Invoker.head, " stack: ", Invoker.stack

    @staticmethod
    def redo():
        #Tool.run();
        if len(Invoker.stack) > Invoker.head:
            command = Invoker.stack[Invoker.head]
            command.execute()
            Invoker.head += 1

            Invoker.button_event["enable"](Invoker.button["undo"])
            if len(Invoker.stack) <= Invoker.head:
                Invoker.button_event["disable"](Invoker.button["redo"])
            #document.getElementById("undo").src="../images/icons/undo.gif";
            #if(Invoker.stack.length <= Invoker.head) {
            #    document.getElementById("redo").src="../images/icons/redod.gif";
        #print "after redo, head: ", Invoker.head, " stack: ", Invoker.stack

    @staticmethod
    def set_button_event(name, func):
        Invoker.button_event[name] = func

    @staticmethod
    def set_button(name, button, disable=False):
        Invoker.button[name] = button
        if disable:
            Invoker.button_event["disable"](button)
            
#class GTK2Invoker(Invoker):
#    def __init__()
#======================Command end====================START==============
