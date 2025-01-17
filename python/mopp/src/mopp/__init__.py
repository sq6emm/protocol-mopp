#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# This file is part of the SigBit project
# https://github.com/tuxintrouble/sigbit
# Author: Sebastian Stetter, DJ5SE
# License: GNU GENERAL PUBLIC LICENSE Version 3
#
# common utility functions for SigBit
from math import ceil
import json

def ditlen(wpm):
    """returns the lenght of a dit in seconds for a given words-per-minute"""
    #PARIS incl. Abstände == 50 ditlängen -> 1 ditlänge at1wpm = 60s / (50 * wpm)
    return 60 / (50 * wpm)


###morse LUT###
morse = {
	"0" : "-----", "1" : ".----", "2" : "..---", "3" : "...--", "4" : "....-", "5" : ".....",
	"6" : "-....", "7" : "--...", "8" : "---..", "9" : "----.",
	"a" : ".-", "b" : "-...", "c" : "-.-.", "d" : "-..", "e" : ".", "f" : "..-.", "g" : "--.",
	"h" : "....", "i" : "..", "j" : ".---", "k" : "-.-", "l" : ".-..", "m" : "--", "n" : "-.",
	"o" : "---", "p" : ".--.", "q" : "--.-", "r" : ".-.", "s" : "...", "t" : "-", "u" : "..-",
	"v" : "...-", "w" : ".--", "x" : "-..-", "y" : "-.--", "z" : "--..", "=" : "-...-",
	"/" : "-..-.", "+" : ".-.-.", "-" : "-....-", "." : ".-.-.-", "," : "--..--", "?" : "..--..",
	":" : "---...", "!" : "-.-.--", "'" : ".----.", ";" : "-.-.-.", "&" : ".-...", "@" : ".--.-.",
        "ä" : ".-.-", "ö" : "---.", "ü" : "..--", "ch" : "----", '"' : ".-..-.", "(" : "-.--.", ")" : "-.--.-",
        "<sk>" : "...-.-", "<bk>" : "-...-.-"
  }


def encode(text): # FIXME: Make a first function to convert character to .- language and a 2nd to convert to 01010 and a final one to convert to mopp binary
    """takes a string of characters and returns a wordbuffer"""
    wordbuffer = []
    for c in text:
        if c == " ":
            wordbuffer.append("11")
        if c in morse:
            for el in morse[c]:
                if el == "-":
                    wordbuffer.append("10")
                if el == ".":
                    wordbuffer.append("01")
            wordbuffer.append("00")
    if len(wordbuffer) > 0:
        wordbuffer.pop()
    wordbuffer.append("11")
    return wordbuffer
                

def decode(buffer):
    """takes a wordbuffer and returns a string of characters"""
    global morse    
    outcode = ""
    outchars = ""
    for el in buffer:
      if el == "01":
        outcode += "."
      elif el == "10":
        outcode += "-"
      elif el == "00":
        for letter, code in morse.items():
          if code == outcode:
            outchars += letter
            outcode = ""
      elif el == "11":
        for letter, code in morse.items():
          if code == outcode:
            outchars += letter
            outcode = ""
    outchars = outchars + " "
    return outchars


#make own zfill for uPython
def zfill(str,digits):
    '''we need to implement our own zfill for uPython)'''
    if len(str)>=digits:
        return str
    else:
        return ((digits - len(str)) * '0')+str


#make own ljust for uPython
def ljust(string, width, fillchar=' '):
    '''returns the str left justified, remaining space to the right is filed with fillchar, if str is shorter then width, original string is returned '''
    while len(string) < width:
        string += fillchar
    return string



# Module for MOPP protocol
# Taken and adjusted from the m32-chat-server implementation by SP9WPN

