def calculate_reward(car):
    reward = 0
 
    if car.auto:
        # if lap_reward == True and track_number > 0:
        #     reward += 100
        #     lap_reward = False
        reward += 0.1 * car.velocity.x**2/car.max_velocity
        reward += 0.005
    return reward

