import numpy as np
import pandas as pd

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


