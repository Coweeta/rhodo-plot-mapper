import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import pyttsx

import laser_range
import map_solver
import map_display


def say(text):
    engine = pyttsx.init()
    engine.setProperty('rate', 150)
    engine.setProperty('voice', 'american')
    engine.say(text)
    engine.runAndWait()

"""
class Mapper(object):
    
def go_to(self, args):
    if args[0] not in self._p.index:
        return "No such point"
    self._from = args[0]
    return None
    
def target(self, args):
    if args[0] not in self._p.index:
        return "No such point"
    self._to = args[0]
    self._get_reading()
    
    
def redo(self, args):
    self._get_reading()
    
"""

def deviates(r1, r2):
    delta_dist = abs(r1['horz_dist'] - r2['horz_dist'])
    if delta_dist > 0.2:
        return True
    # http://stackoverflow.com/questions/1878907/the-smallest-difference-between-2-angles    
    rotation = r1['azimuth'] - r2['azimuth']
    delta_angle = abs((rotation + 180.0) % 360.0 - 180.0)
    if delta_angle > 1.0:
        return True
        
    return False    
        
    

def multi_reading(tp, new_vector=True, prev_reading=None, max_goes=4):   
    """Reads from the TruPulse until there are two good, matching readings.
    
    """
    
    
    goes = 0
    last = None
    while True:
        if goes == max_goes:
            say("Give up")
            return None
        goes += 1
        
        got = single_reading(tp, new_vector, prev_reading)
        if got:
            if not last:
                last = got
                continue
            if deviates(got, last):
                say("deviates")
                last = got
                continue
            
            # we've got two consecutive readings
            break    
                
        
    say('Got {:0.1f} meters bearing {}'.format(got['horz_dist'], bearing(got['azimuth'])))
    return got
    
        
        
def single_reading(tp, new_vector=True, prev_reading=None):     
    say('click')
    
    reading = tp.get_reading()
    if reading is None:
        print "TruPulse reported an error."
        say('error')
        return None
        
    # messy way of checking 2nd decimal place is non-zero    
    inaccuracy_flag = int(round(100 * reading['horz_dist'])) % 10 != 0
    if inaccuracy_flag:
        print "dist reading inaccurate ({})".format(reading)
        say('inaccurate')
        return None
        
    if new_vector and prev_reading and prev_reading == reading:
        print "got duplicate ({})".format(reading)
        say('duplicate')
        return None
        
    return reading
    


def read_file(filename):
    with open(filename, 'r') as f:
        points = pd.read_excel(f, header=2, index_col=0)
        
    return points




def get_pos(reading, ref_pos):
    dist = complex(reading['horz_dist'])
    # Convert to radians.
    angle = reading['azimuth'] * 2.0 * numpy.pi / 360.0
    return ref_pos - dist * numpy.exp(angle)


def new_reading(tp, name, ref_name, readings):
    ref = points[ref_name]
    new_pos = get_pos(reading, ref)
    points[name] = new_pos

types = ['anchor', 'oak', 'rhodo']


def create_point(points):
            
    while True:
        name = raw_input("New point's name: ")
        if name in points.index:
            print 'already exists'
            continue
        break
        
    while True:
        sort = raw_input("This point's type id: ('?' for list) ")
        if sort == '?':
            print "\n".join(["{}: {}".format(i, n) for i, n in enumerate(types)])
            continue
        try:
            sort = types[int(sort)]
        except:
            continue
        if sort == 'anchor':
            locked = True
            ew = raw_input("East-west location: ")
            ns = raw_input("North-south location: ")
            try:
                ew = float(ew)
                ns = float(ns)
            except:
                print "bad"
                continue
        else:
            ew = np.nan
            ns = np.nan
            locked = False
        points.loc[name] = {'type': sort, 'ew': ew, 'ns': ns, 'locked': locked}  

        break

    

def bearing(azimuth):
    angle = azimuth + 22.5
    octdrant = int(np.floor(angle / 45.0)) % 8
    n, e, s, w = "north ", "east", "south ", "west"
    return [n, n+e, e, s+e, s, s+w, w, n+w][octdrant]
    
def get_name(text, default):
    message = "{}: (<CR> for '{}') ".format(text, default)
    name = raw_input(message)
    if name == '':
        name = default
    return name
       
def count_down(delay):
    for i in range(delay, 0, -1):
        say(str(i))
        sleep(1)
       

