import numpy as np
import pandas as pd
from scipy.optimize import leastsq

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
    


