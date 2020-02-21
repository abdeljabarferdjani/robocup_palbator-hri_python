#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#Copyright 2015 RAPP

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at

    #http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

import rospy
import json
import sys
import os

from pylab import *
from scipy.io import wavfile

from rapp_platform_ros_communications.srv import (
  TextToSpeechSrv,
  TextToSpeechSrvResponse
  )

from rapp_exceptions import RappError

import actionlib
import rapp_platform_ros_communications.msg 

import subprocess

class TextToSpeechEspeak:

  def __init__(self):
    # Speech recognition service published
    self.serv_topic = rospy.get_param("rapp_text_to_speech_espeak_topic")
    self.serv_speed = rospy.get_param("speed")
    self.serv_pitch = rospy.get_param("pitch")
    self.serv_language = rospy.get_param("language")
    if self.serv_language=="":
      rospy.logerror('Language not specified')

    if(not self.serv_topic):
      rospy.logerror("Text to speech espeak topic param not found")

    # self.serv = rospy.Service(self.serv_topic, TextToSpeechSrv, self.text_to_speech_callback)

    self.process=None
  
    self.action_tts=actionlib.SimpleActionServer("action_TTS",rapp_platform_ros_communications.msg.SayVocalSpeechAction,self.action_tts_callback,auto_start=False)
    self.action_tts_feedback=rapp_platform_ros_communications.msg.SayVocalSpeechFeedback()
    self.action_tts_result=rapp_platform_ros_communications.msg.SayVocalSpeechResult()
    self.action_tts.start()


  #the action callback
  def action_tts_callback(self,goal):
    
    success=True
    
    self.action_tts_feedback.tts_feedback='all clear'

    if self.serv_language=="en":
      lang='mb-us1'

    speed=self.serv_speed
    pitch=self.serv_pitch

    text=goal.text_to_say
    text = text.replace(" ", "_")

    if self.action_tts.is_preempt_requested():
      rospy.loginfo('Preempted SayVocalSpeech Action')
      self.action_tts.set_preempted()
      success=False
    
    # command = 'espeak -p ' + str(pitch) + ' -s ' + str(speed) + ' -v ' + lang + text 

    # output = os.system(command)
    # if output != 0:
    #     self.action_tts_feedback.tts_feedback="Error: Text to speech espeak malfunctioned. You have probably\
    #             given wrong language settings"
    #     success=False
    
    self.process=subprocess.Popen(['espeak','-p',str(pitch),'-s',str(speed),'-v',lang],stdin=subprocess.PIPE, stdout=subprocess.PIPE,close_fds=True)
    self.process.stdin.write(text)
    self.process.stdin.close()
    while self.process.poll() is None:
      if self.action_tts.is_preempt_requested():
        rospy.loginfo('Preempted SayVocalSpeech Action')
        self.process.terminate()
        self.action_tts.set_preempted()
        success=False


    self.action_tts.publish_feedback(self.action_tts_feedback)

    if success:
      self.action_tts_result.errors=self.action_tts_feedback.tts_feedback
      rospy.loginfo("Action SayVocalSpeech succeeded")
      self.action_tts.set_succeeded(self.action_tts_result)

  # The service callback
  def text_to_speech_callback(self, req):

    res = TextToSpeechSrvResponse()
    if self.serv_language=="en":
      lang='mb-us1 '    

    # speed = 130 # upper limit = 180
    # pitch = 50 # upper limit = 99
    speed=self.serv_speed
    pitch=self.serv_pitch

    text=req.text
    text = text.replace(" ", "_")
    command = 'espeak -p ' + str(pitch) + ' -s ' + str(speed) + ' -v ' + lang + text 

    output = os.system(command)
    if output != 0:
        res.error = "Error: Text to speech espeak malfunctioned. You have probably\
                given wrong language settings"
        return res

    return res

if __name__ == "__main__":
  rospy.init_node('text_to_speech_espeak_ros_node')
  text_to_speech_espeak_ros_node = TextToSpeechEspeak()
  rospy.spin()


