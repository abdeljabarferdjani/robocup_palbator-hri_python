#!/usr/bin/env python
import socket
import time
import rospy

from std_msgs.msg import String

class ConnectionManager(object):

    def __init__(self):
        rospy.init_node('Connection_manager_node')
        self.pub=rospy.Publisher('connection_state',String,queue_size=1)
        self.rate=rospy.Rate(1)
        self.hostname_server = "one.one.one.one"

    def is_connected(self):
        try:
            # see if we can resolve the host name -- tells us if there is
            # a DNS listening
            host = socket.gethostbyname(self.hostname_server)
            # connect to the host -- tells us if the host is actually
            # reachable
            s = socket.create_connection((host, 80), 2)
            s.close()
            return True
        except:
            pass
        return False
                
            

if __name__ == "__main__":
    instance_connection=ConnectionManager()
    while not rospy.is_shutdown():
        a=instance_connection.is_connected()
        rospy.loginfo(a)
        if a==True:
            instance_connection.pub.publish("Connected")
        else:
            instance_connection.pub.publish("Disconnected")
        instance_connection.rate.sleep()

    
