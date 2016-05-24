import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import leastsq

def gen_points_and_readings(edge_len, num_est, rpp, err):
    refs = gen_ref_points(edge_len)
    refs['type'] = 'anchor'
    refs['locked'] = True
    actual = gen_meas_points(edge_len, num_est)
    actual['type'] = 'tree'
    actual['locked'] = False
    readings = gen_readings(refs, actual, rpp, err)
    
    unknown = actual.copy()
    unknown[['ew','ns']] = np.nan
    points = pd.concat((refs, unknown))
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


def residual(coord_vec, vec_map, point_coords, from_point, to_point, from_to_delta):
    """Callback for scipy.optimize.leastsq() to place points
    
    
    """
    # Write the iterated coordinates back into the DataFrame
    num_points = len(coord_vec) / 2
    point_coords.loc[vec_map,'ew'] = coord_vec[num_points:]
    point_coords.loc[vec_map,'ns'] = coord_vec[:num_points]
        
    err = point_coords.loc[from_point].values + from_to_delta.values - point_coords.loc[to_point].values
    
    return err.flatten()


def place_unlocked_points(points, readings):
    """
    :param points: list of all points.  Updated by function
    :type points: pandas.DataFrame
    
    
    *points* is updated.
    *readings* is updated.
    
    """
    valid = readings['invalid'] == False
    valid_readings = readings[valid]
    names = points.index
    
    locked = points['locked']
    fluid_points = points[~locked]
    
    # Construct a flat numpy array of coordinates
    xpp = np.hstack((fluid_points['ew'].values, fluid_points['ns'].values)) #TEMP!!!  leastsq flattens
    xpp = np.nan_to_num(xpp)

    angle = np.pi * valid_readings['azim'].values / 180
    dist = valid_readings['hdist'].values
    from_to_delta = pd.DataFrame({'ew': dist * np.sin(angle), 'ns': dist * np.cos(angle)})

    point_coords = points[['ew','ns']].copy()
    args = (~locked, point_coords, valid_readings['from'], valid_readings['to'], from_to_delta)
    plsq = leastsq(residual, xpp, args=args)

    ew = plsq[0][len(fluid_points):]
    ns = plsq[0][:len(fluid_points)]

    points.loc[~locked, 'ew'] = ew
    points.loc[~locked, 'ns'] = ns
    
    est_of_readings = points.loc[valid_readings['to'],['ew','ns']].values - from_to_delta.values
    deviation = points.loc[valid_readings['from'],['ew','ns']].values - est_of_readings

    readings.loc[valid,'dev'] = np.sqrt(deviation[:,0] ** 2 + deviation[:,1] ** 2)

    readings.loc[~valid,'dev'] = np.nan
    


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
        

