#!/usr/bin/python

import rospy
from std_msgs.msg import String
import json
from HriManager.msg import DataToSay


class TestROS(object):
    def __init__(self):
        rospy.init_node("test",anonymous=True)
        # self.sub=rospy.Subscriber("test_JSON",String,self.handle_sub)
        self.pub=rospy.Publisher("CurrentView",DataToSay,queue_size=10)
        self.rate=rospy.Rate(1)

    def publisher(self):
        message=DataToSay()
        

        x={u'name': u'Wait', u'order': 3, u'eta': 0, u'speech': {u'said': u"Did you say your name was John?", u'title': u"I'm waiting for the referee"}, u'arguments': {u'time': 3}, u'action': u'confirm', u'id': u'findg1_wait'}
        json_str=json.dumps(x)
        message.json_in_string=json_str
        message.data_to_use_in_string=''
        self.pub.publish(message)

if __name__=="__main__":
    x=TestROS()
    while not rospy.is_shutdown():
        x.publisher()
        x.rate.sleep()