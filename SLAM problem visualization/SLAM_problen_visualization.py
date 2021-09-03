

##TBD: - consider time (linearly?). Older landmarks should be less wrong than new ones.
##       * multiply all individual linear and rotational offsets by ((latestLandmarkTime-lastSLAMtime)/(currentLandmarkTime-lastSLAMtime)) ?
##          currently this is done using 'linearTimeOffsets'






import pygame
import numpy as np

import GF.generalFunctions as GF

import multilateration as multLat


def handlePygameEvents(eventToHandle):
    if(eventToHandle.type == pygame.QUIT):
        global windowKeepRunning
        windowKeepRunning = False #stop program (soon)
        print("stopping pygame window")
    elif(eventToHandle.type == pygame.KEYDOWN):
        global sceneIndex
        if(eventToHandle.key == pygame.K_0):
            sceneIndex += (1 if (sceneIndex < (scenes-1)) else 0)
        elif(eventToHandle.key == pygame.K_9):
            sceneIndex -= (1 if (sceneIndex > 0) else 0)
        elif(eventToHandle.key == pygame.K_r):
            global resetConePoses
            resetConePoses = True
        elif(eventToHandle.key == pygame.K_t):
            global linearTimeOffsets
            linearTimeOffsets = not linearTimeOffsets
            print("turned", ("on" if linearTimeOffsets else "off"), "linearTimeOffsets")
        elif(eventToHandle.key == pygame.K_s):
            global addSensorNoise
            addSensorNoise = not addSensorNoise
            print("turned", ("on" if addSensorNoise else "off"), "sensorNoise")
    elif(eventToHandle.type == pygame.MOUSEWHEEL):
        global sizeScale
        sizeScale *= 1.0+(eventToHandle.y/10.0) #10.0 is an arbetrary zoomspeed
        if(sizeScale < 1.0):
            print("can't zoom out any further")
            sizeScale = 1.0
    elif((eventToHandle.type == pygame.MOUSEBUTTONDOWN) or (eventToHandle.type == pygame.MOUSEBUTTONUP)):
        if(eventToHandle.button == 2):
            global viewpointChanging
            if(eventToHandle.type == pygame.MOUSEBUTTONDOWN):
                pygame.event.set_grab(1)
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                global viewpointMouseTemp, viewpointPrev
                viewpointChanging = True
                viewpointMouseTemp = pygame.mouse.get_pos()
                viewpointPrev = viewpointShift.copy()
            else:
                pygame.event.set_grab(0)
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                updateViewpointShift() #update it one last time (or at all, if this hasn't been running in redraw())
                viewpointChanging = False
            

def realToPixelPos(realPos, withRespectTo=np.zeros(2)):
    dist, angle = GF.distAngleBetwPos(np.array(withRespectTo), np.array(realPos) + viewpointShift) #get distance to, and angle with respect to, car
    shiftedPixelPos = GF.distAnglePosToPos(dist*sizeScale, angle, np.array([resolution[0]/2, resolution[1]/2])) #calculate new (pixel) pos from the car pos, at the same distance, and the angle, plus the angle that the entire scene is shifted
    return(np.array([shiftedPixelPos[0], resolution[1]-shiftedPixelPos[1]])) #invert Y-axis for (0,0) at bottomleft display

def randomPos(withRespectTo, meanRadius, stdDev):
    randomRadius = np.random.normal(meanRadius, stdDev)
    randomAngle = np.random.random()*2*np.pi
    return(GF.distAnglePosToPos(randomRadius, randomAngle, np.array(withRespectTo)))

def rotationShift(centerPos, posToShift, shiftAngle):
    dist, angle = GF.distAngleBetwPos(np.array(centerPos), np.array(posToShift))
    return(GF.distAnglePosToPos(dist, angle+shiftAngle, np.array(centerPos)))

