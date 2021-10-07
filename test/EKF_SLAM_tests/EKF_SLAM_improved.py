"""
Extended Kalman Filter SLAM example
author: Atsushi Sakai (@Atsushi_twi)
"""

import math

import matplotlib.pyplot as plt
import numpy as np

# EKF state covariance
Cx = np.diag([0.1, 0.1, np.deg2rad(10.0)]) ** 2
Q = np.diag([0.2, np.deg2rad(1.0)]) ** 2 #measurement uncertainty (fill in measurement variance (std dev squared)). (Used to calculate Kalman gain)

#  Simulation parameter
Q_sim = np.diag([0.2, np.deg2rad(1.0)]) ** 2
R_sim = np.diag([1.0, np.deg2rad(10.0)]) ** 2

DT = 0.1  # time tick [s]
SIM_TIME = 150.0  # simulation time [s]
MAX_RANGE = 20.0  # maximum observation range
M_DIST_TH = 2.0  # Threshold of Mahalanobis distance for data association.
STATE_SIZE = 3  # State size [x,y,yaw]
LM_SIZE = 2  # LM state size [x,y]

show_animation = True


def ekf_slam(xEst, PEst, u, z):
    # Predict
    G, Fx = jacob_motion(xEst, u)
    xEst[0:STATE_SIZE] = motion_model(xEst[0:STATE_SIZE], u)
    PEst = G.T @ PEst @ G + Fx.T @ Cx @ Fx
    initP = np.eye(LM_SIZE)

    # Update
    updatelist = []
    skipList = [False for iz in range(len(z))]
    for iz in range(len(z)):  # for each observation
        min_id = search_correspond_landmark_id(xEst, PEst, z[iz, 0:2])

        nLM = calc_n_lm(xEst)
        if min_id == nLM:
            print("New LM")
            # Extend state and covariance matrix
            xAug = np.vstack((xEst, calc_landmark_position(xEst, z[iz, :])))
            PAug = np.vstack((np.hstack((PEst, np.zeros((len(xEst), LM_SIZE)))),
                              np.hstack((np.zeros((LM_SIZE, len(xEst))), initP))))
            xEst = xAug
            PEst = PAug
            skipList[iz] = True
    for iz in range(len(z[:, 0])):  # for each observation
        if(skipList[iz]):
            continue #skip this one
        min_id = search_correspond_landmark_id(xEst, PEst, z[iz, 0:2])
        
        lm = get_landmark_position_from_state(xEst, min_id)
        y, S, H = calc_innovation(lm, xEst, PEst, z[iz, 0:2], min_id)
        
        K = (PEst @ H.T) @ np.linalg.inv(S)
        updatelist.append([(K @ y), (K @ H)])
        
    if(len(updatelist)>0):
        avgKy = updatelist[0][0]; avgKH = updatelist[0][1]
        print("updatelist:", len(updatelist))
        for Ky, KH in updatelist[1:]:
            avgKy = avgKy + Ky
            avgKH = avgKH + KH
        if(len(updatelist)>1):
            avgKy = avgKy / len(updatelist)
            avgKH = avgKH / len(updatelist)
        xEst = xEst + avgKy
        PEst = (np.eye(len(xEst)) - avgKH) @ PEst

    xEst[2] = pi_2_pi(xEst[2])

    return xEst, PEst


def calc_input():
    v = 1.0  # [m/s]
    yaw_rate = 0.1  # [rad/s]
    u = np.array([[v, yaw_rate]]).T
    return u


def observation(xTrue, xd, RFID):
    u = calc_input()
    xTrue = motion_model(xTrue, u)

    # add noise to gps x-y
    z = np.zeros((0, 3))

    for i in range(len(RFID[:, 0])):

        dx = RFID[i, 0] - xTrue[0, 0]
        dy = RFID[i, 1] - xTrue[1, 0]
        d = math.hypot(dx, dy)
        angle = pi_2_pi(math.atan2(dy, dx) - xTrue[2, 0])
        if d <= MAX_RANGE:
            dn = d + np.random.randn() * Q_sim[0, 0] ** 0.5  # add noise
            angle_n = angle + np.random.randn() * Q_sim[1, 1] ** 0.5  # add noise
            zi = np.array([dn, angle_n, i])
            z = np.vstack((z, zi))

    # add noise to input
    uNoisy = np.array([[
        u[0, 0] + np.random.randn() * R_sim[0, 0] ** 0.5,
        u[1, 0] + np.random.randn() * R_sim[1, 1] ** 0.5]]).T

    xd = motion_model(xd, uNoisy)
    return xTrue, z, xd, uNoisy


def motion_model(x, u):
    F = np.array([[1.0, 0, 0],
                  [0, 1.0, 0],
                  [0, 0, 1.0]])

    B = np.array([[DT * math.cos(x[2, 0]), 0],
                  [DT * math.sin(x[2, 0]), 0],
                  [0.0, DT]])

    x = (F @ x) + (B @ u)
    return x


def calc_n_lm(x):
    n = int((len(x) - STATE_SIZE) / LM_SIZE)
    return n


def jacob_motion(x, u):
    Fx = np.hstack((np.eye(STATE_SIZE), np.zeros(
        (STATE_SIZE, LM_SIZE * calc_n_lm(x)))))
    
    jF = np.array([[1.0, 0.0, -DT * u[0, 0] * math.sin(x[2, 0])],
                   [0.0, 1.0, DT * u[0, 0] * math.cos(x[2, 0])],
                   [0.0, 0.0, 1.0]], dtype=float)

    G = Fx.T @ jF @ Fx
    
    return G, Fx,


