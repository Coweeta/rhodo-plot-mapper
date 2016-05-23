import laser_range
import gen
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import pyttsx


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


def multi_reading(tp, new_vector=True, prev_reading=None, repeats=3):   
    
    readings = []
    
    for i in range(repeats):
        say('click {}'.format(i+1))
        reading = tp.get_reading()
        if reading is None:
            print "TruPulse reported an error."
            say('error')
        inaccuracy_flag = int(100 * reading['horz_dist']) % 2
        if inaccuracy_flag:
            print "reading inaccurate ({})".format(reading)
            say('inaccurate')
        readings.append(reading)
        sleep(1)
    
    if new_vector and prev_reading and prev_reading == readings[0]:
        print "got duplicate ({})".format(reading)
        say('duplicate')
        readings.pop(0)
        
    if not readings:
        say("no readings")
        return None
        
    d = [r['horz_dist'] for r in readings]
    a = [r['azimuth'] for r in readings]    

    if a[0] > 270 or a[0] < 90:
        # we're pointing around north; change azimuth range to -180 to 180
        for i, x in enumerate(a):
            if x > 180:
                a[i] = x - 360.0

    d_spread = max(d) - min(d)
    a_spread = max(a) - min(a)
    if d_spread > 0.2 or a_spread > 1.0:
        say("variation")
        print d_spread, a_spread, readings
        return None
        
        
    say('Got {:0.1f} meters bearing {}'.format(d[0], bearing(a[0])))
    return readings[0]
    


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
        points.loc[name] = {'type': sort, 'ew': ew, 'ns': ns}  

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
       

def main():
    dev_name = None
    point_filename = "points.xlsx"
    reading_filename = "readings.xlsx"
    
    readings = pd.DataFrame(columns=('azim', 'hdist', 'from', 'to', 'dev', 'invalid'))
    points = pd.DataFrame(columns=('type', 'ew', 'ns'))
    
    say('Hello mapper.')
    
    loc = None
    target = None
    last = None
    
    tp = None
    while True:
        cmd = raw_input('Action: ("?" for help) ')
        
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
                tp = laser_range.TruPulseInterface(dev_name, trace=True)
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
            refs = points.loc[points['type'] == 'anchor']
            mp = points.loc[points['type'] != 'anchor']
            mp = gen.solve(refs, readings, mp)
            points = pd.concat((refs, mp))
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
            gen.show_map(fig, points, readings[readings['invalid'] == False], pts)
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
            name = raw_input("Target's name: ")
            if not name or name not in points.index:
                print "Bad name."
                continue
            target = name
            r = multi_reading(tp, prev_reading=last)
            if r is not None:
                last = r
                readings.loc[len(readings)] = {'from':loc, 'to':target, 'azim': r['azimuth'], 'hdist': r['horz_dist'], 'invalid':False, 'dev': np.nan}
            continue        
           
        if cmd == 'r':
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
                w:
                q: quit
                """
            continue
            
        if cmd == 'q':
            break
            
   
    
main()    
