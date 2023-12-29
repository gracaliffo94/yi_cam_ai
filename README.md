**YI - AI Cam Software**

This software performs polling and storage for YI cams connected to the local network and automatically connects to new YI ip cameras found in the LAN.

NOTE: the YI cameras must expose a RTSP port, easily duable thanks to _https://github.com/alienatedsec/yi-hack-v5_ :)

NOTE: I will upload the requirements.txt soon, but for now try to create a venv by yourself and install the required libraries

For now, launch firstly the script **getAndSaveStreamFromCams.py** that creates a tree in the file system in which the frames incoming from the YI cameras are saved.
Then, launch **predictAndConsumeFrames.py** that will create both images and txt predictions. 
The image predictions are .jpg files predicted through yolov8 with bounding boxes, classes and confidences and the txt predictions are files containing the coordinates for the bounding boxes, classes and confidences, so that one can quickly check which classes have been detected in each image, how much confidence, and so on.