def calc_landmark_position(x, z):
    zp = np.zeros((2, 1))

    zp[0, 0] = x[0, 0] + z[0] * math.cos(x[2, 0] + z[1])
    zp[1, 0] = x[1, 0] + z[0] * math.sin(x[2, 0] + z[1])

    return zp


def get_landmark_position_from_state(x, ind):
    lm = x[STATE_SIZE + LM_SIZE * ind: STATE_SIZE + LM_SIZE * (ind + 1), :]
    
    return lm


def search_correspond_landmark_id(xAug, PAug, zi):
    """
    Landmark association with Mahalanobis distance
    """

    nLM = calc_n_lm(xAug)

    min_dist = []
    
    newLMpos = calc_landmark_position(xAug, zi) #(thijs)

    for i in range(nLM):
        knownLMpos = get_landmark_position_from_state(xAug, i) #(thijs) changed variable name to reflect contents
        #y, S, H = calc_innovation(lm, xAug, PAug, zi, i)  #(thijs) i'm not even sure what how they calculate the distance between the known landmark pos and the new one
        #min_dist.append(y.T @ np.linalg.inv(S) @ y)       #(thijs)  i'll just ignore this and substitute my own
        delta = knownLMpos - newLMpos #(thijs) calculate x and y distance between measured landmark pos and known landmark pos
        min_dist.append(math.sqrt((delta.T @ delta)[0, 0])) #calculate distance to known landmark (A^2+B^2=C^2)

    min_dist.append(M_DIST_TH)  # new landmark    #(thijs) if this last (out of bounds!) index is the closest, it means that no sufficiently nearby landmark exists, so make a new one

    min_id = min_dist.index(min(min_dist))

    return min_id


def calc_innovation(lm, xEst, PEst, z, LMid):
    delta = lm - xEst[0:2]
    q = (delta.T @ delta)[0, 0]
    z_angle = math.atan2(delta[1, 0], delta[0, 0]) - xEst[2, 0]
    zp = np.array([[math.sqrt(q), pi_2_pi(z_angle)]])
    y = (z - zp).T
    y[1] = pi_2_pi(y[1])
    H = jacob_h(q, delta, xEst, LMid + 1)
    S = H @ PEst @ H.T + Q

    return y, S, H


def jacob_h(q, delta, x, i):
    sq = math.sqrt(q)
    G = np.array([[-sq * delta[0, 0], - sq * delta[1, 0], 0, sq * delta[0, 0], sq * delta[1, 0]],
                  [delta[1, 0], - delta[0, 0], - q, - delta[1, 0], delta[0, 0]]])

    G = G / q
    nLM = calc_n_lm(x)
    F1 = np.hstack((np.eye(3), np.zeros((3, 2 * nLM))))
    F2 = np.hstack((np.zeros((2, 3)), np.zeros((2, 2 * (i - 1))),
                    np.eye(2), np.zeros((2, 2 * nLM - 2 * i))))

    F = np.vstack((F1, F2))

    H = G @ F

    return H


def pi_2_pi(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def main():
    print(__file__ + " start!!")

    time = 0.0

    # RFID positions [x, y]
    RFID = np.array([[10.0, -2.0],
                     [15.0, 10.0],
                     [3.0, 15.0],
                     [-2.0, 14.0],
                     [13.0, 5.0],
                     [-7.0, 18.0],
                     [3.0, 15.0],
                     [-5.0, 20.0]])

    # State Vector [x y yaw v]'
    xEst = np.zeros((STATE_SIZE, 1))
    xTrue = np.zeros((STATE_SIZE, 1))
    PEst = np.eye(STATE_SIZE)

    xDR = np.zeros((STATE_SIZE, 1))  # Dead reckoning

    # history
    hxEst = xEst
    hxTrue = xTrue
    hxDR = xTrue
    min_pose_ang = 500
    max_pose_ang = 0
    while SIM_TIME >= time:
        time += DT

        xTrue, z, xDR, u = observation(xTrue, xDR, RFID)
        print("Input to SLAM")
        print("xEst: \n", xEst, "\n pEst: \n", PEst, "\n u: \n", u, "\n z: \n", z)
        xEst, PEst = ekf_slam(xEst, PEst, u, z)
        # print("Pose estimate ", xEst)
        # print(xEst[2])
        # pose angle range is [-PI, PI]
        if xEst[2, 0] > max_pose_ang:
            max_pose_ang = xEst[2, 0]
        if xEst[2, 0] < min_pose_ang:
            min_pose_ang = xEst[2, 0]
        print("min max is", min_pose_ang, max_pose_ang)
        x_state = xEst[0:STATE_SIZE]

        # store data history
        hxEst = np.hstack((hxEst, x_state))
        hxDR = np.hstack((hxDR, xDR))
        hxTrue = np.hstack((hxTrue, xTrue))

        if show_animation:  # pragma: no cover
            plt.cla()
            # for stopping simulation with the esc key.
            plt.gcf().canvas.mpl_connect(
                'key_release_event',
                lambda event: [exit(0) if event.key == 'escape' else None])

            plt.plot(RFID[:, 0], RFID[:, 1], "*k")
            plt.plot(xEst[0], xEst[1], ".r")

            # plot landmark
            for i in range(calc_n_lm(xEst)):
                plt.plot(xEst[STATE_SIZE + i * 2],
                         xEst[STATE_SIZE + i * 2 + 1], "xg")

            plt.plot(hxTrue[0, :],
                     hxTrue[1, :], "-b")
            plt.plot(hxDR[0, :],
                     hxDR[1, :], "-k")
            plt.plot(hxEst[0, :],
                     hxEst[1, :], "-r")
            plt.axis("equal")
            plt.grid(True)
            plt.pause(0.001)
    if show_animation:
        plt.pause(10)


if __name__ == '__main__':
    main()