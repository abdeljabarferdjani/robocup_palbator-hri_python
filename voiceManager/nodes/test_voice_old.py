#!/usr/bin/python

import pyttsx3
import rospy
from std_msgs.msg import String
import threading
from own_speech_recognition.srv import SendVocalCommand, SendVocalCommandResponse
from own_speech_recognition.msg import VocalDataType
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
        # if data_to_say=="HELLO":
        #     self.setup_vocal_engine()
        #     time.sleep(1)
        #     self.engine.say("Hello Human, my name is Palbator")
        #     self.engine.runAndWait()
        #     return SendVocalCommandResponse(True)
        # elif data_to_say=="HELLO PALBATOR":
        #     self.setup_vocal_engine()
        #     time.sleep(1)
        #     self.engine.say("Hello Human, what do you want ?")
        #     self.engine.runAndWait()
        #     return SendVocalCommandResponse(True)

        if data.data_type=="names":
            self.setup_vocal_engine()
            time.sleep(1)
            self.engine.say("Hello "+str(data.vocal_output)+", my name is Palbator")
            self.engine.runAndWait()
            return SendVocalCommandResponse(True)
        
        elif data.data_type=="boisson":
            self.setup_vocal_engine()
            time.sleep(1)
            self.engine.say("You are lucky ! We have fresh "+str(data.vocal_output))
            self.engine.runAndWait()
            return SendVocalCommandResponse(True)

        else:
            return SendVocalCommandResponse(False)

        # else:
        #     self.setup_vocal_engine()
        #     time.sleep(1)
        #     self.engine.say("I didn't understand your name, can you repeat please?")
        #     self.engine.runAndWait()
        #     return SendVocalCommandResponse(True)

    # def say_dialog(self):
    #     if self.lock.acquire(False):
    #         data_result=self.vocal_command
    #         if data_result=="HELLO":
    #             self.engine.say("Hello Human, my name is Palbator")
    #             self.engine.runAndWait()
    #             print("test")
    #         elif data_result=="HELLO PALBATOR":
    #             self.engine.say("Hello Human, what do you want ?")
    #             self.engine.runAndWait()
    #         self.lock.release()
    #     else:
    #         pass

    # def handle_asr_result(self,req):
    #     if self.lock.acquire(False):
    #         self.vocal_command=req.data
    #         self.lock.release()
    #     else:
    #         pass

if __name__=="__main__":
    x=VoiceGenerator()
    while not rospy.is_shutdown():
        rospy.spin()

