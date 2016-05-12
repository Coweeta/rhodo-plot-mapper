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
    engine.setProperty('voice', 'english')
    engine.say(text)
    engine.runAndWait()


    



def read_file(filename):
    with open(filename, 'r') as f:
        points = pd.read_excel(f, header=2, index_col=0)
        
    return points


# "/dev/rfcomm0"


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


def create_point(name, points):
            
    print 'Creating new point "{}".'.format(name)

    while True:
        sort = raw_input("This point's type id: ('?' for list) ")
        if sort == '?':
            print "\n".join(["{}: {}".format(i, n) for i, n in enumerate(types)])
            continue
        try:
            sort = types[int(sort)]
        except:
            continue
        points.loc[name] = {'type': sort, 'ew': np.nan, 'ns': np.nan}  

        break

last = None


def matches_last(r, name, ref_name):
    global last
    if last is None or r != last[0]:
       last = (r, name, ref_name)
       return False
       
    if name == last[1] and ref_name == last[2]:
        return False
        
    return True   
                    

def loop(tp, points, readings):
    while True:
        name = raw_input("This point's name: ('$' to quit, '?' for list) ")
        if name == '$':
            return True
        if name == '?':
            print "\n".join(sorted(points.index))
            continue
        if not name:
            continue
        if name not in points.index:
            create_point(name, points)
            
        break

    while True:
        ref_name = raw_input("Ref point's name: ('?' for list) ")
        if ref_name == '?':
            print "\n".join(sorted(points.index))
            continue
        if ref_name not in points.index:
            create_point(ref_name, points)
            break
        if ref_name == name:
            print "Can't be current location"
            continue
        break

    
    #TEMP!!! tp.set_horiz_vector_mode()  #TEMP!!! workaround to avoid old result
    
    while True:
        say('click')
        r = tp.get_reading()
        if r is None:
            print "TruPulse reported an error."
            say('error')
            return False
            
        if matches_last(r, name, ref_name):
            print "got duplicate ({}); redoing...".format(r)
            say('duplicate')
            sleep(3)
            continue
        break    
        
    inaccuracy_flag = int(100 * r['horz_dist']) % 2
    if inaccuracy_flag:
        print "reading inaccurate ({})".format(r)
        say('inaccurate')
    
    say('{} is {:0.1f} meters from {}. . . bearing {}'.format(ref_name, r['horz_dist'], name, bearing(r['azimuth'])))
    readings.loc[len(readings)] = {'from':name, 'to':ref_name, 'azim': r['azimuth'], 'hdist': r['horz_dist'], 'invalid':False, 'dev': np.nan}
    print r
    
    return False

def bearing(azimuth):
    angle = azimuth + 22.5
    octdrant = int(angle / 45.0) % 8
    n = "north "
    e = "east"
    s = "south "
    w = "west"
    return [n, n+e, e, s+e, s, s+w, w, n+w][octdrant]
    

def main():
    dev_name = sys.argv[1]
    point_filename = sys.argv[2]
    reading_filename = sys.argv[3]
    
    readings = pd.DataFrame(columns=('azim', 'hdist', 'from', 'to', 'dev', 'invalid'))
    points = read_file(point_filename)
    
    say('Hello mapper.')
    
    print readings
    print points
    
    tp = None
    while True:
        cmd = raw_input('Action: ("?" for help) ')
        if cmd == 'r':
           readings = read_file(reading_filename)
           print readings
           continue
    

        if cmd == 'c':
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
                        
        if cmd == 'e':
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
  
        if cmd == 'm':
            pts = raw_input('point to highlight: ')
            if pts == '':
                pts = None
            elif pts not in points.index:
                print 'not valid point name'
                pts = None
    
            refs = points.loc[points['type'] == 'anchor']
            mp = points.loc[points['type'] != 'anchor']
            fig = plt.figure()
            gen.show_map(fig, refs=refs, pts=pts, readings=readings, est=mp)
            fig.show()
            continue
            
        if cmd == 'g':
            if tp is None:
                print 'connect first'
                continue
            while True:
                done = loop(tp, points, readings)
                if done:
                    break
            continue

        if cmd == 's':
            readings.to_excel('readings2.xls', startrow=2)
            points.to_excel('points2.xls', startrow=2)
            continue
            
        if cmd == 'i':
            while True:
                rid = raw_input('which reading to invalidate? ("$" to quit) ')
                if rid == '$':
                    continue
                try:
                    rid = int(rid)    
                    readings.loc[rid, 'invalid'] = True
                except:
                    pass
                
        if cmd == '?':
            print 'e: evaluate\ng: gather\ns: save\ni: invalidate reading\np: print values\nm: map values\nc: connect to TruPulse\nv: get version\nr; read in readings file\nq: quit\n'
            continue
            
        if cmd == 'q':
            break
            
   
    

def plot_points(points, psorts):
    keys = points.keys()
    values = np.array(points.values())
    sorts = np.array(psorts.values())
    cmapper = np.array([0.1, 0.2, 0.3, 0.4])
    smapper = 100 * np.array([1,2,3,4])

    plt.scatter(
        values.real, values.imag, marker='o', c=cmapper[sorts], s=smapper[sorts])

    for label, loc in zip(keys, values):
        plt.annotate(
            label, xytext = (0, -20),
            textcoords = 'offset points', ha = 'center', va = 'bottom',
            xy = (loc.real, loc.imag))

    plt.show()
    
main()    
