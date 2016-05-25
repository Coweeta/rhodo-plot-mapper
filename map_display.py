import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from matplotlib.path import Path
import matplotlib.patches as patches



def stuff(readings, refs, points, anchor_to):
    angle = np.pi * readings['azim'].values / 180
    dist = readings['hdist'].values

    all_points = pd.concat((refs, points))
    ns = np.hstack((refs['ns'], points['ns']))
    ew = np.hstack((refs['ew'], points['ew']))

    from_readings = all_points.loc[readings['from']]
    nsf = from_readings['ns']
    ewf = from_readings['ew']

    to_readings = all_points.loc[readings['to']]
    nst = to_readings['ns']
    ewt = to_readings['ew']

    dns = dist * np.cos(angle)
    dew = dist * np.sin(angle)

    if anchor_to:
        return (nst - dns, ewt - dew, nst, ewt)
    else:
        return (nsf, ewf, nsf + dns, ewf + dew)


def unique_rows(array):
    """
    
    Taken blindly from http://stackoverflow.com/questions/16970982/find-unique-rows-in-numpy-array
    """
    b = np.ascontiguousarray(array).view(np.dtype((np.void, array.dtype.itemsize * array.shape[1])))
    _, index = np.unique(b, return_index=True)
    return array[index]
    
    
def show_hull(points, ax):
    """Add a polygon to a plot that contains all the points.
    
    This seems like a lot of work...
    """
    
    try:
        hull = ConvexHull(points)
        vertices = hull.vertices
        vertices = np.append(vertices, vertices[0])
        codes = [Path.LINETO] * len(vertices)
        codes[0] = Path.MOVETO
        codes[-1] = Path.CLOSEPOLY
        
        path = Path(points[vertices], codes)
        patch = patches.PathPatch(path, facecolor='orange', lw=0, alpha=0.3)
        
        ax.add_patch(patch)
    except:
        print "oh well ..."
    




def show_map(fig, points, readings=None, focus_points=None):
    
    if focus_points is None:
        focus_points = []
    refs = points[points['type'] == 'anchor']
    est = points[points['type'] != 'anchor']
    
    ax = fig.add_subplot(111, aspect='equal')
    ax.set_xlabel('meters west of origin')
    ax.set_ylabel('meters north of origin')
    if readings is not None:
        for name in est.index:
            pts = est.loc[name]
            rf = readings[readings['from'] == name]
            rt = readings[readings['to'] == name]
            nsf, ewf, nsd, ewd = stuff(rf, refs, est, anchor_to=True)
            nso, ewo, nst, ewt = stuff(rt, refs, est, anchor_to=False)
            f_points = np.array([ewf, nsf]).T
            t_points = np.array([ewt, nst]).T
            a_points = np.append(f_points, t_points, axis=0)
            if len(a_points) > 2:
                show_hull(a_points, ax)
            ax.scatter(ewf, nsf, marker='.', c='g', linewidths=0)
            ax.scatter(ewt, nst, marker='.', c='r', linewidths=0)
            if name in focus_points:
                plt.plot([ewf, ewd], [nsf, nsd], 'y-')
                plt.plot([ewo, ewt], [nso, nst], 'b-')

    plt.scatter(refs['ew'], refs['ns'], marker='^', c='g', s=100)
    ns = refs['ns']
    ew = refs['ew']
    names = refs.index
    for i in range(len(ns)):
        plt.annotate(
            names[i], xytext = (0, -20),
            textcoords = 'offset points', ha = 'center', va = 'bottom',
            xy = (ew[i], ns[i]))


    plt.scatter(est['ew'], est['ns'], marker='o', c='r', s = 20)
    ns = est['ns']
    ew = est['ew']
    names = est.index
    for i in range(len(ns)):
        plt.annotate(
            names[i], xytext = (0, -20),
            textcoords = 'offset points', ha = 'center', va = 'bottom',
            xy = (ew[i], ns[i]))
        

