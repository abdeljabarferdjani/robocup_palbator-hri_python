#!/usr/bin/env python

import rospy
import actionlib

import speechToTextPalbator.msg

import speech_recognition as sr
import json
import os
import ttsMimic.msg

class SpeechToTextOnline(object):

    def __init__(self):
        rospy.init_node("STT_online_node")
        self.action_server=actionlib.SimpleActionServer("action_STT_online", speechToTextPalbator.msg.SttOnlineAction,self.handle_server_callback,auto_start=False)
        self.action_server_feedback=speechToTextPalbator.msg.SttOnlineFeedback()
        self.action_server_result=speechToTextPalbator.msg.SttOnlineResult()
        self.current_directory=os.path.dirname(os.path.realpath(__file__))      

        self.client_TTS=actionlib.SimpleActionClient("action_TTS_MIMIC",ttsMimic.msg.TtsMimicAction)

        rospy.on_shutdown(self.shutdown)
        self.action_server.start()
        rospy.loginfo("server for STT online initiated")

    def shutdown(self):
        """This function is executed on node shutdown."""
        # command executed after Ctrl+C is pressed
        rospy.loginfo("Stop ASRControl")
        self.action_server.set_aborted()
        # exit()

    def tts_action(self,speech):
        self.goal_TTS=ttsMimic.msg.TtsMimicGoal(speech)
        self.client_TTS.send_goal(self.goal_TTS)
        self.client_TTS.wait_for_result()

    def parser_view_action_to_dic_mode(self,view_action):
        dic_mode=""
        if view_action=="askAge":
            dic_mode="age"
            self.enable_publish_detection_output=True
        
        elif view_action=="askDrink":
            dic_mode="drinks"
            self.enable_publish_detection_output=True
        
        elif view_action=="askSomething":
            self.enable_publish_detection_output=False

        elif view_action=="askName":
            dic_mode="names"
            self.enable_publish_detection_output=True

        elif view_action=="confirm":
            dic_mode="confirmation"
            self.enable_publish_detection_output=True

        elif view_action==None:
            self.enable_publish_detection_output=False
        
        elif view_action=='askOpenDoor':
            dic_mode="next"
            self.enable_publish_detection_output=True

        else:
            self.enable_publish_detection_output=False
        return dic_mode   

    def load_database(self):
        _database = "~database"
        if rospy.has_param(_database):
            for database_mode,database_path in rospy.get_param(_database).iteritems():
                if database_mode==self.dictionary_choose:
                    file_database=open(self.current_directory+'/'+database_path,"r")
                    self.database_words=[]
                    
                    for line in file_database:
                        data=line.split("\n")[0]
                        data2=data.split("\t")
                        if len(data2)>1:
                            self.database_words.append([data2[0],float(data2[1])])
                        else:
                            self.database_words.append(data2[0])
                    file_database.close()
                    print(self.database_words)


    def recognize_speech_from_mic(self,recognizer, microphone):
        """Transcribe speech from recorded from `microphone`.

        Returns a dictionary with three keys:
        "success": a boolean indicating whether or not the API request was
                successful
        "error":   `None` if no error occured, otherwise a string containing
                an error message if the API could not be reached or
                speech was unrecognizable
        "transcription": `None` if speech could not be transcribed,
                otherwise a string containing the transcribed text
        """
        # check that recognizer and microphone arguments are appropriate type
        if not isinstance(recognizer, sr.Recognizer):
            raise TypeError("`recognizer` must be `Recognizer` instance")

        if not isinstance(microphone, sr.Microphone):
            raise TypeError("`microphone` must be `Microphone` instance")

        # adjust the recognizer sensitivity to ambient noise and record audio
        # from the microphone
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Speak now please")
            self.tts_action("Speak Now online")
            audio = recognizer.listen(source,timeout=3,phrase_time_limit=3)

        # set up the response object
        response = {
            "success": True,
            "error": None,
            "transcription": None
        }

        # try recognizing the speech in the recording
        # if a RequestError or UnknownValueError exception is caught,
        #     update the response object accordingly
        try:
            response["transcription"] = recognizer.recognize_google(audio)

        except sr.RequestError:
            # API was unreachable or unresponsive
            response["success"] = False
            response["error"] = "API unavailable"
        except sr.UnknownValueError:
            # speech was unintelligible
            response["error"] = "Unable to recognize speech"

        return response


    def process_detection(self,transcription,action):


        transcription=transcription.upper()
        data = ''
        for element in self.database_words:
            if element in transcription:
                data=element
                rospy.loginfo("GOOD DETECTION")
                break

        if data == '':
            rospy.loginfo("BAD DETECTION. Please try again")
        
        return data

    def handle_server_callback(self,goal):
        rospy.loginfo("Action Online initiating ...")
        success=False

        self.action_server_feedback.stt_feedback = 'None'
        # index=0
        data=None

        d=json.loads(goal.order)
        view_id=d['order']
        view_action=d['action']
        # view_speech_to_say=d['speech']

        self.dictionary_choose = self.parser_view_action_to_dic_mode(view_action)
        self.load_database()

        while not success and not rospy.is_shutdown():
            if self.action_server.is_preempt_requested():
                rospy.loginfo("Preempted request server offline")
                self.action_server.set_preempted()
                break

            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

            
            # print(view_speech_to_say) ##### A IMPLEMENTER -> SERVER TTS MIMIC

                # get the guess from the user
                # if a transcription is returned, break out of the loop and
                #     continue
                # if no transcription returned and API request failed, break
                #     loop and continue
                # if API request succeeded but no transcription was returned,
                #     re-prompt the user to say their guess again. Do this up
                #     to PROMPT_LIMIT times
            guess = self.recognize_speech_from_mic(recognizer, microphone)
            print("You said: {}".format(guess["transcription"]))

            
            if guess["transcription"]:
                    data=self.process_detection(guess["transcription"],view_action)
                    
                    # index=self.next_index(index,data)
                    if data != '':
                        success=True
                    continue

            if not guess["success"]:
                continue
            print("I didn't catch that. What did you say?\n")
            if guess["error"]:
                print("ERROR: {}".format(guess["error"]))
                continue

        if success:
            self.action_server.publish_feedback(self.action_server_feedback)
            self.action_server_result.stt_result = data
            rospy.loginfo("Action STT Online succeeded")
            self.action_server.set_succeeded(self.action_server_result)

if __name__ == "__main__":
    instance_online=SpeechToTextOnline()
    while not rospy.is_shutdown():
        rospy.spin()