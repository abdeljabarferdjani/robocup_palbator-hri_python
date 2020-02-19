#!/usr/bin/python

import rospy
from std_msgs.msg import String
# from rospy_message_converter import json_message_converter
import json

class TestROS(object):
    def __init__(self):
        rospy.init_node("test",anonymous=True)
        # self.sub=rospy.Subscriber("test_JSON",String,self.handle_sub)
        self.pub=rospy.Publisher("SendData",String,queue_size=10)
        self.pub2=rospy.Publisher("SendData",String,queue_size=10)
        self.rate=rospy.Rate(1)

    def publisher(self):
        x={u'dataToUse': u'ETI', u'index': 2}
        json_str=json.dumps(x)
        # y={u'dataToUse': u'false', u'index': 3}
        # json_str2=json.dumps(y)
        
        self.pub.publish(json_str)
        # self.pub2.publish(json_str2)
        


    # def handle_sub(self,req):
    #     json_str=json_message_converter.convert_ros_message_to_json(String(req.data))
    #     d=json.loads(json_str)
    #     print(type(d))
    #     print(d)
    #     print("try ", d['data'])

if __name__=="__main__":
    x=TestROS()
    while not rospy.is_shutdown():
        x.publisher()
        x.rate.sleep()