def generateRandomCones(N, carNoiseParameters, sensorNoiseParameters, addSensorNoise=True, linearTimeOffsets=False):
    ## first generate random cones
    realConesMeanRadius, realConeStdDev, shiftedConeMeanRadius, shiftedConeStdDev, shiftedRotationStdDev = carNoiseParameters
    realCones = [randomPos(np.zeros(2), realConesMeanRadius, realConeStdDev) for i in range(N)]
    print("realCones:"); [print(item) for item in realCones]
    ## then generate measured cones based on car noise
    linearOffset = randomPos(np.zeros(2), shiftedConeMeanRadius, shiftedConeStdDev)
    rotationalOffset = np.random.normal(0.0, shiftedRotationStdDev)
    print("linearOffset & rotationalOffset:", linearOffset, np.rad2deg(rotationalOffset), "deg")
    shiftedCones = [rotationShift(np.zeros(2), realCones[i], rotationalOffset * (((i+1.0)/N) if linearTimeOffsets else 1.0)) for i in range(N)]
    #print("shiftedCones:"); [print(item) for item in shiftedCones]
    shiftedCones = [(shiftedCones[i]+(linearOffset * (((i+1.0)/N) if linearTimeOffsets else 1.0))) for i in range(N)]
    #print("shiftedCones:"); [print(item) for item in shiftedCones]
    ## now add sensor noise
    sensorNoiseList = []
    if(addSensorNoise):
        sensorNoiseMeanRadius, sensorNoiseStdSev = sensorNoiseParameters
        sensorNoiseList = [randomPos(np.zeros(2), sensorNoiseMeanRadius, sensorNoiseStdSev) for i in range(N)]
        shiftedCones = [(shiftedCones[i]+sensorNoiseList[i]) for i in range(N)]
        print("sensorNoiseList:"); [print(item) for item in sensorNoiseList]
        print("shiftedCones:"); [print(item) for item in shiftedCones]
    return(realCones, shiftedCones, linearOffset, rotationalOffset, sensorNoiseList)
    ## note: in this application, realCones is where the simulation thinks the cones are, shiftedCones is what is measured (so the real-life 'positions' of the cones)

def drawCar(window, position, orientation, color):
    pygame.draw.circle(window, color, realToPixelPos(position), 4) #draw center indicator
    pygame.draw.line(window, color, realToPixelPos(position), realToPixelPos(position + (np.array([np.cos(orientation), np.sin(orientation)]) * 0.5)), 2) #draw (zero) direction indicator

def drawCones(window, coneList, conePixelRadius, color):
    coneIndexFont = pygame.font.Font(None, 21)
    for i in range(len(coneList)):
        conePixelPos = realToPixelPos(coneList[i])
        pygame.draw.circle(window, color, conePixelPos, conePixelRadius) #draw cone
        
        textToRender = str(i)
        #textColor = [255-color[0], 255-color[1], 255-color[2]]
        textimg = coneIndexFont.render(textToRender, 1, color, bgColor)
        window.blit(textimg, [conePixelPos[0] + conePixelRadius, conePixelPos[1] + conePixelRadius])

def drawShift(window, realCones, shiftedCones, rotationalOffset, linearTimeOffsets=False):
    for i in range(len(shiftedCones)):
        dist, realConeAngle = GF.distAngleBetwPos(np.zeros(2), realCones[i])
        shiftedConeAngle = realConeAngle + (rotationalOffset * (((i+1.0)/len(shiftedCones)) if linearTimeOffsets else 1.0))
        #shiftedConeAngle = GF.distAngleBetwPos(np.zeros(2), shiftedCones[i])[1]
        boundBox = (realToPixelPos([-dist, dist]), (2*dist*sizeScale, 2*dist*sizeScale))
        if(rotationalOffset < 0):
            pygame.draw.arc(window, debugColor, boundBox, shiftedConeAngle, realConeAngle, 1)
        else:
            pygame.draw.arc(window, debugColor, boundBox, realConeAngle, shiftedConeAngle, 1)
        onlyRotationShiftedPos = realToPixelPos(rotationShift(np.zeros(2), realCones[i], rotationalOffset * (((i+1.0)/len(shiftedCones)) if linearTimeOffsets else 1.0)))
        conePixelRadius = 4
        pygame.draw.circle(window, debugColor, onlyRotationShiftedPos, conePixelRadius) #draw cone
        pygame.draw.line(window, debugColor, onlyRotationShiftedPos, realToPixelPos(shiftedCones[i]), 2)

def drawSceneDescription(window, sceneIndex):
    if((sceneIndex >= 0) and (sceneIndex < len(sceneDescription))):
        textToRender = sceneDescription[sceneIndex]
        #textColor = [255-bgColor[0], 255-bgColor[1], 255-bgColor[2]]
        textimg = pygame.font.Font(None, 21).render(textToRender, 1, debugColor, bgColor)
        window.blit(textimg, [5, 5])


#def 


