# Overview
Python code for a car sim <br/>
Moving_car: Code that simulates a self-driving car, aiming to travel along a line of cones <br/>
coneconnecting: Code that holds math for finding cones that 'connect' to form the track boundry <br/>

## How to use Object_Detection_Module 

For proper use of the Object_Detection_Module you need to follow these steps:

### 1. Download the configurations and the weights from the HARD Google Drive:
```
https://drive.google.com/drive/folders/16qPjcqzjfw3wzPSjmJlqCNKbgekR5UpY?usp=sharing
```
### 2. Make the following 2 directories:
```
Configurations
```
Where all the contents of the Configurations folder from drive should be in. </br>

And
```
Weights
```
Where the contents of YOLO_V4 Tiny Weights.zip should be in. </br>

In the end you should end up with this folder structure:
```
|New Version
|-Configurations
|-Weights
|-coco.names
|-detecion.py
```
### 3. Make sure you have OpenCV built and optionally with CUDA and CuDNN.