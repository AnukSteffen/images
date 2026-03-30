#-- coding:UTF-8 --
"""
Reinforcement learning RIS-assisted UAV system.
Adapted for Python 3.9.25

This script is the environment part of the RIS-assisted UAV system.
The RL is in RL_brain.py.

Paper: "3D-Trajectory Design and Phase-Shift for RIS-Assisted UAV Communication using Deep Reinforcement Learning"
by Haibo Mei, Kun Yang, Qiang Liu, Kezhi Wang;
"""
import numpy as np
import random as rd
import time
import math as mt
import sys
import copy
from scipy.interpolate import make_interp_spline
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
import matplotlib.pyplot as plt

if sys.version_info.major == 2:
    import Tkinter as tk
else:
    import tkinter as tk

UNIT = 1              
IOT_H = 100           
IOT_W = 100           
Max_Hight = 100       
Min_Hight = 30        

D_k = 512 
t_min = 1
t_max = 3

B = 2000  
N_0 = mt.pow(10, ((-169 / 3) / 10))
Xi = mt.pow(10, (3/10))  
a = 9.61
b = 0.16
eta_los = 0.01  
eta_nlos = 0.2  
A = eta_los - eta_nlos
C = 0.2 * np.log10(4 * np.pi * 9 / 3) + eta_nlos
Power = 0.5 * mt.pow(10, 3)  

W_R = [50, 50]  
Z_R = 50         
M = 20           


