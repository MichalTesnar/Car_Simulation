from math import sin, radians, degrees, copysign
from pygame.math import Vector2
import numpy as np
from enum import Enum

class Side(Enum):
    LEFT = 1
    RIGHT = 2

class Cone:
    def __init__(self, x, y, category):
        self.position = Vector2(x, y)
        self.image = {Side.LEFT: None, Side.RIGHT: None}    
        self.visible = False   
        self.in_fov = False
        self.category = category
        self.dist_car = 10**10
        self.alpha = 0

        self.cone_list = {Side.LEFT:[], Side.RIGHT: []}
        self.polar_cone_list = []
        self.visible_cone_list = {Side.LEFT:[], Side.RIGHT: []}
        self.new_visible_cone_flag = {}
        self.first_cone_found = {Side.LEFT: False, Side.RIGHT: False}
        self.first_visible_cone = {Side.LEFT: 0, Side.RIGHT: 0}

    def update_cone_list(self): 
        self.polar_cone_list = []       
        for category in Side:
            initial_length = len(self.visible_cone_list[category]) 
            self.visible_cone_list[category] = []

            for cone in self.cone_list[category]:
                self.polar_cone_list.append([cone.alpha, cone.dist_car, cone.category])
                if cone.visible == True:
                    self.visible_cone_list[category].append(cone)

            if initial_length != len(self.visible_cone_list[category]):
                self.new_visible_cone_flag[category] = True
            else:
                self.new_visible_cone_flag[category] = False
        
    def update(self, pp, time_running): 
        
        #distance to car
        self.dist_car = np.linalg.norm(self.position - pp.car.position)
        
        #calculating angle between car angle and cone (alpha)
        a_b = self.position - pp.car.position
        a_b = np.transpose(np.matrix([a_b.x,-1*a_b.y ]))
        rotate = np.matrix([[np.cos(-pp.car.angle*np.pi/180),-1*np.sin(-pp.car.angle*np.pi/180)],
                            [np.sin(-pp.car.angle*np.pi/180),np.cos(-pp.car.angle*np.pi/180)]])
        a_b = rotate*a_b
        a = a_b[0]
        b = a_b[1]
        beta = np.arctan(b/a)*(180/np.pi)
        alpha = beta + 90*(b/np.abs(b))*np.abs((a/np.abs(a)) - 1)
        self.alpha = alpha[0,0]

        #if cone within car fov, set to visible
        if self.dist_car < pp.car.fov / pp.ppu and pp.car.auto == True and np.abs(self.alpha) < pp.car.fov_range:
            self.visible = True
            self.in_fov = True
        else:
            #self.visible = False #commenting this line allows cones to be remembered
            self.in_fov = False