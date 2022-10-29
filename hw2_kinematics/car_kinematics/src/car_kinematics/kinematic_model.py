#!/usr/bin/env python
from __future__ import division
from threading import Lock
import numpy as np
from numpy.core.numeric import roll
import rospy

from std_msgs.msg import Float64

import matplotlib.pyplot as plt


class KinematicCarMotionModel:
    """The kinematic car motion model."""

    def __init__(self, car_length, **kwargs):
        """Initialize the kinematic car motion model.

        Args:
            car_length: the length of the car
            **kwargs (object): any number of optional keyword arguments:
                vel_std (float): std dev of the control velocity noise
                alpha_std (float): std dev of the control alpha noise
                x_std (float): std dev of the x position noise
                y_std (float): std dev of the y position noise
                theta_std (float): std dev of the theta noise
        """

        defaults = {
            "vel_std": 0.1,
            "alpha_std": 0.1,
            "x_std": 0.05,
            "y_std": 0.05,
            "theta_std": 0.1,
        }
        if not set(kwargs).issubset(set(defaults)):
            raise ValueError("Invalid keyword argument provided")
        # These next two lines set the instance attributes from the defaults and
        # kwargs dictionaries. For example, the key "vel_std" becomes the
        # instance attribute self.vel_std.
        self.__dict__.update(defaults)
        self.__dict__.update(kwargs)

        if car_length <= 0.0:
            raise ValueError(
                "The model is only defined for defined for positive, non-zero car lengths"
            )
        self.car_length = car_length

    def compute_changes(self, states, controls, dt, alpha_threshold=1e-2):
        """Integrate the (deterministic) kinematic car model.

        Given vectorized states and controls, compute the changes in state when
        applying the control for duration dt.

        If the absolute value of the applied alpha is below alpha_threshold,
        round down to 0. We assume that the steering angle (and therefore the
        orientation component of state) does not change in this case.

        Args:
            states: np.array of states with shape M x 3
            controls: np.array of controls with shape M x 2
            dt (float): control duration

        Returns:
            M x 3 np.array, where the three columns are dx, dy, dtheta

        """
        changes_in_statues = np.zeros_like(states, dtype=float)
        dtheta = changes_in_statues[:, 2]
        
        changes_in_statues[:, 2] = (controls[:, 0] / self.car_length) * np.tan(controls[:, 1]) * dt
        changes_in_statues[np.abs(controls[:, 1]) < alpha_threshold, 2] = 0
        changes_in_statues[:, 0] = controls[:, 0] * np.cos(states[:, 2]) * dt
        changes_in_statues[:, 1] = controls[:, 0] * np.sin(states[:, 2]) * dt
        
        t = np.abs(controls[:, 1]) >= alpha_threshold
        t_theta = states[:, 2][np.abs(controls[:, 1]) >= alpha_threshold]
        new_theta = t_theta + dtheta[t]
        val = self.car_length / np.tan(controls[:, 1])[t]
        changes_in_statues[t, 0] = val * (np.sin(new_theta) - np.sin(t_theta))
        changes_in_statues[t, 1] = val * (np.cos(t_theta) - np.cos(new_theta))
        
        return changes_in_statues

    def apply_deterministic_motion_model(self, states, vel, alpha, dt):
        """Propagate states through the determistic kinematic car motion model.

        Given the nominal control (vel, alpha
        ), compute the changes in state 
        and update it to the resulting state.

        NOTE: This function does not have a return value: your implementation
        should modify the states argument in-place with the updated states.

        >>> states = np.ones((3, 2))
        >>> states[2, :] = np.arange(2)  #  modifies the row at index 2
        >>> a = np.array([[1, 2], [3, 4], [5, 6]])
        >>> states[:] = a + a            # modifies states; note the [:]

        Args:
            states: np.array of states with shape M x 3
            vel (float): nominal control velocity
            alpha (float): nominal control steering angle
            dt (float): control duration
        """
        n_particles = states.shape[0]
        controls = np.tile(np.array([vel, alpha]),(n_particles, 1))
        state_changes = self.compute_changes(states, controls, dt)
        states += state_changes
        states[:, 2] = (states[:, 2] + np.pi) % (2 * np.pi) - np.pi
        states[states[:, 2] == -np.pi, 2] = np.pi

    def apply_motion_model(self, states, vel, alpha, dt):
        """Propagate states through the noisy kinematic car motion model.

        Given the nominal control (vel, alpha), sample M noisy controls.
        Then, compute the changes in state with the noisy controls.
        Finally, add noise to the resulting states.

        NOTE: This function does not have a return value: your implementation
        should modify the states argument in-place with the updated states.

        >>> states = np.ones((3, 2))
        >>> states[2, :] = np.arange(2)  #  modifies the row at index 2
        >>> a = np.array([[1, 2], [3, 4], [5, 6]])
        >>> states[:] = a + a            # modifies states; note the [:]

        Args:
            states: np.array of states with shape M x 3
            vel (float): nominal control velocity
            alpha (float): nominal control steering angle
            dt (float): control duration
        """
        n_particles = states.shape[0]       
        v = np.random.normal(vel, self.vel_std, n_particles)
        a = np.random.normal(alpha, self.alpha_std, n_particles)
        controls = np.stack((v, a), axis = -1)
        
        state_changes = self.compute_changes(states, controls, dt)
        
        d_x = np.random.normal(state_changes[:, 0], self.x_std, n_particles)
        d_y = np.random.normal(state_changes[:, 1], self.y_std, n_particles)
        d_theta = np.random.normal(state_changes[:, 2], self.theta_std, n_particles)
  
        states[:, 0] += d_x
        states[:, 1] += d_y 
        states[:, 2] += d_theta
        states[:, 2] = (states[:, 2] + np.pi) % (2 * np.pi) - np.pi
        states[states[:, 2] == -np.pi, 2] = np.pi