class RIS_UAV(object):
    def __init__(self):
        super(RIS_UAV, self).__init__()
        self.N_slot = 600 
        self.x_s = 10
        self.y_s = 10
        self.h_s = 1
        self.GTs = 6
        self.l_o_v = 100 * self.h_s
        self.l_f_v = 100 * self.h_s
        self.l_o_h = [0, 0]
        self.l_f_h = [0, 0]
        self.eps = 60   

        self.finish = False
        self.action_space_uav_horizontal = ['n', 's', 'e', 'w', 'h']
        self.action_space_uav_vertical = ['a', 'd', 's']

        self.n_actions = len(self.action_space_uav_horizontal) * len(self.action_space_uav_vertical) * self.GTs * (np.int32(t_max/0.1) - np.int32(t_min/0.1) + 1)
        self.n_features = 3  

        self.actions = np.zeros((np.int32(self.n_actions), 1+4), dtype=np.int32)
        index = 0
        for h in range(len(self.action_space_uav_horizontal)):
            for v in range(len(self.action_space_uav_vertical)):
                for s in range(self.GTs):
                    for t in range(np.int32(t_min/0.1), np.int32((t_max)/0.1)+1):
                        self.actions[index, :] = [index, h, v, s, t]
                        index = index + 1
        self._build_ris_uav()

    def _build_ris_uav(self):
        self.d_s = np.zeros((self.N_slot, self.GTs), dtype=np.float64)
        self.energy = np.zeros((1, self.N_slot), dtype=np.float64)
        self.location = np.zeros((5, 2), dtype=np.float64)
        self.location[0, :] = [rd.randint(0, int(2*IOT_H/3)), rd.randint(0, int(2*IOT_W/3))]
        self.location[1, :] = [rd.randint(0, int(2*IOT_H/3)), rd.randint(0, int(2*IOT_W/3))]
        self.location[2, :] = [rd.randint(0, int(2*IOT_H/3)), rd.randint(0, int(2*IOT_W/3))]

        self.w_k = np.zeros((self.GTs, 2), dtype=np.float64)
        self.u_k = np.zeros((self.GTs, 1), dtype=np.float64)

        for count in range(3):
            for cou in range(2):
                g = count * 2 + cou
                self.w_k[g, 0] = self.location[count, 0] + rd.randint(20, 40)
                self.w_k[g, 1] = self.location[count, 1] + rd.randint(20, 40)

                self.w_k[g, 0] = self.w_k[g, 0] * self.x_s + self.x_s * rd.random()
                self.w_k[g, 1] = self.w_k[g, 1] * self.y_s + self.y_s * rd.random()
                self.u_k[g, 0] = D_k / 2 + (D_k / 2) * rd.random()
        return

    def reset(self):
        self.d_s = np.zeros((self.N_slot, self.GTs), dtype=np.float64)
        self.energy = np.zeros((1, self.N_slot), dtype=np.float64)
        self.h_n = 100
        self.l_n = [0, 0]
        self.finish = False
        self.slot = 0
        return np.array([self.l_n[0], self.l_n[1], self.h_n])

    def link_rate(self, gt, RIS, P_Shift):
        h = self.h_n * self.h_s
        x = self.l_n[0] * self.x_s + 0.5 * self.x_s
        y = self.l_n[1] * self.y_s + 0.5 * self.y_s
        d = np.sqrt(mt.pow(h, 2) + mt.pow(x - self.w_k[gt, 0], 2) + mt.pow(y - self.w_k[gt, 1], 2))

        d_ug = np.sqrt(mt.pow(h, 2) + mt.pow(x - self.w_k[gt, 0], 2) + mt.pow(y - self.w_k[gt, 1], 2))
        d_ur = np.sqrt(mt.pow(h - Z_R, 2) + mt.pow(W_R[0] - x, 2) + mt.pow(W_R[1] - y, 2))
        d_rg = np.sqrt(mt.pow(Z_R, 2) + mt.pow(W_R[0] - self.w_k[gt, 0], 2) + mt.pow(W_R[1] - self.w_k[gt, 1], 2))

        if (np.sqrt(mt.pow(x - self.w_k[gt, 0], 2) + mt.pow(y - self.w_k[gt, 1], 2)) > 0):
            ratio = h / np.sqrt(mt.pow(x - self.w_k[gt, 0], 2) + mt.pow(y - self.w_k[gt, 1], 2))
        else:
            ratio = np.Inf

        p_los = 1 + a * mt.pow(np.exp(1), (a * b - b * np.arctan(ratio) * (180 / np.pi)))
        p_los = 1 / p_los
        
        if (RIS == True) & (P_Shift == True):
            g_los = p_los * Power * mt.pow(Xi / (B * N_0 * d_ug), 2)
            g_nlos = (1 - p_los) * Power * mt.pow(M * Xi / (B * N_0 * d_ur * d_rg), 2)
            r = B * np.log2(1 + g_los + g_nlos)
        elif (RIS == True) & (P_Shift == False):
            g_los = p_los * Power * mt.pow(Xi / (B * N_0 * d_ug), 2)
            phase_shift = 0
            for m in range(M):
                angle_dif = np.abs((0.5 * m * ((W_R[0] - self.w_k[gt, 0]) / d_rg - (W_R[0] - x) / d_ur) * (2 * np.pi)))
                phase_shift = phase_shift + mt.sin((angle_dif / 180) * mt.pi)
            g_nlos = (1 - p_los) * Power * mt.pow(phase_shift * Xi / (B * N_0 * d_ur * d_rg), 2)
            r = B * np.log2(1 + g_los + g_nlos)
        else:
            L_km = A * p_los + C
            r = B * np.log2(1 + Power * mt.pow(L_km / (B * N_0 * d), 2))
        
        return r / 1000

    def step(self, action, slot, RIS, P_Shift):
        self.finish = True
        h = action[1]
        v = action[2]
        c_n = action[3]
        t_n = action[4]

        pre_l_n = self.l_n
        pre_h_n = self.h_n

        self.OtPoI = 0
        if v == 0:   
            self.h_n = self.h_n + 1
            if self.h_n > Max_Hight:
                self.h_n = self.h_n - 1
                self.OtPoI = 1
        elif v == 1:   
            self.h_n = self.h_n - 1
            if self.h_n < Min_Hight:
                self.h_n = self.h_n + 1
                self.OtPoI = 1
        elif v == 2:   
            self.h_n = self.h_n

        if h == 0:  
            self.l_n[1] = self.l_n[1] + 1
            if self.l_n[1] > IOT_H:
                self.l_n[1] = self.l_n[1] - 1
                self.OtPoI = 1
        elif h == 1:  
            self.l_n[1] = self.l_n[1] - 1
            if self.l_n[1] < 0:
                self.l_n[1] = self.l_n[1] + 1
        elif h == 2:  
            self.l_n[0] = self.l_n[0] + 1
            if self.l_n[0] > IOT_W:
                self.l_n[0] = self.l_n[0] - 1
                self.OtPoI = 1
        elif h == 3:   
            self.l_n[0] = self.l_n[0] - 1
            if self.l_n[0] < 0:
                self.l_n[0] = self.l_n[0] + 1
                self.OtPoI = 1
        elif h == 4:   
            self.l_n[0] = self.l_n[0]
            self.l_n[1] = self.l_n[1]

        EE = np.zeros((1, self.GTs), dtype=np.float64)
        self.energy[0, slot] = self.flight_energy_slot(pre_l_n, self.l_n, pre_h_n, self.h_n, t_n) / 1000
        for g in range(self.GTs):
            if (g == c_n):
                self.d_s[slot, g] = self.d_s[slot, g] + self.link_rate(g, RIS, P_Shift) * (t_n / 10)
            cumulative_through = sum(self.d_s[:, g])
            cumulative_energy = sum(self.energy[0, :])
            EE[0, g] = cumulative_through / cumulative_energy
            if (cumulative_through < self.u_k[g, 0]):
                self.finish = False

        reward = np.sum(EE[0, :])
        if self.OtPoI == 1:
            reward = reward / 100
        _state = np.array([self.l_n[0], self.l_n[1], self.h_n])
        return _state, reward

    def find_action(self, index):
        return self.actions[index, :]

    def flight_energy_slot(self, pre_l_n, l_n, pre_h, h, t_n):
        d_o = 0.6
        rho = 1.225
        s = 0.05
        G = 0.503
        U_tip = 120
        v_o = 4.3
        omega = 300
        R = 0.4
        delta = 0.012
        k = 0.1
        W = 20
        P0 = (delta / 8) * rho * s * G * (pow(omega, 3)) * (pow(R, 3))
        P1 = (1 + k) * (pow(W, (3 / 2)) / np.sqrt(2 * rho * G))
        P2 = 11.46

        x_pre = pre_l_n[0] * self.x_s + 0.5 * self.x_s
        y_pre = pre_l_n[1] * self.y_s + 0.5 * self.y_s
        z_pre = pre_h * self.h_s
        x = l_n[0] * self.x_s + 0.5 * self.x_s
        y = l_n[1] * self.y_s + 0.5 * self.y_s
        z = h * self.h_s

        d = np.sqrt((x_pre - x) ** 2 + (y_pre - y) ** 2)
        h_dist = np.abs(z_pre - z)
        v_h = d / t_n
        v_v = h_dist / t_n
        Energy_uav = t_n * P0 * (1 + 3 * np.power(v_h, 2) / np.power(U_tip, 2)) + t_n * (1 / 2) * d_o * rho * s * G * np.power(v_h, 3) + \
                     t_n * P1 * np.sqrt(np.sqrt(1 + np.power(v_h, 4) / (4 * np.power(v_o, 4))) - np.power(v_h, 2) / (2 * np.power(v_o, 2))) + P2 * v_v * t_n
        return Energy_uav

    def flight_energy(self, UAV_trajectory, UAV_flight_time, EP, slot):
        d_o = 0.6
        rho = 1.225
        s = 0.05
        G = 0.503
        U_tip = 120
        v_o = 4.3
        omega = 300
        R = 0.4
        delta = 0.012
        k = 0.1
        W = 20
        P0 = (delta / 8) * rho * s * G * (pow(omega, 3)) * (pow(R, 3))
        P1 = (1 + k) * (pow(W, (3 / 2)) / np.sqrt(2 * rho * G))
        Energy_uav = np.zeros((EP, self.N_slot), dtype=np.float64)
        P2 = 11.46
        count = 0
        for ep in range(self.eps - EP, self.eps):
            horizontal = UAV_trajectory[ep, :, [0, 1]]
            vertical = UAV_trajectory[ep, :, -1]
            t_n = UAV_flight_time[ep, :]
            t_n = t_n / 10

            for i in range(slot[0, ep]):
                if (i == 0):
                    d = np.sqrt((horizontal[0, i] - self.l_o_h[0])**2 + (horizontal[1, i] - self.l_o_h[1])**2)
                    h_dist = np.abs(vertical[i] - vertical[0])
                else:
                    d = np.sqrt((horizontal[0, i] - horizontal[0, i-1])**2 + (horizontal[1, i] - horizontal[1, i-1])**2)
                    h_dist = np.abs(vertical[i] - vertical[i - 1])

                v_h = d / t_n[i]
                v_v = h_dist / t_n[i]
                Energy_uav[count, i] = t_n[i] * P0 * (1 + 3 * np.power(v_h, 2) / np.power(U_tip, 2)) + t_n[i] * (1 / 2) * d_o * rho * s * G * np.power(v_h, 3) + \
                                       t_n[i] * P1 * np.sqrt(np.sqrt(1 + np.power(v_h, 4) / (4 * np.power(v_o, 4))) - np.power(v_h, 2) / (2 * np.power(v_o, 2))) + P2 * v_v * t_n[i]
            count = count + 1
        return Energy_uav

    def UAV_FLY(self, UAV_trajectory, Slot):
        for slot in range(Slot):
            UAV_trajectory[slot, 0] = UAV_trajectory[slot, 0] * self.x_s + 0.5 * self.x_s
            UAV_trajectory[slot, 1] = UAV_trajectory[slot, 1] * self.y_s + 0.5 * self.y_s
            UAV_trajectory[slot, 2] = UAV_trajectory[slot, 2] * self.h_s

        for slot in range(2, Slot):
            diff = np.abs(UAV_trajectory[slot, 0] - UAV_trajectory[slot-2, 0]) + np.abs(UAV_trajectory[slot, 1] - UAV_trajectory[slot-2, 1])
            if (diff > self.x_s):
                UAV_trajectory[slot - 1, 0] = (UAV_trajectory[slot-2, 0] + UAV_trajectory[slot, 0]) / 2
                UAV_trajectory[slot - 1, 1] = (UAV_trajectory[slot - 2, 1] + UAV_trajectory[slot, 1]) / 2
        return UAV_trajectory

    def throughput(self, UAV_trajectorys, UAV_flight_time, GT_schedule, EP, RIS, P_Shift, Slot):
        through = np.zeros((EP, self.N_slot), dtype=np.float64)
        rate = np.zeros((EP, self.N_slot), dtype=np.float64)
        count = 0
        for ep in range(self.eps - EP, self.eps):
            r_kn = np.zeros((self.N_slot, self.GTs), dtype=np.float64)
            t_n = UAV_flight_time[ep, :]
            UAV_trajectory = UAV_trajectorys[ep, :]
            for i in range(Slot[0, ep]):
                schedule = GT_schedule[ep, i]
                for g in range(self.GTs):
                    if (schedule == g):
                        h = UAV_trajectory[i, 2]
                        x = UAV_trajectory[i, 0]
                        y = UAV_trajectory[i, 1]

                        d = np.sqrt(mt.pow(h, 2) + mt.pow(x - self.w_k[g, 0], 2) + mt.pow(y - self.w_k[g, 1], 2))
                        d_ug = np.sqrt(mt.pow(h, 2) + mt.pow(x - self.w_k[g, 0], 2) + mt.pow(y - self.w_k[g, 1], 2))
                        d_ur = np.sqrt(mt.pow(h - Z_R, 2) + mt.pow(W_R[0] - x, 2) + mt.pow(W_R[1] - y, 2))
                        d_rg = np.sqrt(mt.pow(Z_R, 2) + mt.pow(W_R[0] - self.w_k[g, 0], 2) + mt.pow(W_R[1] - self.w_k[g, 1], 2))

                        if (np.sqrt(mt.pow(x - self.w_k[g, 0], 2) + mt.pow(y - self.w_k[g, 1], 2)) > 0):
                            ratio = h / np.sqrt(mt.pow(x - self.w_k[g, 0], 2) + mt.pow(y - self.w_k[g, 1], 2))
                        else:
                            ratio = np.Inf

                        p_los = 1 + a * mt.pow(np.exp(1), (a * b - b * np.arctan(ratio) * (180 / np.pi)))
                        p_los = 1 / p_los
                        if (RIS == True) & (P_Shift == True):
                            g_los = p_los * Power * mt.pow(Xi / (B * N_0 * d_ug), 2)
                            g_nlos = (1 - p_los) * Power * mt.pow(M * Xi / (B * N_0 * d_ur * d_rg), 2)
                            r = B * np.log2(1 + g_los + g_nlos)
                        elif (RIS == True) & (P_Shift == False):
                            g_los = p_los * Power * mt.pow(Xi / (B * N_0 * d_ug), 2)
                            phase_shift = 0
                            for m in range(M):
                                angle_dif = np.abs(0.5 * m * ((W_R[0] - self.w_k[g, 0]) / d_rg - (W_R[0] - x) / d_ur) * (2 * np.pi))
                                phase_shift = phase_shift + mt.sin((angle_dif / 180) * mt.pi)
                            g_nlos = (1 - p_los) * Power * mt.pow(phase_shift * Xi / (B * N_0 * d_ur * d_rg), 2)
                            r = B * np.log2(1 + g_los + g_nlos)
                        else:
                            L_km = A * p_los + C
                            r = B * np.log2(1 + Power * mt.pow(L_km / (B * N_0 * d), 2))

                        r_kn[i, g] = r / 1000
                        rate[count, i] = rate[count, i] + r_kn[i, g]
                        through[count, i] = through[count, i] + (t_n[i] / 10) * rate[count, i]
            count = count + 1
        return through, rate