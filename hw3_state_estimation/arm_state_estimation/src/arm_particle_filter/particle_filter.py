from dis import dis
from math import dist
import random
from sre_parse import State
import sys
from threading import Lock

import cv2
import numpy as np
from numpy.random import uniform

from arm_particle_filter.resampler import LowVarianceSampler

random.seed(42)
np.random.seed(42)


class ParticleFilter:
    def __init__(self, mean, cov, num_particles, std_u):
        self.std_u = std_u
        self._init_mean = mean
        self._init_cov = cov
        self.num_particles = num_particles
        self.lock = Lock()
        self.particles = np.zeros((self.num_particles, 2))
        self.weights = None
        self.reset()
        self.resampler = LowVarianceSampler(
            self.particles, self.weights, self.lock)

    def reset(self):
        """Initialize particles and weights.
        """
        for i in range(self.num_particles):
            self.particles[i, :] = np.random.multivariate_normal(
                self._init_mean.ravel(), self._init_cov)
        self.weights = np.ones(self.num_particles) / self.num_particles

    def predict(self, u):
        """Apply constant velocity motion model to the particles

        Args:
            u (np.array): x and y velocity (of shape (2,))
        """
        dt = 0.1
        self.particles += u * dt + np.random.normal(0, self.std_u, size=(self.num_particles, 2))
    
    def update(self, z):
        """Update the state estimate after receiving an observation.
        self.weights should be modified in-place.

        Args:
            z: detector observation
        """
        # use distance formula
        distance = np.sqrt(np.square(self.particles[:,0] - z[0]) + np.square(self.particles[:,1] - z[1]))
        self.weights[:] = np.amax(distance) - distance
        mean, cov = self.mean_and_variance()
        return mean, cov


    def mean_and_variance(self):
        """Compute the mean and covariance matrix for a set of particles.
        """
        mean = np.average(self.particles, weights=self.weights, axis=0)
        zero_mean = self.particles - mean
        cov = np.dot(zero_mean.T, zero_mean) / self.num_particles

        return mean.reshape((-1, 1)), cov

    def draw_particles(self, frame, color=[0, 0, 255], radius=2):
        """Draw the particles on a frame and return it.

        Args:
            frame: base image frame
            radius: radius of particles
        """
        for x_particle, y_particle in self.particles.astype(int):
            cv2.circle(frame, (x_particle, y_particle),
                       radius, color, -1)  # RED: Particles
            
            
