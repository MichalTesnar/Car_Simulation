from math import sin, radians, degrees, copysign
from pygame.math import Vector2
import time
import numpy as np

from cone import Side

class Car:
    def __init__(self, x, y, angle = 0, length = 2, max_steering = 80, max_acceleration = 4.0):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0.0, 0.0)
        self.angle = angle
        self.length = length
        self.max_acceleration = max_acceleration
        self.max_steering = max_steering
        self.max_velocity = 5
        self.brake_deceleration = 4
        self.free_deceleration = 1
        self.car_image = None
        self.crashed = False

        self.acceleration = 0.0
        self.steering_angle = 0.0
        self.fov = 175 #150
        self.turning_sharpness = 1.8
        self.breaks = True
        self.fov_range = 60
        self.auto = False
        self.headlights = False

    def config_angle(self):
        # car angle between (-180,180)
        temp_sign = np.mod(self.angle,360)
        if temp_sign > 180:
            car_angle_sign = -1
        else:
            car_angle_sign = 1
            
        self.angle = np.mod(self.angle,180)*car_angle_sign
        
        if self.angle < 0:
            self.angle = -180 - self.angle

    #def steering(self, pp):
         #if (len(pp.target.visible_targets) > 0 
         #and np.linalg.norm(pp.target.closest_target.position-self.position) < self.fov/pp.ppu
         #and np.linalg.norm(pp.target.closest_target.position-self.position) > 20/pp.ppu
         #and self.auto == True 
         #and pp.target.closest_target.passed == False):
            
             #dist = pp.target.closest_target.dist_car
             #alpha = pp.target.closest_target.alpha
             #self.steering_angle = (self.max_steering*2/np.pi)*np.arctan(alpha/dist**self.turning_sharpness)
             #self.velocity.x = pp.cruising_speed

         #self.acceleration = max(-self.max_acceleration, min(self.acceleration, self.max_acceleration))
         #self.steering_angle = max(-self.max_steering, min(self.steering_angle, self.max_steering))



    # Car crash mechanic
    def car_crash_mechanic(self, cone_obj):
        if len(cone_obj.cone_list[Side.LEFT]) > 0 or len(cone_obj.cone_list[Side.RIGHT]) > 0:
            self.crashed = False
            
            for category in Side:
                for i in range(len(cone_obj.cone_list[category])):
                    if np.linalg.norm(tuple(x-y for x,y in zip([self.position.x, self.position.y], [cone_obj.cone_list[category][i].position.x, cone_obj.cone_list[category][i].position.y]))) < 0.4:
                        self.crashed = True
                        break

                if self.crashed:
                    break
                

    def update(self, dt):
        self.velocity += (self.acceleration * dt, 0)
        self.velocity.x = max(-self.max_velocity, min(self.velocity.x, self.max_velocity))

        if self.steering_angle:
            turning_radius = self.length / sin(radians(self.steering_angle))
            angular_velocity = self.velocity.x / turning_radius
        else:
            angular_velocity = 0

        self.position += self.velocity.rotate(-self.angle) * dt
        self.angle += degrees(angular_velocity) * dt
