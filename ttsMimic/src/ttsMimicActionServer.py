#! /usr/bin/env python

import rospy

import actionlib

import ttsMimic.msg
import subprocess

import os

class ttsMimicActionServer(object):

    def __init__(self):
        rospy.init_node('tts_Mimic_action_server_node')
        self.action_tts_server=actionlib.SimpleActionServer("action_TTS_MIMIC",ttsMimic.msg.TtsMimicAction,self.action_server_callback,auto_start=False)

        self.action_tts_server_feedback=ttsMimic.msg.TtsMimicFeedback()
        self.action_tts_server_result=ttsMimic.msg.TtsMimicResult()

        self.action_tts_server.start()
        self.current_index=None
        rospy.loginfo("tts mimic server initiated")
        self.path_to_wav='/home/student/Bureau/record_MIMIC/'

    def get_current_index(self):
        cp=0
        for file in os.listdir(self.path_to_wav):
            if file.endswith(".wav"):
                cp=cp+1
        self.current_index=cp+1



    def action_server_callback(self,goal):
        rospy.loginfo("Action initiating ...")
        success=True

        self.action_tts_server_feedback.tts_feedback='None'
        text=goal.text_to_say

        self.get_current_index()

        # self.process=subprocess.Popen(['mimic','-t',str(text),'-o',self.path_to_wav+'record_'+str(self.current_index)+'.wav'],stdin=subprocess.PIPE, stdout=subprocess.PIPE,close_fds=True)
        self.process=subprocess.Popen(['mimic','-t',str(text)],stdin=subprocess.PIPE, stdout=subprocess.PIPE,close_fds=True)
        
        # self.process.stdin.write(text)
        self.process.stdin.close()
        while self.process.poll() is None:
            if self.action_tts_server.is_preempt_requested():
                rospy.loginfo('Preempted SayVocalSpeech Action')
                self.process.terminate()
                self.action_tts_server.set_preempted()
                success=False
                break

        self.action_tts_server.publish_feedback(self.action_tts_server_feedback)

        if success:
            self.action_tts_server_result.tts_result=self.action_tts_server_feedback.tts_feedback
            rospy.loginfo("Action SayVocalSpeech succeeded")
            self.action_tts_server.set_succeeded(self.action_tts_server_result)

if __name__ == "__main__":
    instance_TTS=ttsMimicActionServer()
    while not rospy.is_shutdown():
        rospy.spin()