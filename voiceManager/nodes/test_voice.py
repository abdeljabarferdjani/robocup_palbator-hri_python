#!/usr/bin/python

import pyttsx3
import rospy
from std_msgs.msg import String
import threading
from voiceManager.srv import SendVocalCommand, SendVocalCommandResponse
from voiceManager.msg import VocalDataType
import time
class VoiceGenerator(object):

    def __init__(self):
        rospy.init_node("voice_generator",anonymous=True)
        # self.sub_asr_result=rospy.Subscriber("/result_asr",String,self.handle_asr_result)
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        # self.rospy_rate=rospy.Rate(0.5)
        self.lock=threading.Lock()
        self.vocal_command=None
        self.vocal_service=rospy.Service('vocal_command_service',SendVocalCommand,self.handle_vocal_service)
        for voice in self.voices: 
            # to get the info. about various voices in our PC  
            if voice.name=="english":
                self.engine.setProperty('voice',voice.id)
                break
        self.rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', self.rate-50)

    def setup_vocal_engine(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        for voice in self.voices: 
            # to get the info. about various voices in our PC  
            if voice.name=="english":
                self.engine.setProperty('voice',voice.id)
                break
        self.rate = self.engine.getProperty('rate')

    def handle_vocal_service(self,req):
        data=req.vocal_command
        print("DATA: "+str(data))
        

        if data != "":
            self.setup_vocal_engine()
            time.sleep(1)
            self.engine.say(data)
            self.engine.runAndWait()
            return SendVocalCommandResponse(True)
        
        

if __name__=="__main__":
    x=VoiceGenerator()
    while not rospy.is_shutdown():
        rospy.spin()

