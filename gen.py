import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import leastsq

#    radius = np.csc(angle / 2) * edge_len

def make_ref_points(radius, num):
    angle = np.linspace(start=0, stop=2*np.pi, num=num, endpoint=False)
    ns = radius * np.cos(angle)
    ew = radius * np.sin(angle)
    names = ['R{}'.format(chr(ord('a') + i)) for i in range(num)]

    refs = pd.DataFrame({'ns':ns, 'ew':ew, 'name':names})
    return refs


def gen_points(edge_len, refs, Np, Nme, err):

    Nr = 4
    Nt = Np + Nr

    fp = np.repeat(np.arange(Nr, Nt, dtype=int), Nme)
    offset = np.random.randint(1, Nt, (Np * Nme))
    tp = np.mod(fp + offset, Nt)

    ns = edge_len * np.random.rand(Np)
    ew = edge_len * np.random.rand(Np)

    ans = np.hstack((refs['ns'], ns))
    aew = np.hstack((refs['ew'], ew))


    nsd = ans[tp] - ans[fp] + np.random.randn(Np * Nme) * err
    ewd = aew[tp] - aew[fp] + np.random.randn(Np * Nme) * err

    dist = np.sqrt(nsd**2 + ewd**2)
    azim = 360 * np.arctan2(ewd, nsd) / (2 * np.pi)

    readings = pd.DataFrame(data={'from':fp, 'to':tp, 'hdist':dist, 'azim':azim})

    names = ['T{:02}'.format(i+Nr) for i in range(Np)]
    points = pd.DataFrame({'ns':ns, 'ew':ew, 'name':names})

    return points, readings


def residual(x, xref, f, t, dm, Np):
    xcomp = x[:Np] + 1j * x[Np:]
    xall = np.hstack((xref,xcomp))
    xt = xall[t]
    xf = xall[f]

    err = np.abs(dm - (xt - xf))
    return err


def solve(refs, readings, Np):
    xpp = np.zeros(2 * Np)
    xref = refs['ns'] + 1j * refs['ew']
    angle = np.pi * readings['azim'].values / 180
    dist = readings['hdist'].values
    dm = dist * np.exp(1j * angle)
    plsq = leastsq(residual, xpp, args=(xref, readings['from'], readings['to'], dm, Np))

    est = pd.DataFrame({'ns':plsq[0][:Np], 'ew':plsq[0][Np:]})

    return est


def stuff(readings, refs, points, anchor_to):
    angle = np.pi * readings['azim'].values / 180
    dist = readings['hdist'].values

    ns = np.hstack((refs['ns'], points['ns']))
    ew = np.hstack((refs['ew'], points['ew']))

    nsf = ns[readings['from']]
    ewf = ew[readings['from']]

    nst = ns[readings['to']]
    ewt = ew[readings['to']]

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
    names = refs['name']
    for i in range(len(ns)):
        plt.text(ew[i], ns[i], names[i])

    if actual is not None:
        plt.scatter(actual['ew'], actual['ns'], marker='o', c='y', s=100)
        ns = actual['ns']
        ew = actual['ew']
        names = actual['name']
        for i in range(len(ns)):
            plt.text(ew[i], ns[i], names[i], ha='center', va='center')

    if est is not None:
        plt.scatter(est['ew'], est['ns'], marker='o', c='r', s = 20)