def averageAngle(angles: np.ndarray):
    # for i in range(len(angles)):
    #     angles[i] = GF.radRoll(angles[i])
    sumVector = np.zeros(2) #the easiest way to calculate a circular mean (mean that considers rollover), is to use the sum of (unit (or any real)) vectors
    zeroPos = np.zeros(2)
    for angle in angles:
        sumVector += GF.distAnglePosToPos(1.0, angle, zeroPos)
    #return(GF.get_norm_angle_between(zeroPos, sumVector, 0.0))
    return(GF.distAngleBetwPos(zeroPos, sumVector)[1])

def calculateOffsets(realCones, shiftedCones, targetLinearOffset, linearTimeOffsets=False): #note targetLinearOffset is temporary
    ## calculate:
    
    #print("multilat: \n\n")
    
    errorMagnitudes = np.array([(((i+1.0)/len(shiftedCones)) if linearTimeOffsets else 1.0) for i in range(len(shiftedCones))])
    
    # linearOffsetResults = [
    #     multLat.findMinimumErrorsAbsAllAxis(np.zeros(2), np.array(shiftedCones), np.array([GF.distAngleBetwPos(np.zeros(2), realCones[i])[0] for i in range(len(realCones))]), errorMagnitudes),
    #     multLat.findMinimumErrorsSquaredAllAxis(np.zeros(2), np.array(shiftedCones), np.array([GF.distAngleBetwPos(np.zeros(2), realCones[i])[0] for i in range(len(realCones))]), errorMagnitudes),
    #     multLat.findMinimumErrorsAbsAllAxis(np.zeros(2), np.array(realCones), np.array([GF.distAngleBetwPos(np.zeros(2), shiftedCones[i])[0] for i in range(len(shiftedCones))]), errorMagnitudes),
    #     multLat.findMinimumErrorsSquaredAllAxis(np.zeros(2), np.array(realCones), np.array([GF.distAngleBetwPos(np.zeros(2), shiftedCones[i])[0] for i in range(len(shiftedCones))]), errorMagnitudes)]
    # print("linearOffsetResults:")
    # [print(item) for item in linearOffsetResults]
    
    # #calculatedLinearOffset = linearOffsetResults[0][0]
    
    # minDistIndex = 0;   minDist = GF.distAngleBetwPos(targetLinearOffset, linearOffsetResults[0][0])[0]
    # minErrorIndex = 0;  minError = linearOffsetResults[0][1]
    # for i in range(1, len(linearOffsetResults)):
    #     linOff, sumOfError = linearOffsetResults[i]
    #     dist = GF.distAngleBetwPos(targetLinearOffset, linOff)[0]
    #     if(dist < minDist):
    #         minDist = dist
    #         minDistIndex = i
    #     if(sumOfError < minError):
    #         minError = sumOfError
    #         minErrorIndex = i
    # print("best dist result:", minDistIndex, minDist, linearOffsetResults[minDistIndex], targetLinearOffset)
    # print("best error result:", minErrorIndex, GF.distAngleBetwPos(targetLinearOffset, linearOffsetResults[minErrorIndex][0])[0], linearOffsetResults[minErrorIndex], targetLinearOffset)
    # calculatedLinearOffset = linearOffsetResults[minDistIndex][0]
    
    calculatedLinearOffset, resultError = multLat.multilaterate(np.zeros(2), np.array(shiftedCones), np.array([GF.distAngleBetwPos(np.zeros(2), realCones[i])[0] for i in range(len(realCones))]), errorMagnitudes)
    
    ## calculate it in a different way to see and see if that way is better
    #altCalculatedLinearOffset, altResultError = multLat.multilaterate(np.zeros(2), np.array(realCones), np.array([GF.distAngleBetwPos(np.zeros(2), shiftedCones[i])[0] for i in range(len(shiftedCones))]), errorMagnitudes)
    altErrorMagnitudes = np.array([((len(shiftedCones)/(i+1.0)) if linearTimeOffsets else 1.0) for i in range(len(shiftedCones))])
    altCalculatedLinearOffset, altResultError = multLat.multilaterate(np.zeros(2), np.array(shiftedCones), np.array([GF.distAngleBetwPos(np.zeros(2), realCones[i])[0] for i in range(len(realCones))]), altErrorMagnitudes)
    print("altCalculated Linear Offset:", altCalculatedLinearOffset, resultError, altResultError, altResultError < resultError, GF.distAngleBetwPos(targetLinearOffset, altCalculatedLinearOffset)[0] < GF.distAngleBetwPos(targetLinearOffset, calculatedLinearOffset)[0])
    #print("\n\n multilat done")
    
    print("calculated Linear Offset:", calculatedLinearOffset, targetLinearOffset, "true error:", targetLinearOffset-calculatedLinearOffset, GF.distAngleBetwPos(targetLinearOffset, calculatedLinearOffset))
    unshiftedConesOnlyLinear = [shiftedCones[i]-(calculatedLinearOffset*(((i+1.0)/len(shiftedCones)) if linearTimeOffsets else 1.0)) for i in range(len(shiftedCones))]
    #print("unshiftedConesOnlyLinear:"); [print(item) for item in unshiftedConesOnlyLinear]
    
    angles = np.zeros(len(shiftedCones))
    for i in range(len(shiftedCones)):
        #angles[i] = get_norm_angle_between(np.zeros(2), shiftedCones[i], get_norm_angle_between(np.zeros(2), realCones[i]))
        angles[i] = GF.distAngleBetwPos(np.zeros(2), unshiftedConesOnlyLinear[i])[1] - GF.distAngleBetwPos(np.zeros(2), realCones[i])[1]
        if(linearTimeOffsets):
            angles[i] *= (len(shiftedCones) / (i+1.0))
    calculatedRotationalOffset = averageAngle(angles)
    print("calculated Rot.Offset:", np.rad2deg(calculatedRotationalOffset), "true error:",  np.rad2deg(GF.radDiff(calculatedRotationalOffset, targetRotationalOffset)))
    unshiftedCones = [rotationShift(np.zeros(2), unshiftedConesOnlyLinear[i], -calculatedRotationalOffset*(((i+1.0)/len(shiftedCones)) if linearTimeOffsets else 1.0)) for i in range(len(shiftedCones))]
    #print("unshiftedCones:"); [print(item) for item in unshiftedCones]
    
    return(calculatedLinearOffset, calculatedRotationalOffset, unshiftedConesOnlyLinear, unshiftedCones)


