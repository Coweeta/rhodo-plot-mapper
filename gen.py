import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import leastsq

def gen_ref_points(edge_len):
    e = edge_len
    refs = pd.DataFrame({'ns':[0, 0, e, e], 'ew':[0, e, 0, e]} , index=['RA', 'RB', 'RC', 'RD'])
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

    readings = pd.DataFrame(data={'from':names[fp], 'to':names[tp], 'hdist':dist, 'azim':azim})

    return readings


def residual(x, xref, f, t, dm, Np):
    xcomp = x[:Np] + 1j * x[Np:]
    xall = np.hstack((xcomp, xref))
    xt = xall[t]
    xf = xall[f]

    err = np.abs(dm - (xt - xf))
    return err


def solve(refs, readings, points):
    names = points.index
    xpp = np.hstack((points['ew'].values, points['ns'].values))

    xref = refs['ns'] + 1j * refs['ew']
    angle = np.pi * readings['azim'].values / 180
    dist = readings['hdist'].values
    dm = dist * np.exp(1j * angle)

    a = pd.concat((points, refs))
    ti = [a.index.get_loc(t) for t in readings['to']]
    fi = [a.index.get_loc(f) for f in readings['from']]

    plsq = leastsq(residual, xpp, args=(xref, fi, ti, dm, len(points)))

    est = pd.DataFrame({'ew':plsq[0][len(points):], 'ns':plsq[0][:len(points)]}, index=names)

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


def show_map(fig, refs, readings=None, meas=None, pts=None, actual=None, est=None):
    ax = fig.add_subplot(111, aspect='equal')
    if readings is not None and pts is not None:
        rf = readings[readings['from']==pts]
        nsf, ewf, nst, ewt = stuff(rf, refs, actual, anchor_to=True)
        plt.plot([ewf, ewt], [nsf, nst], 'g-')
        rf = readings[readings['from']==pts]
        nsf, ewf, nst, ewt = stuff(rf, refs, actual, anchor_to=False)
        plt.plot([ewf, ewt], [nsf, nst], 'r-')

    #for i in range(len(xcomp)):
    #    plt.plot([actual_points[i].real,xcomp[i].real], [actual_points[i].imag,xcomp[i].imag], 'r-')

    plt.scatter(refs['ew'], refs['ns'], marker='^', c='g', s=100)
    ns = refs['ns']
    ew = refs['ew']
    names = refs.index
    for i in range(len(ns)):
        plt.text(ew[i], ns[i], names[i])

    if actual is not None:
        if est is not None:
            plt.plot(
                [est['ew'], actual['ew']],
                [est['ns'], actual['ns']],
                'y-')
        plt.scatter(actual['ew'], actual['ns'], marker='o', c='y', s=100)
        ns = actual['ns']
        ew = actual['ew']
        names = actual.index
        for i in range(len(ns)):
            plt.text(ew[i], ns[i], names[i], ha='center', va='center')

    if est is not None:
        plt.scatter(est['ew'], est['ns'], marker='o', c='r', s = 20)

