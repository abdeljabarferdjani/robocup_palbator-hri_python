import speech_recognition as sr
import os

import ttsMimic.msg
import rospy
import actionlib

class RecorderForSpeechRecog:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_dir = '../misc/records'
        self.current_directory=os.path.dirname(os.path.realpath(__file__))        
        self.client_TTS=actionlib.SimpleActionClient("action_TTS_MIMIC",ttsMimic.msg.TtsMimicAction)

    def tts_action(self,speech):
        self.goal_TTS=ttsMimic.msg.TtsMimicGoal(speech)
        self.client_TTS.send_goal(self.goal_TTS)
        self.client_TTS.wait_for_result()

    def record_audio(self):
        if not isinstance(self.recognizer, sr.Recognizer):
            raise TypeError("`recognizer` must be `Recognizer` instance")

        if not isinstance(self.microphone, sr.Microphone):
            raise TypeError("`microphone` must be `Microphone` instance")

        # adjust the recognizer sensitivity to ambient noise and record audio
        # from the microphone
        
        cp=0
        for file in os.listdir(self.current_directory+'/'+self.audio_dir):
            if file.endswith(".wav"):
                cp = cp+1

        with self.microphone as source:
            # self.recognizer.adjust_for_ambient_noise(source,duration=2)
            self.recognizer.adjust_for_ambient_noise(source)
            print('Speak Now my friend!!!!!')
            self.tts_action('Speak now offline')
            print('Intent '+str(cp+1))
            audio = self.recognizer.listen(source)

    
        wav_data=audio.get_wav_data(convert_rate=16000,convert_width=2)
        with open(self.current_directory+'/'+self.audio_dir+'/intent'+str(cp+1)+'.wav', "wb") as f:
            f.write(wav_data)
        print('Audio written successfully')
  