def updateViewpointShift():
    if(viewpointChanging):
        global viewpointShift
        mousePos = pygame.mouse.get_pos()
        mouseDelta = [float(mousePos[0] - viewpointMouseTemp[0]), float(viewpointMouseTemp[1] - mousePos[1])]
        viewpointShift[0] = viewpointPrev[0] + (mouseDelta[0]/sizeScale)
        viewpointShift[1] = viewpointPrev[1] + (mouseDelta[1]/sizeScale)

realConeColor = [255,255,0] #yellow
shiftedConeColor = [0,50,255] #dark blue
debugColor = [255, 165, 0]
bgColor = [50, 50, 50] #grey
global sizeScale
sizeScale = 60.0 #pixels per meter
global viewpointShift, viewpointChanging, viewpointMouseTemp, viewpointPrev
viewpointShift = np.zeros(2)
viewpointChanging = False
viewpointMouseTemp = [0,0]
viewpointPrev = np.zeros(2)
global resolution
resolution = (1200, 600)
global windowKeepRunning
windowKeepRunning = True
global sceneIndex
sceneIndex = 0
scenes = 5 #how many scenes there are
global resetConePoses
resetConePoses = False

global linearTimeOffsets
linearTimeOffsets = True

#constants
global addSensorNoise
addSensorNoise = True
coneCount = 4
carNoiseParams = (4.0, 1.0, 0.3, 0.2, np.deg2rad(15)) #parameters: (mean distance to cones, std dev of cone distance, mean linear offset (hypotonuse), std dev of linear offset (hypotonuse), std dev of rotational offset)
sensorNoiseParams = (0.0, 0.1) #parameters: (mean position error (hypotonuse), std dev of position error (hypotonuse))

sceneDescription = ("rotational and linear offset",
                    "how to find linear offset",
                    "reverse-engineering the intersect between the circles",
                    "finding rotational offset based on calculated linear offset",
                    "applying results")


