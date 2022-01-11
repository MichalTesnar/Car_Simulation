# misc functions
import os
import pygame
from math import sin, radians, degrees, copysign
from pygame.math import Vector2
import time
import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import splprep, splev
import pandas as pd

from cone import *

import sys
sys.path.append(os.path.abspath(os.path.join('..', 'Moving_Car')))


def load_existing_map(name):
    
    left_cones = []
    right_cones = []

    current_dir = os.getcwd()
    map_path = os.path.join(current_dir, f"levels generated/{name}.csv")
    map_file = pd.read_csv(map_path)
    
    for i in range(len(map_file.iloc[:,0])):
        if map_file['Cone_Type'].iloc[i] == 'LEFT':

            left_cone = Cone(map_file['Cone_X'].iloc[i],map_file['Cone_Y'].iloc[i], Side.LEFT)
            left_cones.append(left_cone)
            # mouse_pos_list.append((map_file['Cone_X'].iloc[i]*ppu,map_file['Cone_Y'].iloc[i]*ppu))             
        
        else:
            right_cone = Cone(map_file['Cone_X'].iloc[i],map_file['Cone_Y'].iloc[i], Side.RIGHT)
            right_cones.append(right_cone)
            # mouse_pos_list.append((map_file['Cone_X'].iloc[i]*ppu,map_file['Cone_Y'].iloc[i]*ppu))             
        
    
    return left_cones, right_cones

























