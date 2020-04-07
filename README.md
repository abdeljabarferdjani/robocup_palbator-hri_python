# PALBATOR-HRI
HRI python for Palbator, including Flask server and python client ( HRI Manager )

## Dependencies for MULTIPLEXER (FLASK server)
- Sudo apt-get install python3-dev python3-pip
- Sudo pip install flask
- Sudo pip install -U flask-cors
- Sudo pip install flask-socketio
- Sudo apt-get install python-eventlet

## Dependencies for HRI MANAGER (FLASK client)
- Sudo pip install -U socketIO-client

## Launch
- First, launch the flask server with : "python multiplexer.py"
- Then, launch the python client with : "python HRIManager.py"

## Uses
In order to completely launch the HRI,

- Start the palbator python `before` the react
- Start the palbator js by following the instructions in the specifi repo



## Dependencies for Voice Manager
- sudo apt-get install -y python python-dev python-pip build-essential swig libpulse-dev git
- sudo pip install pyttsx3
- sudo apt-get install libasound-dev
- sudo apt-get install python-pyaudio
- sudo apt-get install swig
- sudo pip install pocketsphinx
- sudo pip install statistics

## Launch Voice Manager
- roslaunch voiceManager asr.launch 

## Dependencies for Text To Speech Manager
- sudo apt-get install espeak libespeak-dev
- sudo apt-get install mbrola
- sudo apt-get install mbrola-*
- sudo python -m pip install scipy

## Launch TTS Manager
- roslaunch rapp_text_to_speech_espeak text_to_speech_espeak.launch

## Dependencies for ttsMimic
- sudo apt-get install gcc make pkg-config automake libtool libicu-dev libpcre2-dev libasound2-dev git
- git clone https://github.com/MycroftAI/mimic.git
- cd mimic
- ./autogen.sh
- ./configure --prefix="/usr/local"
- make -j4
- make check
- sudo make install

You can try Mimic using the command line : mimic -t "Hello world"

## Launch ttsMimic
- rosrun ttsMimic ttsMimicActionServer.py

## Dependencies for speechToTextPalbator
- sudo apt-get install -y python python-dev python-pip build-essential swig libpulse-dev git
- sudo pip install pyttsx3
- sudo apt-get install libasound-dev
- sudo apt-get install python-pyaudio
- sudo apt-get install swig
- sudo pip install pocketsphinx
- sudo pip install SpeechRecognition
If there are issues with pyaudio, those command lines could solve them:
- sudo pip uninstall pyaudio or sudo apt-get purge --auto-remove python-pyaudio
- sudo apt-get install portaudio19-dev python-all-dev python3-all-dev && sudo pip install pyaudio

## Launch speechToTextPalbator
- roslaunch speechToTextPalbator stt_global.launch