if __name__ == '__main__':
    try:
        pygame.init()
        pygame.font.init()
        window = pygame.display.set_mode(resolution)#, pygame.RESIZABLE)
        pygame.display.set_caption("(pygame) SLAM problem visualization")
        #global windowKeepRunning
        
        realCones, shiftedCones, targetLinearOffset, targetRotationalOffset, sensorNoiseList = generateRandomCones(coneCount, carNoiseParams, sensorNoiseParams, addSensorNoise, linearTimeOffsets)
        calculatedLinearOffset, calculatedRotationalOffset, unshiftedConesOnlyLinear, unshiftedCones = calculateOffsets(realCones, shiftedCones, targetLinearOffset, linearTimeOffsets)
        
        while(windowKeepRunning):
            for eventToHandle in pygame.event.get():
                handlePygameEvents(eventToHandle)
            updateViewpointShift()
            
            if(resetConePoses):
                resetConePoses = False
                print("\n\n")
                realCones, shiftedCones, targetLinearOffset, targetRotationalOffset, sensorNoiseList = generateRandomCones(coneCount, carNoiseParams, sensorNoiseParams, addSensorNoise, linearTimeOffsets)
                calculatedLinearOffset, calculatedRotationalOffset, unshiftedConesOnlyLinear, unshiftedCones = calculateOffsets(realCones, shiftedCones, targetLinearOffset, linearTimeOffsets)
            
            ## draw
            window.fill(bgColor)
            drawSceneDescription(window, sceneIndex)
            if(sceneIndex == 0):
                drawCar(window, np.zeros(2), 0.0, [255, 255, 255]) #draw zero indicator
                drawCar(window, targetLinearOffset, targetRotationalOffset, realConeColor) #draw true offset indicator
                
                drawCones(window, realCones, 10, realConeColor)
                drawCones(window, shiftedCones, 7, shiftedConeColor)
                
                drawShift(window, realCones, shiftedCones, targetRotationalOffset, linearTimeOffsets)
            
            elif(sceneIndex == 1):
                conePixelRadius = 7
                pygame.draw.circle(window, shiftedConeColor, realToPixelPos(np.zeros(2)), conePixelRadius) #draw shifted cone(s) in center
                
                for i in range(len(shiftedCones)):
                    pixelRadius = GF.distAngleBetwPos(np.zeros(2), realCones[i])[0] * sizeScale
                    pygame.draw.circle(window, debugColor, realToPixelPos(np.zeros(2), shiftedCones[i]), pixelRadius, 1)
                    pygame.draw.line(window, debugColor, realToPixelPos(np.zeros(2)), realToPixelPos(-1*targetLinearOffset), 2)
            
            elif(sceneIndex == 2):
                conePixelRadius = 7
                pygame.draw.circle(window, shiftedConeColor, realToPixelPos(np.zeros(2)), conePixelRadius) #draw shifted cone(s) in center
                
                for i in range(len(shiftedCones)):
                    pixelRadius = GF.distAngleBetwPos(np.zeros(2), realCones[i])[0] * sizeScale
                    pygame.draw.circle(window, debugColor, realToPixelPos(np.zeros(2), shiftedCones[i]), pixelRadius, 1)
                    pygame.draw.line(window, shiftedConeColor, realToPixelPos(np.zeros(2)), realToPixelPos(-1*calculatedLinearOffset), 2)
            
            elif(sceneIndex == 3):
                drawCar(window, np.zeros(2), 0.0, [255, 255, 255]) #draw zero indicator
                drawCar(window, targetLinearOffset, targetRotationalOffset, realConeColor) #draw true offset indicator
                drawCar(window, calculatedLinearOffset, calculatedRotationalOffset, shiftedConeColor) #draw calculated offset indicato
                
                drawCones(window, realCones, 10, realConeColor)
                drawCones(window, unshiftedConesOnlyLinear, 7, shiftedConeColor)
                
                drawShift(window, realCones, unshiftedConesOnlyLinear, calculatedRotationalOffset, linearTimeOffsets)
            
            elif(sceneIndex == 4):
                drawCar(window, np.zeros(2), 0.0, [255, 255, 255]) #draw zero indicator
                drawCar(window, targetLinearOffset, targetRotationalOffset, realConeColor) #draw true offset indicator
                drawCar(window, calculatedLinearOffset, calculatedRotationalOffset, shiftedConeColor) #draw calculated offset indicato
                
                drawCones(window, realCones, 10, realConeColor)
                drawCones(window, unshiftedCones, 7, shiftedConeColor)
                
                #drawShift(window, realCones, unshiftedCones, calculatedRotationalOffset, linearTimeOffsets)
            
            pygame.display.flip() #send (finished) frame to display
        
    finally:
        try:
            pygame.quit()
        except:
            print("couldn't close pygame")