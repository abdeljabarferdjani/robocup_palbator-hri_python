#!/usr/bin/python

import rospy
from std_msgs.msg import String
import json

class TestROS(object):
    def __init__(self):
        rospy.init_node("test",anonymous=True)
        # self.sub=rospy.Subscriber("test_JSON",String,self.handle_sub)
        self.pub=rospy.Publisher("CurrentView",String,queue_size=10)
        self.rate=rospy.Rate(1)

    def publisher(self):
        x={u'name': u'Wait', u'order': 2, u'eta': 0, u'speech': {u'said': u"Did you say your name was John?", u'title': u"I'm waiting for the referee"}, u'arguments': {u'time': 3}, u'action': u'confirm', u'id': u'findg1_wait'}
        json_str=json.dumps(x)
        
        self.pub.publish(json_str)

if __name__=="__main__":
    x=TestROS()
    while not rospy.is_shutdown():
        x.publisher()
        x.rate.sleep()