import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import leastsq

def gen_points_and_readings(edge_len, num_est, rpp, err):
    refs = gen_ref_points(edge_len)
    refs['type'] = 'anchor'
    actual = gen_meas_points(edge_len, num_est)
    actual['type'] = 'tree'
    readings = gen_readings(refs, actual, rpp, err)
    est = solve(refs, readings, actual)
    points =  pd.concat((refs, est))
    return points, readings, actual
    
    
def gen_ref_points(edge_len):
    e = edge_len
    refs = pd.DataFrame({'ns':[0, 0, e, e], 'ew':[0, e, e, 0]} , index=['Rsw', 'Rse', 'Rne', 'Rnw'])
    return refs


def gen_meas_points(edge_len, num):
    ns = edge_len * np.random.rand(num)
    ew = edge_len * np.random.rand(num)
    names = ['T{:02}'.format(i) for i in range(num)]

    points = pd.DataFrame({'ns':ns, 'ew':ew}, index=names)
    return points


def gen_readings(refs, points, num_per_point, err):

    all_points = pd.concat((points, refs))

    num_meas = num_per_point * len(points)

    fp = np.repeat(np.arange(len(points), dtype=int), num_per_point)
    offset = np.random.randint(1, len(all_points), num_meas)
    tp = np.mod(fp + offset, len(all_points))

    ns = all_points['ns'].values
    ew = all_points['ew'].values
    names = all_points.index.values

    nsd = ns[tp] - ns[fp] + np.random.randn(num_meas) * err
    ewd = ew[tp] - ew[fp] + np.random.randn(num_meas) * err

    dist = np.sqrt(nsd**2 + ewd**2)
    azim = 360 * np.arctan2(ewd, nsd) / (2 * np.pi)

    readings = pd.DataFrame(data={'from':names[fp], 'to':names[tp], 'hdist':dist, 'azim':azim, 'invalid':False})

    return readings


def residual(x, xref, f, t, dm, Np):
    xcomp = x[:Np] + 1j * x[Np:]
    xall = np.hstack((xcomp, xref))
    xt = xall[t]
    xf = xall[f]
    
    err = np.abs(dm - (xt - xf))
    return err


def solve(refs, readings, points):
    valid = readings['invalid'] == False
    valid_readings = readings[valid]
    names = points.index
    xpp = np.hstack((points['ew'].values, points['ns'].values))
    xpp = np.nan_to_num(xpp)

    xref = refs['ns'].values + 1j * refs['ew'].values
    angle = np.pi * valid_readings['azim'].values / 180
    dist = valid_readings['hdist'].values
    dm = dist * np.exp(1j * angle)

    a = pd.concat((points, refs))
    ti = [a.index.get_loc(t) for t in valid_readings['to']]
    fi = [a.index.get_loc(f) for f in valid_readings['from']]

    plsq = leastsq(residual, xpp, args=(xref, fi, ti, dm, len(points)))

    est = pd.DataFrame({'ew':plsq[0][len(points):], 'ns':plsq[0][:len(points)]}, index=names)
    est['type'] = points['type']

    all_points = pd.concat((est, refs))

    nsp = all_points.loc[valid_readings['to']]['ns'].values - dm.real
    ewp = all_points.loc[valid_readings['to']]['ew'].values - dm.imag

    nse = all_points.loc[valid_readings['from']]['ns'].values - nsp
    ewe = all_points.loc[valid_readings['from']]['ew'].values - ewp

    readings.loc[valid,'dev'] = np.sqrt(nse**2 + ewe**2)
    readings.loc[~valid,'dev'] = np.nan
    
    return est




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


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from matplotlib.path import Path
import matplotlib.patches as patches

def show_hull(points, ax):
    """Add a polygon to a plot that contains all the points.
    
    This seems like a lot of work...
    """
    hull = ConvexHull(points)
    vertices = hull.vertices
    vertices = np.append(vertices, vertices[0])
    codes = [Path.LINETO] * len(vertices)
    codes[0] = Path.MOVETO
    codes[-1] = Path.CLOSEPOLY
    
    path = Path(points[vertices], codes)
    patch = patches.PathPatch(path, facecolor='orange', lw=0, alpha=0.3)
    
    ax.add_patch(patch)
    
    




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
        