def main():
    dev_name = None
    point_filename = "points.xlsx"
    reading_filename = "readings.xlsx"
    
    readings = pd.DataFrame(columns=('azim', 'hdist', 'from', 'to', 'dev', 'invalid'))
    points = pd.DataFrame(columns=('type', 'ew', 'ns', 'locked'))
    
    say('Hello mapper.')
    
    loc = None
    target = None
    last = None
    
    tp = None
    
    delay = 0
    
    while True:
        cmd = raw_input('Action: ("?" for help) ')
        
        if cmd == 'x':
            delay_str = raw_input("Delay before reading (sec): ")
            try:
                delay = int(delay_str)
            except:
                print "ignored"
            continue                
            
        if cmd == 'l':
            point_filename = get_name("Device name", point_filename)
            reading_filename = get_name("Device name", reading_filename)
            points = read_file(point_filename)
            readings = read_file(reading_filename)
            print points
            print readings
            continue
    

        if cmd == 'c':
            dev_name = get_name("Device name", "/dev/rfcomm0")
            try:
                tp = laser_range.TruPulseInterface(dev_name, do_trace=True)
                print 'got unit'
                
                
            except Exception as e:
                print 'problem: :('
                print e
                tp = None
            continue    
            
        if cmd == 'v':
            try:
                fw_vers = tp.get_firmware_version()
                print fw_vers
                
                sleep(1)
                tp.set_horiz_vector_mode()
                sleep(1)
                reading = tp.get_reading()
            
            except Exception as e:
                print 'problem: :('
                print e
                tp = None
            continue    
            
        if cmd == 'w':
            # invalidate reading with worst deviation 
            worst = readings['dev'].idxmax()
            if isinstance(worst, int):
                readings.loc[worst, 'invalid'] = True
            continue
            
            
        if cmd == 'e':
            readings['invalid'] = readings['invalid'] == True
            mp = map_solver.place_unlocked_points(points, readings)
            print points
            print readings
            continue
            
        if cmd == 'p':
            print "Points"
            print points
            print "Readings"
            print readings
            continue
            
        if cmd == 'n':
            create_point(points)
            continue
  
        if cmd == 'm':
            pts = raw_input('names of points to highlight (space delimited): ')
            pts == pts.split()
    
            refs = points.loc[points['type'] == 'anchor']
            mp = points.loc[points['type'] != 'anchor']
            fig = plt.figure()
            map_display.show_map(fig, points, readings[readings['invalid'] == False], pts)
            fig.show()
            continue
            
        if cmd == 'g':
            name = raw_input("This point's name: ")
            if not name or name not in points.index:
                print "Bad name."
                continue
                
            loc = name
            continue
            
        if cmd == 't':
            if not loc:
                print "where are you?"
                continue
            name = raw_input("Target's name: ")
            if not name or name not in points.index:
                print "Bad name."
                continue
            target = name
            count_down(delay)
            r = multi_reading(tp, prev_reading=last)
            if r is not None:
                last = r
                readings.loc[len(readings)] = {'from':loc, 'to':target, 'azim': r['azimuth'], 'hdist': r['horz_dist'], 'invalid':False, 'dev': np.nan}
            continue        
           
        if cmd == 'r':
            if not loc or not target:
                say("huh?")
                print "repeat what?"
                continue
            count_down(delay)
            r = multi_reading(tp, prev_reading=last, new_vector=False)
            if r is not None:
                last = r
                readings.loc[len(readings)] = {'from':loc, 'to':target, 'azim': r['azimuth'], 'hdist': r['horz_dist'], 'invalid':False, 'dev': np.nan}
            continue
            
        if cmd == 'd':
            readings.loc[len(readings)-1, 'invalid'] = True
            continue
            

        if cmd == 's':
            point_filename = get_name("Device name", point_filename)
            reading_filename = get_name("Device name", reading_filename)
            readings.to_excel(reading_filename, startrow=2)
            points.to_excel(point_filename, startrow=2)
            continue
            
        if cmd == 'i':
            while True:
                rid = raw_input('which reading to toggle validity? (CR to quit) ')
                if rid == '':
                    break
                try:
                    rid = int(rid)    
                    readings.loc[rid, 'invalid'] = readings.loc[rid, 'invalid'] == False
                except:
                    pass
                
        if cmd == '?':
            print """
                e: evaluate
                g: goto next point
                t: target reading
                d: delete last reading
                s: save file
                n: new point
                l: load file
                i: toggle valid flag on reading
                p: print values
                m: map values
                c: connect to TruPulse
                v: get TruPulse version
                w: invalidate reading with worst deviation
                r: repeat last meas
                x: set delay before reading
                q: quit
                """
            continue
            
        if cmd == 'q':
            break
            
   
    
main()    
