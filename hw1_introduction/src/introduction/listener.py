from email import message
from tkinter import Spinbox
import numpy as np
import rospy

# Import necessary message type
# BEGIN QUESTION 4.3
"*** REPLACE THIS LINE ***"
from geometry_msgs.msg import PoseStamped
# END QUESTION 4.3


def norm_python(data):
    """Compute the norm for each row of a numpy array using Python for loops.

    >>> data = np.array([[3, 4],
    ...                  [5, 12]])
    >>> norm_python(data)
    array([ 7., 17.])
    """
    n, d = data.shape
    norm = np.zeros(n) # Create an array of all zeros
    # You can use np.absolute
    # BEGIN QUESTION 4.1

    for i in range(n):
        sum = 0
        for j in range(d):
            sum += np.abs(data[i,j])
        norm[i] = sum
        
        
    # END QUESTION 4.1
    return norm


def norm_numpy(data):
    """Compute the norm for each row of a numpy array using numpy functions.

    >>> data = np.array([[3, 4],
    ...                  [5, 12]])
    >>> norm_numpy(data)
    array([ 7., 17.])
    """
    n, d = data.shape
    norm = np.zeros(n)
    # You can use np.linalg.norm.
    # Hint: you may find the `axis` parameter useful.
    # BEGIN QUESTION 4.2

    # ord: L1 norm
    # axis: Process by row vector, find the norm of multiple row vectors

    norm= np.linalg.norm(data, ord=1, axis=1)

    # END QUESTION 4.2
    return norm


class PoseListener:
    """Collect car poses."""

    def __init__(self, size=100):
        self.size = size
        self.done = False
        self.storage = []  # a list of (x, y) tuples
        # Create a subscriber for the car pose. Spend too much time here, just need to create subscriber:)
        # Hint: once you've figured out the right message type, don't forget to
        # import it at the top! If the message type from `rostopic info` is
        # "X_msgs/Y", the Python import would be "from X_msgs.msg import Y".
        # BEGIN QUESTION 4.3
        "*** REPLACE THIS LINE ***"

        # /car/car_pose -> Type:geometry_msgs/PoseStamped
        self.subscriber = rospy.Subscriber("/car/car_pose", PoseStamped, self.callback)
        

        # END QUESTION 4.3

    def callback(self, msg):
        """Store the x and y coordinates of the car."""
        header = msg.header
        rospy.loginfo(
            "Received a new message with timestamp " + str(header.stamp.secs) + "(s)"
        )

        # Extract and store the x and y position from the message data
        # BEGIN QUESTION 4.4
        "*** REPLACE THIS LINE ***"
        
        x = msg.pose.position.x
        y = msg.pose.position.y
        self.storage.append((x, y))

        # END QUESTION 4.4
        if len(self.storage) == self.size:
            self.done = True
            rospy.loginfo("Received enough samples, trying to unsubscribe")
            self.subscriber.unregister()