class Mopp:
    serial = 1

    def __init__(self, speed = 20):
        self.speed = speed
        self.set_speed (speed=speed)
        return
    
    def set_speed(self, speed = 20):
        # Ref timings: https://morsecode.world/international/timing.html#:~:text=It's%20clear%20that%20this%20makes,%22)%20which%20also%20makes%20sense.
        speed_wpm = speed
        self.dit_duration = int(60 / (50*speed_wpm)*1000)
        self.dah_duration = 3*self.dit_duration
        self.eoc_duration = 3*self.dit_duration
        self.eow_duration = 7*self.dit_duration

    def _str2hex(self, bytes):
        hex = ":".join("{:02x}".format(c) for c in bytes)
        return hex

    def _str2bin(self, bytes):
        bincode = "".join("{:08b}".format(c) for c in bytes)
        return bincode

    def mopp(self, speed, msg):
        #logging.debug("Encoding message with "+str(speed)+" wpm :"+str(msg))

        morse = {
            "0" : "-----", "1" : ".----", "2" : "..---", "3" : "...--", "4" : "....-", "5" : ".....",
            "6" : "-....", "7" : "--...", "8" : "---..", "9" : "----.",
            "a" : ".-", "b" : "-...", "c" : "-.-.", "d" : "-..", "e" : ".", "f" : "..-.", "g" : "--.",
            "h" : "....", "i" : "..", "j" : ".---", "k" : "-.-", "l" : ".-..", "m" : "--", "n" : "-.",
            "o" : "---", "p" : ".--.", "q" : "--.-", "r" : ".-.", "s" : "...", "t" : "-", "u" : "..-",
            "v" : "...-", "w" : ".--", "x" : "-..-", "y" : "-.--", "z" : "--..", "=" : "-...-",
            "/" : "-..-.", "+" : ".-.-.", "-" : "-....-", "." : ".-.-.-", "," : "--..--", "?" : "..--..",
            ":" : "---...", "!" : "-.-.--", "'" : ".----."
        }

        m = '01'				# protocol version
        m += bin(self.serial)[2:].zfill(6)
        m += bin(speed)[2:].zfill(6)

        for c in msg:
            if c == " ":
                continue				# spaces not supported by morserino!

            for b in morse[c.lower()]:
                if b == '.':
                    m += '01'
                else:
                    m += '10'

            m += '00'				# EOC

        m = m[0:-2] + '11'			# final EOW
        m = m.ljust(int(8*ceil(len(m)/8.0)),'0')

        #print (m, " ENCODER") # FIXME

        res = ''
        for i in range (0, len(m), 8):
            #print (m[i:i+8], bytes(chr(int(m[i:i+8],2)),"latin_1"), i, " ENCODER")
            res += chr(int(m[i:i+8],2))

        self.serial += 1
        return bytes(res,'latin_1') # WATCH OUT: UNICODE MAKES MULTI-BYTES 

    def _stripheader(self, msg):
        res = bytes(0x00) + bytes(msg[1] & 3) + msg[2:]
        return res

    def msg_strcmp (self, data_bytes, speed, msg):
        if self._stripheader(data_bytes) == self._stripheader(self.mopp(speed, msg)):
            return True
        else:
            return False
        
    def received_speed (self, data_bytes): # FIXME
        speed = data_bytes[1] >> 2 
        return speed

    def received_serial (self, data_bytes): # FIXME
        #myserial = data_bytes[0] >> 2 
        myserial = 0 # FIXME
        return myserial

    def received_data (self, data_bytes): # TODO
        return self._str2hex(data_bytes)

    def decode_message (self, data_bytes):
        if len(data_bytes) < 1:
            return {"Keepalive": True}
        
        speed = data_bytes[1] >> 2 

        # Convert symbols to string of 0 and 1 again
        n = ""
        for l in [data_bytes[i:i+1] for i in range(len(data_bytes))]:
            n += "{:08b}".format(ord(l))
        
        # list of bit pairs 01, 10, 11, 00
        sym = [n[i:i+2] for i in range(0, len(n), 2)] 
        protocol = sym[0]
        serial = int("".join(sym[1:4]),2)

        # Extract message in format ./-/EOC/EOW
        msg = ""
        for i in range (14, len(n), 2):
            s = n[i:i+2]
            msg += self._mopp2morse(s)

        return {"Protocol": protocol, "Serial": serial, "Speed": speed, "Message": msg}


    def _mopp2morse(self, sym):
        s = ""
        if sym == '01':
            s = '.'
        elif sym == '10':
            s = '-'
        elif sym == '00':
            s = 'EOC'
        elif sym == '11':
            s = 'EOW'
        else:
            return ""
            #logging.debug ("This should not happen: symbol ", s)
        return s
    
    def _morse2txt(self, morse):
        return
    
    def return_duration_json(self, message):
        json_string = '{"durations": []}'
        data = json.loads(json_string)

        for symbol in message:
            if symbol == ".":
                data['durations'].append(self.dit_duration)
                data['durations'].append(-self.dit_duration)
            elif symbol == "-":
                data['durations'].append(self.dah_duration)
                data['durations'].append(-self.dit_duration)
            elif symbol == "C": # EOC
                data['durations'].append(-self.eoc_duration)
            elif symbol == "W": # EOW
                data['durations'].append(-self.eow_duration)

        updated_json_string = json.dumps(data, indent=2)
        return updated_json_string

