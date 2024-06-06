import time
from datetime import datetime
from PIL import Image
import numpy as np
import requests
import random as rnd
from dotenv import load_dotenv
from os import system, getenv

from pixoo import Pixoo

load_dotenv()

pixooAdressMAC = getenv('PIXOO_ADDRESS_MAC')
latitude = getenv('LATITUDE')
longitude = getenv('LONGITUDE')
weatherAPIkey = getenv('WEATHER_API_KEY')

connected = False

pixoo16 = Pixoo(pixooAdressMAC)
try:
    pixoo16.connect()
    connected = True
except:
    connected = pixoo16.check_connection(connected)

limit = 100
#^to limit the max loops in a While loop
adjacents = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
#^used in minesweeper and tileChoose functions
msGrid = np.zeros((13, 9), dtype=np.int8)
#^used in minesweeper, colorGrid, tileChoose, and MAIN
msGridExtra = np.zeros((13, 11), dtype=np.int8)
#^used in minesweeper and tileChoose
msColor = np.zeros((11, 9, 3), dtype=np.uint8)
#^used in colorGrid
msProbabilities = np.zeros((11, 9), dtype=np.uint8)
#^used in probabilityCalc
msArr = np.zeros((11, 9), dtype=np.uint8)
#^used in probabilityCalc
data = np.zeros((16, 16, 3), dtype=np.uint8)
#^used in drawFrame
binClockArr = np.zeros((4, 6, 3), dtype=np.uint8)
#^used in binClock
precipArr = np.zeros((4, 6, 3), dtype=np.uint8)
#^used in fetchWeatherData
localEdgeList = np.zeros((11, 9), dtype=np.uint8)
#^used in probabilityCalc, ruleOne, ruleTwo, ruleThree
localFreebieList = np.zeros((11, 9), dtype=np.uint8)
#^used in probabilityCalc, ruleOne, ruleTwo, ruleThree
localMinesList = np.zeros((11, 9), dtype=np.uint8)
#^used in probabilityCalc, ruleOne, ruleTwo, ruleThree
edgeList = []
#^used in probabilityCalc, ruleOne, ruleTwo, ruleThree
freebieList = []
#^used in probabilityCalc, ruleOne, ruleTwo, ruleThree
knownMines = []
#^used in probabilityCalc, ruleOne, ruleTwo, ruleThree
turn = 0
#^used in minesweeper
turnsTakenToWin = []
#^used in minesweeper
turnsTakenToLose = []
#^used in minesweeper


#############################################################################################################################################
def setWindowTitle(title):
    system(f"title {title}")


#############################################################################################################################################
def drawframe(weatherData, precipArr, msGrid, turn):
    guessYear = 2022
    loops = 0
    while (datetime(guessYear,12,25) < datetime.now()) & (loops < limit):
        #a bit scuffed, but hey it works
        guessYear += 1
        loops += 1
    daysTill = (datetime(guessYear,12,25) - datetime.now()).days + 1

    [msGrid, turn] = minesweeper(msGrid, edgeList, turn)
    
    #convert everything into a grid of RGB values
    data[0:16,0:16] = 0
    data[0:4,0:6] = binClock() #binary clock
    data[0:4,7:16] = pixelNumbers(daysTill, 3, [[97,204,59],[217,41,41]]) #christmas countdown
    data[4:8,0:6] = pixelNumbers(weatherData[0], 2, [[240,150,78],[199,88,21]]) #temperature
    data[8:12,0:6] = pixelNumbers(weatherData[1], 2, [[42,89,174],[76,144,235]]) #humidity
    data[12:16,0:6] = precipArr #chances of precipitation
    data[5:16,7:16] = colorGrid(msGrid)[0:11,0:9] #minesweeper
    img = Image.fromarray(data, 'RGB')
    img.save('frame_current.png')
    return [msGrid, turn]


#############################################################################################################################################
def binClock():
    now = datetime.now()
    binClockArr[0:4,0:6,0:3] = 0
    timeString = now.strftime(" %w %H %I %M %S") #notice the space at the beginning
    timeArray = timeString.split(' ')
    # 0: DST, 0-1
    # 1: weekday, 1-7
    # 2: AM/PM, 0-1
    # 3: hour, 1-12
    # 4: minute, 0-59
    # 5: second, 0-59
    timeArray[0] = time.localtime().tm_isdst
    for i in range(1,6):
        timeArray[i] = int(timeArray[i])
    if timeArray[1] == 0:
        timeArray[1] = 7 #sunday is normally 0 for some reason, i want monday to be first
    timeArray[2] = timeArray[2] // 12
    #print(timeArray) #uncomment this for the raw numbers in decimal
    binClockArr[0,0] = [255, 255, 255] #power light
    timeArray[0] = str(timeArray[0])
    timeArray[1] = f"{timeArray[1]:b}".zfill(3)
    timeArray[2] = f"{timeArray[2]}"
    timeArray[3] = f"{timeArray[3]:b}".zfill(4)
    timeArray[4] = f"{timeArray[4]:b}".zfill(6)
    timeArray[5] = f"{timeArray[5]:b}".zfill(6)
    #print(timeArray) #uncomment this for the raw numbers in binary
    for i in range(0,6):
        timeArray[i] = list(timeArray[i])
    colorsBright = [[225,171,10],
                    [237,60,60],
                    [237,193,60],
                    [237,193,60],
                    [79,182,69],
                    [68,139,236]]
    colorsDark = [[54,89,239],
                  [71,18,18],
                  [71,58,18],
                  [71,58,18],
                  [24,54,21],
                  [20,41,70]]
    for i in range(0,6):
        for j in range(0,len(timeArray[i])):
            if timeArray[i][j] == '1':
                timeArray[i][j] = colorsBright[i]
            else:
                timeArray[i][j] = colorsDark[i]
    binClockArr[0,1] = timeArray[0][0]    # DST, in blue/yellow
    binClockArr[0,3:6] = timeArray[1]  # weekday, in red
    binClockArr[1,0] = timeArray[2][0] # AM/PM, in yellow
    binClockArr[1,2:6] = timeArray[3]  # hour, in yellow
    binClockArr[2,0:6] = timeArray[4]  # minute, in green
    binClockArr[3,0:6] = timeArray[5]  # second, in blue

    return binClockArr


#############################################################################################################################################
def pixelNumbers(number, maxLength, colors):
    if number >= 0:
        number = [int(x) for x in list(str(int(number)))]
    else:
        number = [x for x in list(str(int(number)))]
        number[0] = 10
        number[1:] = [int(x) for x in number[1:]]
    #number = [int(x) for x in list(str(int(number)))]
    numberTemplates = np.array([[[1,1,1],[1,0,1],[1,0,1],[1,1,1]], # 0
                       [[1,1,0],[0,1,0],[0,1,0],[0,1,0]],  # 1
                       [[1,1,1],[0,0,1],[1,1,0],[1,1,1]],  # 2
                       [[1,1,1],[0,1,1],[0,0,1],[1,1,1]],  # 3
                       [[1,0,1],[1,0,1],[1,1,1],[0,0,1]],  # 4
                       [[1,1,1],[1,1,0],[0,0,1],[1,1,1]],  # 5
                       [[1,1,1],[1,0,0],[1,1,1],[1,1,1]],  # 6
                       [[1,1,1],[0,0,1],[0,1,1],[0,0,1]],  # 7
                       [[1,1,1],[1,1,1],[1,0,1],[1,1,1]],  # 8
                       [[1,1,1],[1,1,1],[0,0,1],[1,1,1]],  # 9
                       [[0,0,0],[1,1,1],[0,0,0],[0,0,0]]]) # -
    numbers = ['a' for x in range(maxLength-1)]
    numbers[maxLength-len(number):maxLength-1] = number
    pixelGrid = np.zeros((4, 3*maxLength, 3), dtype=np.uint8)
    for i in range(0,maxLength):
        if numbers[i] != 'a':
            for j in range(0,4):
                for k in range(0,3):
                    if numberTemplates[numbers[i],j,k] == 1:
                        pixelGrid[j,3*i+k] = colors[i%2]
    return pixelGrid


#############################################################################################################################################
def fetchWeatherData():
    print('FETCHING WEATHER DATA')
    api_result = requests.get('https://api.openweathermap.org/data/2.5/weather?lat='+latitude+'&lon='+longitude+'&units=imperial&appid='+weatherAPIkey)
    api_response = api_result.json()
    weatherData = [api_response['main']['temp'],
                   api_response['main']['humidity']]

    weatherData[0] = round(weatherData[0])
    api_result = requests.get('https://api.openweathermap.org/data/2.5/forecast?lat='+latitude+'&lon='+longitude+'&units=imperial&appid='+weatherAPIkey)
    api_response = api_result.json()
    precipChances = [0,0,0,0,0,0]
    weatherTimes = [0,0,0,0,0,0]
    for i in range(0,6):
        precipChances[i] = api_response["list"][i]["pop"]
        weatherTimes[i] = api_response["list"][i]["dt_txt"]
    print(precipChances) # i like keeping this line on for now
    print(weatherTimes)  # this one too
    # keep in mind: weatherTimes is in UTC, which is 6 or 7 hours more than MDT or MST

    precipArr[0:4,0:6,0:3] = 0 # making an array of binary numbers for each 3-hour precip chance
    colorsBright = [[177,198,220],
                    [109,133,151],
                    [227,208,46]]
    colorsDark = [[53,59,66],
                  [33,40,45],
                  [76,69,15]]
    for i in range(0,6):
        precipChances[i] = round(precipChances[i]*10) # convert to 0-10
        precipChances[i] = f"{precipChances[i]:b}".zfill(4) # convert to 4-digit binary
        #print(precipChances[i])
        precipChances[i] = list(precipChances[i]) # convert string to array of letters
        for j in range(0,len(precipChances[i])):
            if precipChances[i][j] == '1':
                if weatherTimes[i][-8:] in ['06:00:00', '18:00:00']: # in DST, this is 12:00:00, AM or PM. in MST, this is 11:00:00, AM or PM.
                    precipChances[i][j] = colorsBright[2]
                else:
                    precipChances[i][j] = colorsBright[i%2]
            else:
                if weatherTimes[i][-8:] in ['06:00:00', '18:00:00']:
                    precipChances[i][j] = colorsDark[2]
                else:
                    precipChances[i][j] = colorsDark[i%2]
        precipArr[0:4,i] = precipChances[i]

    #weatherData[2] = int(max(precipChances)*100)
    #if weatherData[2] == 100:
    #    weatherData[2] = 99 #close enough
    
    return [weatherData, precipArr]


#############################################################################################################################################
def minesweeper(msGrid, edgeList, turn):
    # msGrid is a 13x9 array
    #   top 11x9 are actual tiles, in numerical form
    #   bottom 1x9 is for variables i want to keep for that board
    #       0: y pos of last chosen tile
    #       1: x pos of last chosen tile
    #       2: total number of mines
    #       3: number for delay counting after game finishes
    #       4: board status. 0 = regenerate, 1 = first turn, 2 = all other turns, 3 = game won
    #   the 1x9 in between is just 0's
    if msGrid[12,4] == 0:
        #generates new grid
        msGrid[0:13,0:9] = 0
        msGrid[12,4] = 1
        knownMines.clear()
        edgeList.clear()
        mineCount = rnd.randint(18,24)
        msGrid[12,2] = mineCount
        for i in range(0,mineCount):
            [y, x] = [rnd.randint(0,10), rnd.randint(0,8)]
            loops = 0
            while (msGrid[y,x] == 9) & (loops < limit):
                [y,x] = [rnd.randint(0,10), rnd.randint(0,8)]
                loops += 1
            msGrid[y,x] = 9
        msGridExtra[0:13,0:11] = 0
        msGridExtra[1:12,1:10] = msGrid[0:11,0:9]
        for i in range(1,12):
            for j in range(1,10):
                if msGridExtra[i,j] != 9:
                    for k in range(0,8):
                        if msGridExtra[i+adjacents[k][0],j+adjacents[k][1]] == 9:
                            msGridExtra[i,j] += 1
        msGrid[0:11,0:9] = msGridExtra[1:12,1:10]
    elif msGrid[12,4] == 1:
        turn += 1
        #first turn
        msGrid[12,4] = 2
        [y, x] = [rnd.randint(0,10), rnd.randint(0,8)]
        loops = 0
        while (msGrid[y,x] != 0) & (loops < limit):
            [y, x] = [rnd.randint(0,10), rnd.randint(0,8)]
            loops += 1
        msGrid = tileSelect(msGrid,y,x)
    elif msGrid[12,4] == 3:
        turn += 1
        #win condition
        for i in range(0,11):
            for j in range(0,9):
                if msGrid[i,j] == 9:
                    msGrid[i,j] = 21
                else:
                    msGrid[i,j] = 22
        msGrid[12,4] = 2
        msGrid[12,3] = 1
    elif (msGrid[12,3] > 0) & (msGrid[12,3] != 5):
        turn += 1
        #game finish delay counting
        msGrid[12,3] += 1
    elif (msGrid[12,3] == 5):
        #flags the board for regeneration
        msGrid[12,4] = 0
        if msGrid[0,0] in [21,22]:
            turnsTakenToWin.append(turn)
            #print('total mines:',msGrid[12,2])
        else:
            turnsTakenToLose.append(turn)
        #print('turnsTakenToWin:',turnsTakenToWin)
        #print('win turns sum:',sum(turnsTakenToWin))
        #print('turnsTakenToLose:',turnsTakenToLose)
        #print('lose turns sum:',sum(turnsTakenToLose))
        turn = 0
    else:
        turn += 1
        #TEMPORARY TILE CHOOSER!!!
        """
        [y, x, z] = [rnd.randint(0,10), rnd.randint(0,8), rnd.randint(0,14)]
        loops = 0
        while (msGrid[y,x] > 9) & (loops < limit):
            #choose new tile until it's undiscovered
            loops += 1
            [y, x] = [rnd.randint(0,10), rnd.randint(0,8)]
        if (z != 0):
            #if z isn't 0, guarantee a mineless tile. yes this is cheating
            loops = 0
            while (msGrid[y,x] >= 9) & (loops < limit):
                loops += 1
                [y, x] = [rnd.randint(0,10), rnd.randint(0,8)]
        msGrid[12,0:2] = [y,x]
        """
        
        # NON-TEMPORARY TILE CHOOSER!!!!!
        cheatFactor = 1
        #^ 1 is normal probability, 2 is 1/2 prob, 3 is 1/3, etc
        
        msProbabilities = probabilityCalc(msGrid)
        minimum = np.min(msProbabilities)
        minimum2 = np.array(list(set(msProbabilities.flatten())), dtype=np.uint8)
        minimum2.sort()
        minimum2 = minimum2[1]
        minCoords = np.argwhere(msProbabilities == minimum)
        #print(minCoords)
        if len(minCoords) > 1:
            if minimum == 0:
                closenessList = np.zeros((len(minCoords)), dtype=np.uint8)
                for i in range(0,len(minCoords)):
                    closenessList[i] = ((msGrid[12,0] - minCoords[i,0])**2 + (msGrid[12,1] - minCoords[i,1])**2)**0.5
                [y, x] = minCoords[np.argsort(closenessList)[0],0:2]
                if msGrid[y,x] == 9:
                    print('EPIC FAIL!! A MINE WAS WRONGLY MARKED AS A FREEBIE!!!')
            else:
                #guess
                minCoords = np.argwhere(msProbabilities == minimum)
                #[y, x] = minCoords[rnd.randint(0,len(minCoords)-1)]
                [y, x] = edgeList[rnd.randint(0,len(edgeList)-1)]

                #this bit is for getting the overlapping coords between edgeList and minCoords.
                #aset = set([tuple(y) for y in edgeList])
                #bset = set([tuple(z) for z in minCoords])
                unknownEdges = np.array([x for x in set([tuple(y) for y in edgeList]) & set([tuple(z) for z in minCoords])])
                
                if len(unknownEdges) != 0:
                    [y, x] = unknownEdges[rnd.randint(0,len(unknownEdges)-1)]
                else:
                    [y, x] = minCoords[rnd.randint(0,len(minCoords)-1)]
                #print('GUESS')
                #print('[y, x]',[y, x])
                if cheatFactor != 1:
                    if rnd.randint(0,cheatFactor-1) == 0:
                        #print('CHEATING ENGAGED')
                        loops = 0
                        while (msGrid[y,x] == 9) & (loops < limit):
                            if len(unknownEdges) != 0:
                                [y, x] = unknownEdges[rnd.randint(0,len(unknownEdges)-1)]
                            else:
                                [y, x] = minCoords[rnd.randint(0,len(minCoords)-1)]
                            loops += 1
                #if msGrid[y,x] == 9:
                    #print('FAIL!')
                #else:
                    #print('SUCCESS!')
        else:
            [y,x] = minCoords[0,0:2]
        #maxProb = np.amax(msProbabilities)
        #[idx1, idx2] = np.where(msProbabilities == maxProb)
        #print(idx1)
        #print(idx2)
        msGrid[12,0:2] = [y,x]
        msGrid = tileSelect(msGrid,y,x)
        #time.sleep(1)
        
    return [msGrid, turn]


#############################################################################################################################################
def colorGrid(msGrid):
    #print(msGrid[0:11,0:9],'\n\n',msGrid[12,0:9])
    msColor = np.zeros((11, 9, 3), dtype=np.uint8)
    if len(msGrid) == 0:
        return msColor
    colorReference = np.zeros((23, 3), dtype=np.uint8)
    colorReference[0:10] = [61,61,61]       # undiscovered
    colorReference[10:23] = [[192,192,192], # 0 adjacent mines
                             [2,0,255],     # 1 adjacent mines
                             [1,126,0],     # 2 adjacent mines
                             [254,0,0],     # 3 adjacent mines
                             [1,1,126],     # 4 adjacent mines
                             [129,1,1],     # 5 adjacent mines
                             [0,128,128],   # 6 adjacent mines
                             [0,0,0],       # 7 adjacent mines
                             [128,128,128], # 8 adjacent mines
                             [255,0,0],     # loss screen mine
                             [0,0,0],       # loss screen not-mine
                             [255,255,255], # win screen mine
                             [39,203,39]]   # win screen not-mine
    for i in range(0,11):
        for j in range(0,9):
            msColor[i,j] = colorReference[msGrid[i,j]]
            
    return msColor


#############################################################################################################################################
def tileSelect(msGrid,y,x):
    msGridExtra[0:13,0:11] = 10
    msGridExtra[1:12,1:10] = msGrid[0:11,0:9]
    freeTiles = []
    loops = 0
    #if the chosen tile is greater than 10 (uncovered), keep choosing new tiles until it's not
    while (msGridExtra[y+1,x+1] > 10) & (loops < limit):
        loops += 1
        [y, x] = [rnd.randint(0,10), rnd.randint(0,8)]
    if msGridExtra[y+1,x+1] == 0:
        #for checking around any 0 tiles
        i = 0
        msGrid[12,0:2] = [y+1,x+1]
        msGridExtra[y+1,x+1] += 10
        freeTiles = [[y+1,x+1]]
        loops = 0
        while (len(freeTiles) > i) & (loops < limit):
            [y1, x1] = freeTiles[i][0:2]
            if edgeList.count([y1-1,x1-1]) >= 1:
                edgeList.remove([y1-1,x1-1])
                #print('removed',[y1-1,x1-1])
            loops += 1
            for j in range(0,8):
                [y2, x2] = adjacents[j][0:2]
                if (x1+x2 not in [0,10]) & (y1+y2 not in [0,12]):
                    #^check to make sure it's not outside the board
                    if msGridExtra[y1+y2,x1+x2] < 10:
                        if msGridExtra[y1+y2,x1+x2] == 0:
                            freeTiles.append([y1+y2,x1+x2])
                        msGridExtra[y1+y2,x1+x2] += 10
                        #edgeList stuff
                        if edgeList.count([y1+y2-1,x1+x2-1]) >= 1:
                            edgeList.remove([y1+y2-1,x1+x2-1])
                        for k in range(0,8):
                            [y3, x3] = adjacents[k][0:2]
                            if (x1+x2+x3-1 not in [-1,9]) & (y1+y2+y3-1 not in [-1,11]):
                                if msGridExtra[y1+y2+y3,x1+x2+x3] < 10:
                                    if edgeList.count([y1+y2+y3-1,x1+x2+x3-1]) == 0:
                                        edgeList.append([y1+y2+y3-1,x1+x2+x3-1])
                    
            i += 1
    elif msGridExtra[y+1,x+1] == 9:
        #for hitting a mine (GAME OVER)
        msGrid[12,0:2] = [y+1,x+1]
        msGrid[12,3] = 1
        for i in range(0,11):
            for j in range(0,9):
                if msGrid[i,j] == 9:
                    msGrid[i,j] = 19
                else:
                    msGrid[i,j] = 20
        return msGrid
    elif (msGridExtra[y+1,x+1] > 0) & (msGridExtra[y+1,x+1] < 9):
        #for not hitting a mine
        msGridExtra[y+1,x+1] += 10
        msGridExtra[12,0:2] = [y,x]
        i = 0
        if edgeList.count([y,x]) >= 1:
            edgeList.remove([y,x])
        for i in range(0,8):
            [y1, x1] = adjacents[i][0:2]
            if (x+x1+1 not in [0,10]) & (y+y1+1 not in [0,12]):
                if msGridExtra[y+y1+1,x+x1+1] < 10:
                    if edgeList.count([y+y1,x+x1]) == 0:
                        edgeList.append([y+y1,x+x1])
    msGrid[0:11,0:9] = msGridExtra[1:12,1:10]
    
    if np.count_nonzero(np.array(msGrid[0:11,0:9]) < 10) == msGrid[12,2]:
        #win condition
        msGrid[12,4] = 3

    #print(edgeList)
    #print(len(edgeList))
    #print(probabilityCalc(msGrid))
    
    return msGrid


#############################################################################################################################################
def probabilityCalc(msGrid):
    # converted this code from javascript, thanks EmZeeAech on github for that
    msGridExtra[0:13,0:11] = 30
    msGridExtra[1:12,1:10] = msGrid[0:11,0:9]
    msArr[0:11,0:9] = 0
    msProbabilities[0:11,0:9] = 101
    hundredCount = 0
    freebieList = []
    knownMines = []
    arrGrid = []
    edgeArr = []

    for i in range(0,11):
        for j in range(0,9):
            localEdgeCount = 0
            localFreebieCount = 0
            localMineCount = 0
            for k in range(0,8):
                [y1, x1] = adjacents[k][0:2]
                if edgeList.count([i+y1,j+x1]) >= 1:
                    localEdgeCount += 1
                if freebieList.count([i+y1,j+x1]) >= 1:
                    localFreebieCount += 1
                if knownMines.count([i+y1,j+x1]) >= 1:
                    localMineCount += 1
            localEdgeList[i,j] = localEdgeCount
            localFreebieList[i,j] = localFreebieCount
            localMinesList[i,j] = localMineCount

    edgeCount = len(edgeList)
    nonEdgeCount = np.count_nonzero(np.array(msGrid[0:11,0:9]) < 10) - len(edgeList)
    #print(edgeCount, nonEdgeCount)

    ret = True
    while ret:
        [ret, knownMines] = ruleOne(msGridExtra, localMinesList)
        [ret, freebieList] = ruleTwo(msGridExtra, localFreebieList)
        [ret, knownMines, freebieList] = ruleThree(msGridExtra, localMinesList, localFreebieList)
    [ret1, knownMines] = ruleOne(msGridExtra, localMinesList)
    [ret2, freebieList] = ruleTwo(msGridExtra, localFreebieList)
    ruleFour(msGridExtra)

    #print('msGridExtra[1:12,1:10]\n',msGridExtra[1:12,1:10])
    #print('localEdgeList\n',localEdgeList)
    #print('localFreebieList\n',localFreebieList)
    #print('localMinesList\n',localMinesList)
    #print('msProbabilities\n',msProbabilities)

    edgeList.sort(key=lambda yx: (yx[0], yx[1]))

    if len(edgeList) > 0:
        #print('len(knownMines):',len(knownMines))
        #print('knownMines:',knownMines)
        remainingMines = msGrid[12,2] - len(knownMines)
        for i in range(0,11):
            for j in range(0,9):
                if msGridExtra[i+1,j+1] < 10:
                    if (edgeList.count([i,j])) >= 1:
                        if msProbabilities[i,j] == 101:
                            msProbabilities[i,j] = round(remainingMines / (nonEdgeCount + edgeCount) * 100)
                    else:
                        msProbabilities[i,j] = round(remainingMines / (nonEdgeCount + edgeCount) * 100)

        # this part doesn't work.
        # i'm ignoring it, and instead setting the same probability for all uncalculated tiles
        """
        #print('knownMines\n',knownMines)
        #print('freebieList\n',freebieList)
        for i in range(0,11):
            for j in range(0,9):
                localMineCount = 0
                for k in range(0,8):
                    [y1, x1] = adjacents[k][0:2]
                    if knownMines.count([i+y1,j+x1]) >= 1:
                        localMineCount += 1
                localMinesList[i,j] = localMineCount
                
        isMineList = np.zeros((len(edgeList)), dtype=np.uint8)
        generateArrangements(msGridExtra, isMineList, localMinesList, 0, edgeArr)
        probabilityCalculation(edgeArr, msGridExtra, nonEdgeCount)
        """
    else:
        remainingMines = msGrid[12,2] - len(knownMines)
        for i in range(0,11):
            for j in range(0,9):
                if msGridExtra[i+1,j+1] < 10:
                    msProbabilities[i,j] = round(remainingMines / nonEdgeCount * 100)

    fakeGrid = np.zeros((11,9), dtype=np.uint8)
    fakeGrid[0:11,0:9] = 99
    for i in range(0,11):
        for j in range(0,9):
            if msGrid[i,j] >= 10:
                fakeGrid[i,j] = msGrid[i,j] - 10
            else:
                fakeGrid[i,j] = msProbabilities[i,j]
    #print('fakeGrid')
    #print(fakeGrid)
    #print('msProbabilities')
    #print(msProbabilities)
    #time.sleep(10)
    
    return msProbabilities

# if a tile is satisfied by knowing how many surrounding mines there are:
#############################################################################################################################################
def ruleOne(msGridExtra, localMinesList):
    ret = False
    for i in range(1,12):
        for j in range(1,10):
            # only includes tiles that are:
            #   - not outside the border of the grid
            #print('\n',)
            if (localEdgeList[i-1,j-1] > 0):
                #print('Test 1, [i-1,j-1]    ',[i-1,j-1])
                # only includes tiles that are:
                #   - surrounded by at least 1 edge tile
                if (msGridExtra[i,j] >= 10) & (msGridExtra[i,j] != 30):#
                    #print('Test 3, [i-1,j-1]    ',[i-1,j-1])
                    #   - discovered, because localEdges is non-zero behind the front lines
                    if (msGridExtra[i,j] - 10 == localEdgeList[i-1,j-1] - localFreebieList[i-1,j-1]):
                        #print('Test 4, [i-1,j-1]    ',[i-1,j-1])
                        #   - "satisfied" with their number, through knowing how many edge tiles are mines
                        #       ^this one does NOT apply to all tiles on the first iteration
                        for k in range(0,8):
                            [y1, x1] = adjacents[k][0:2]
                            if (edgeList.count([i+y1-1,j+x1-1])) >= 1:
                                #print('Test 5, [i+y1-1,j+x1-1]    ',[i+y1-1,j+x1-1])
                                #   - adjacent tiles that are edge tiles
                                if msProbabilities[i+y1-1,j+x1-1] == 101:
                                    desigMine(localMinesList, i+y1-1, j+x1-1)
                                    ret = True
    return [ret, knownMines]
                            

#############################################################################################################################################
def ruleTwo(msGridExtra, localFreebieList):
    ret = False
    for i in range(1,12):
        for j in range(1,10):
            # only includes tiles that are:
            #   - not outside the border of the grid
            if (localEdgeList[i-1,j-1] > 0):
                #   - surrounded by at least 1 edge tile
                if (msGridExtra[i,j] >= 10) & (msGridExtra[i,j] != 30):
                    #   - discovered, because localEdges is non-zero behind the front lines
                    if (msGridExtra[i,j] - 10 == localMinesList[i-1,j-1]):
                        #   - "satisfied" with their number, through knowing how many
                        #       surrounding tiles are known mines
                        for k in range(0,8):
                            [y1, x1] = adjacents[k][0:2]
                            if (edgeList.count([i+y1-1,j+x1-1])) >= 1:
                                #   - adjacent tiles that are edge tiles
                                if msProbabilities[i+y1-1,j+x1-1] == 101:
                                    #   - unassigned probability
                                    desigFreebie(localFreebieList, i+y1-1, j+x1-1)
                                    ret = True
    return [ret, freebieList]


#############################################################################################################################################
def ruleThree(msGridExtra, localMinesList, localFreebieList):
    # for flagging mines by mimicking arrangement checking.
    # how this works:
    #go through each unknown edge tile
    #^ label adj0
    #go through the adjacent tiles around the tile
    #   ^ label adj1
    #   make sure they are not past the border
    #   make sure they are discovered
    #   go through the adjacent tiles around adj1
    #       ^ label adj2
    #       make sure it's AWAY from adj0
    #       make sure they are not past the border
    #       make sure they are discovered
    #
    #       # "lost" tiles
    #       count1 = 0
    #       for adjacents not in [[y2,x2] + (adjacents, [0,0])]:
    #           if unknown or mine:
    #               count1 += 1
    #       if (tileNum1 - tileNum2) == count1:
    #           designate y0, x0 as mine
    #           for adjacents not in [[-y2,-x2] + (adjacents, [0,0])]:
    #               if unknown:
    #                   designate y0+y1+y2+y3,x0+x1+x2+x3 as freebie
    #
    #       # "gained" tiles
    #       count2 = 0
    #       for adjacents not in [[-y2,-x2] + (adjacents, [0,0])]:
    #           if unknown or mine:
    #               count2 += 1
    #       elif (tileNum2 - tileNum1) == count2:
    #           designate y0, x0 as freebie
    #           for adjacents not in [[y2,x2] + (adjacents, [0,0])]:
    #               if unknown:
    #                   designate y0+y1+y2+y3,x0+x1+x2+x3 as mine
    ret = False
    for [y0,x0] in edgeList:
        # only includes tiles that are:
        #   - edge tiles
        if msProbabilities[y0,x0] == 101:
            #   - unassigned probability
            for [y1, x1] in adjacents:
                if (y0+y1 not in [-1,11]) & (x0+x1 not in [-1,9]):
                    #   adjacent1 is not outside the border
                    if (msGridExtra[y0+y1,x0+x1] >= 10) & (msGridExtra[y0+y1,x0+x1] != 30):
                        #   adjacent1 is discovered
                        for [y2, x2] in adjacents:
                            if (y0+y1+y2 not in [-1,11]) & (x0+x1+x2 not in [-1,9]):
                                #   adjacent2 is not outside the border
                                if (msGridExtra[y0+y1+1,x0+x1+1] >= 10) & (msGridExtra[y0+y1+1,x0+x1+1] != 30):
                                    #   adjacent2 is discovered
                                    if (y2 not in [i[0]-y1 for i in adjacents]) & (x2 not in [i[1]-x1 for i in adjacents]) & ([y1,x1] != [-y2,-x2]):
                                        #   adjacent2 is away from adjacent0
                                        if abs(y2) != abs(x2):
                                            #   no diagonals for adj2
                                            count1 = 0                                                                
                                            count2 = 0
                                            for [y3, x3] in adjacents:
                                                if (y0+y1+y3 not in [-1,11]) & (x0+x1+x3 not in [-1,9]):
                                                    #if unknown or mine:
                                                    if msProbabilities[y0+y1+y3,x0+x1+x3] in [100, 101]:
                                                        #for adjacents not in [[y2,x2] + (adjacents, [0,0])]:
                                                        if (y3 not in [i[0]+y2 for i in adjacents]) & (x3 not in [i[1]+x2 for i in adjacents]) & ([y3,x3] != [y2,x2]):
                                                            #print('[y3,x3]:',[y3,x3])
                                                            print(msProbabilities[y0+y1+y3,x0+x1+x3])
                                                            count1 += 1
                                                        if (y3 not in [i[0]-y2 for i in adjacents]) & (x3 not in [i[1]-x2 for i in adjacents]) & ([y3,x3] != [y2,x2]):
                                                            count2 += 1
                                                            #print('[y3,x3]:',[y3,x3])
                                                            print(msProbabilities[y0+y1+y3,x0+x1+x3])
                                            #if (tileNum1 - tileNum2) == count1:
                                            if (msGridExtra[y0+y1+1,x0+x1+1] - msGridExtra[y0+y1+y2+1,x0+x1+y2+1]) == count1:
                                                #print('Test 1, [y0, x0], [y1, x1], [y2, x2]: ',[y0, x0], [y1, x1], [y2, x2])
                                                #print('count1, count2:',count1, count2)
                                                desigMine(localMinesList, y0, x0)
                                                #for adjacents not in [[-y2,-x2] + (adjacents, [0,0])]:
                                                for [y3, x3] in adjacents:
                                                    if (y3 not in [i[0]-y2 for i in adjacents]) & (x3 not in [i[1]-x2 for i in adjacents]) & ([y3,x3] != [y2,x2]):
                                                        if msProbabilities[y0+y1+y2+y3,x0+x1+y2+x3] == 101:
                                                            if msGridExtra[y0+y1+y2+y3+1,x0+x1+y2+x3+1] < 10:
                                                                #print('Test 1.1, [y0+y1+y2+y3, x0+x1+y2+x3]: ',[y0+y1+y2+y3,x0+x1+y2+x3])
                                                                desigFreebie(localFreebieList, y0+y1+y2+y3, x0+x1+x2+x3)
                                                ret = True
                                                #print('knownMines:',knownMines)
                                                return [ret, knownMines, freebieList]
                                            #elif (tileNum2 - tileNum1) == count2:
                                            elif (msGridExtra[y0+y1+y2+1,x0+x1+y2+1] - msGridExtra[y0+y1+1,x0+x1+1]) == count2:
                                                #print('Test 2, [y0, x0], [y1, x1], [y2, x2]: ',[y0, x0], [y1, x1], [y2, x2])
                                                #print('count1, count2:',count1, count2)
                                                desigFreebie(localFreebieList, y0, x0)
                                                #for adjacents not in [[y2,x2] + (adjacents, [0,0])]:
                                                for [y3, x3] in adjacents:
                                                    if (y3 not in [i[0]+y2 for i in adjacents]) & (x3 not in [i[1]+x2 for i in adjacents]) & ([y3,x3] != [y2,x2]):
                                                        if msProbabilities[y0+y1+y2+y3,x0+x1+y2+x3] == 101:
                                                            if msGridExtra[y0+y1+y2+y3+1,x0+x1+y2+x3+1] < 10:
                                                                #print('Test 2.1, [y0+y1+y2+y3, x0+x1+y2+x3]: ',[y0+y1+y2+y3,x0+x1+y2+x3])
                                                                desigMine(localMinesList, y0+y1+y2+y3, x0+x1+x2+x3)
                                                ret = True
                                                #print('knownMines:',knownMines)
                                                return [ret, knownMines, freebieList]
    return [ret, knownMines, freebieList]


#############################################################################################################################################
# "Label isolated cells that have independently determined probabilities" :nerd:
def ruleFour(msGridExtra):
    for i in range(1,12):
        for j in range(1,10):
            if (msGridExtra[i,j] > 10) & (msGridExtra[i,j] != 30):
                # only includes tiles that are:
                #   - discovered
                if (localEdgeList[i-1,j-1] > 2):
                    #print('Test 1, [i-1,j-1]    ',[i-1,j-1])
                    #   - surrounded by at least 3 edge tiles
                    count1 = 0
                    for k in range(0,8):
                        [y1, x1] = adjacents[k][0:2]
                        if (i+y1-1 not in [-1,11]) & (j+x1-1 not in [-1,9]):
                            #^ border patrol
                            if (edgeList.count([i+y1-1,j+x1-1])) >= 1:
                                #   - edge tile
                                #openCount of current adjacent tile needs to have 1 adjacent open tile only
                                count2 = 0
                                for l in range(0,8):
                                    [y2, x2] = adjacents[l][0:2]
                                    if (i+y1+y2-1 not in [-1,11]) & (j+x1+x2-1 not in [-1,9]):
                                        #^ border patrol 2 electric boogaloo
                                        if (msGridExtra[i+y1+y2,j+x1+x2] > 10) & (msGridExtra[i+y1+y2,j+x1+x2] != 30):
                                            count2 += 1
                                if count2 == 1:
                                    count1 += 1
                    
                    if count1 == localEdgeList[i-1,j-1]:
                        if msProbabilities[i-1,j-1] == 101:
                            probability = round((msGrid[i-1,j-1] - 10) / localEdgeList[i-1,j-1] * 100)
                            for k in range(0,8):
                                [y1, x1] = adjacents[k][0:2]
                                if (i+y1-1 not in [-1,11]) & (j+x1-1 not in [-1,9]):
                                    #^ border patrol 3 i need to pee
                                    msProbabilities[i+y1-1,j+x1-1] = probability


#############################################################################################################################################
def desigMine(localMinesList, y, x):
    msProbabilities[y,x] = 100
    if knownMines.count([y,x]) == 0:
        knownMines.append([y,x])
    for [y1, x1] in adjacents:
        #[y1, x1] = adjacents[k][0:2]
        if (y+y1 not in [-1,11]) & (x+x1 not in [-1,9]):
            localMinesList[y+y1,x+x1] += 1


#############################################################################################################################################
def desigFreebie(localFreebieList, y, x):
    msProbabilities[y,x] = 0
    if freebieList.count([y,x]) == 0:
        freebieList.append([y,x])
    for [y1, x1] in adjacents:
        #[y1, x1] = adjacents[k][0:2]
        if (y+y1 not in [-1,11]) & (x+x1 not in [-1,9]):
            localFreebieList[y+y1,x+x1] += 1


#############################################################################################################################################
def generateArrangements(msGridExtra, isMineList, localMinesList, index, edgeArr):
    #this thing is broken somehow, fix it
    # for every edge tile, try to place a mine as soon as possible
    # if it doesn't fit, move on to the next edge tile, until 
    # for every successful array, lock the last mine's previous position
    # if a mine cannot find a spot on the board, the board is failed,
    #   and the second to last mine gets locked out
    # the first mine that has to move from these changes unlocks every following edge tile
    fakeGrid = np.zeros((11,9), dtype=np.uint8)
    fakeGrid[0:11,0:9] = 99
    for i in range(0,11):
        for j in range(0,9):
            if msGrid[i,j] >= 10:
                fakeGrid[i,j] = msGrid[i,j] - 10
    
    tileLocks = np.ones((len(isMineList)), dtype=bool)
    for i in range(0,len(edgeList)):
        [y, x] = edgeList[i][0:2]
        if (knownMines.count([y,x])) >= 1:
            isMineList[i] = 1
            tileLocks[i] = True
        if (freebieList.count([y,x])) >= 1:
            isMineList[i] = 0
            tileLocks[i] = False
    pattern = isMineList

    #print(np.array_equal(tileLocks[:], (isMineList == 1)))
    while not (np.array_equal(tileLocks[:], (isMineList == 1))):
        #tileLocks[:] = True
        pattern[:] = 2
        for i in range(0,len(edgeList)):
            [y, x] = edgeList[i][0:2]
            if (knownMines.count([y,x])) >= 1:
                pattern[i] = 1
            #if (freebieList.count([y,x])) >= 1:
                #tileLocks[i] = False

        #print('tileLocks:\n',tileLocks)
        #print('isMineList:\n',isMineList)
        #print('\nedgeList:\n',edgeList)
        for i in range(0,len(isMineList)):
            [y, x] = edgeList[i][0:2]
            if pattern[i] == 2:
                if tileLocks[i]:
                    if canBeMine(msGridExtra, pattern, localMinesList, x, y):
                        #print('[y, x], i = ',[y, x],i)
                        #print('pattern:\n',pattern)
                        #print('tileLocks:\n',tileLocks)
                        pattern[i] = 1 #set a mine
                    elif canNotBeMine(msGridExtra, pattern, localMinesList, x, y):
                        pattern[i] = 0 #set a safe spot
                    else:
                        #print('\ni:',i)
                        #print('IMPOSSIBLE ARRAY')
                        idx = np.where(pattern == 1)[0][-1]
                        tileLocks[idx] = False
                        if idx < len(tileLocks):
                            tileLocks[idx+1:] = True
                        break
                else:
                    if not canBeMine(msGridExtra, pattern, localMinesList, x, y):
                        if not canNotBeMine(msGridExtra, pattern, localMinesList, x, y):
                            #print('\ni:',i)
                            #print('IMPOSSIBLE ARRAY')
                            idx = np.where(pattern == 1)[0][-1]
                            tileLocks[idx] = False
                            if idx < len(tileLocks):
                                tileLocks[idx+1:] = True
                            break
            if pattern[i] == 1:
                fakeGrid[y,x] = 20
            elif pattern[i] == 0:
                fakeGrid[y,x] = msGrid[y,x] + 10
            #else:
                #print('\n\n\nAYO [y,x] is FUCKED UP  ', [y,x])
    
        #print('fakeGrid:\n',fakeGrid)
        edgeArr.append(pattern)
        idx = np.where(pattern == 1)[0][-1]
        tileLocks[idx] = False
        if idx < len(tileLocks):
            tileLocks[idx+1:] = True
        #print('idx:',idx)
        #print('tileLocks:\n',tileLocks)
        #print('pattern:\n',pattern)
        time.sleep(30)
    #print('\nedgeArr\n',edgeArr)
    #print('len(edgeArr)\n',len(edgeArr))
    time.sleep(60)


#############################################################################################################################################
def canBeMine(msGridExtra, pattern, localMinesList, x, y):
    for i in range(0,8):
        [y1, x1] = adjacents[i][0:2]
        if (y+y1 not in [-1,11]) & (x+x1 not in [-1,9]):
            if msGridExtra[y+y1+1,x+x1+1] >= 10:
                minecount = 0
                

    
    #print('localMinesList\n',localMinesList)
    for i in range(0,8):
        [y1, x1] = adjacents[i][0:2]
        if (y+y1 not in [-1,11]) & (x+x1 not in [-1,9]):
            if msGridExtra[y+y1+1,x+x1+1] >= 10:
                count = 0
                #print()
                #print('[y, x]:',[y,x])
                #print('[y+y1, x+x1]:',[y+y1,x+x1])
                for j in range(0,8):
                    [y2, x2] = adjacents[j][0:2]
                    if (y+y1+y2 not in [-1,11]) & (x+x1+x2 not in [-1,9]):
                        #print('[y+y1+y2, x+x1+x2]:',[y+y1+y2,x+x1+x2])
                        if (edgeList.count([y+y1+y2,x+x1+x2])) >= 1:
                            idx = edgeList[:].index([y+y1+y2,x+x1+x2])
                            #print('idx:',idx)
                            if pattern[idx] == 1:
                                count += 1
                                #print('count:',count)
                #print('tile number, count:',(msGridExtra[y+y1+1,x+x1+1] - 10),count)
                if (msGridExtra[y+y1+1,x+x1+1] - 10) <= count:
                    return False
    return True


#############################################################################################################################################
def canNotBeMine(msGridExtra, pattern, localMinesList, x, y):
    for i in range(0,8):
        [y1, x1] = adjacents[i][0:2]
        if (y+y1 not in [-1,11]) & (x+x1 not in [-1,9]):
            if msGridExtra[y+y1+1,x+x1+1] >= 10:
                count1 = 0
                count2 = 0
                #print()
                #print('[y, x]:',[y,x])
                #print('[y+y1, x+x1]:',[y+y1,x+x1])
                #choose an adjacent tile, get it's surrounding tiles, see if it works
                for j in range(0,8):
                    [y2, x2] = adjacents[j][0:2]
                    if (y+y1+y2 not in [-1,11]) & (x+x1+x2 not in [-1,9]):
                        #print('[y+y1+y2, x+x1+x2]:',[y+y1+y2,x+x1+x2])
                        if (edgeList.count([y+y1+y2,x+x1+x2])) >= 1:
                            idx = edgeList[:].index([y+y1+y2,x+x1+x2])
                            #print('idx:',idx)
                            if pattern[idx] == 0:
                                count1 += 1
                                #print('count1:',count1)
                            if pattern[idx] == 2:
                                count2 += 1
                                #print('count2:',count2)
                if count2 == 1:
                    #would there be problems if this 2 were a 0 instead?
                    
                    #print('tile number, adj edges, count, adj freebies:',(msGridExtra[y+y1+1,x+x1+1] - 10), localEdgeList[y+y1,x+x1], count, localFreebieList[y+y1,x+x1])
                    #print(localEdgeList)
                    #print('[y+y1, x+x1]:',[y+y1,x+x1])

                    # is the tile number >= the known number of adjacent mines
                    # if (msGridExtra[y+y1+1,x+x1+1] - 10) >= localEdgeList[y+y1,x+x1] - count - localFreebieList[y+y1,x+x1]:
                    # ^ THIS LINE IS COMMENTED BECAUSE count IS UNDEFINED. PLEASE FIX IF THIS IS EVER USED
                        return True
    return False


#############################################################################################################################################
def probabilityCalculation(edgeArr, msGridExtra, nonEdgeCount):
    # Store where mines are placed in each arrangement and find the
    #   total number of arrangements
    arrCount = 0
    for k in range(0,len(edgeArr)):
        minesPlaced = 0
        for i in range(0,len(edgeArr[k])):
            if edgeArr[k][i] == 100:
                minesPlaced += 1
        remainingMines = msGrid[12,2] - minesPlaced - len(knownMines)
        #print(remainingMines, msGrid[12,2], minesPlaced, len(knownMines))
        #print('remainingMines, Total Mines, minesPlaced, len(knownMines)')
        if (remainingMines >= 0) & (remainingMines <= nonEdgeCount):
            nonEdgeCombos = combinations(nonEdgeCount, remainingMines)
            #print('nonEdgeCombos',nonEdgeCombos)
            for i in range(0,len(edgeArr[k])):
                if edgeArr[k][i] == 1:
                    #
                    msArr[edgeList[i][0],edgeList[i][1]] += nonEdgeCombos
            arrCount += nonEdgeCombos
            for i in range(0,11):
                for j in range(0,9):
                    if msGridExtra[i+1,j+1] < 10:
                        if (edgeList.count([i,j])) == 0:
                            msArr[i,j] += remainingMines / nonEdgeCount * nonEdgeCombos

    #print('arrCount',arrCount)
    # Calculate probability of each cell by dividing the number of
    #   arrangements with mines in each cell by total arrangements
    for i in range(0,11):
        for j in range(0,9):
            if msProbabilities[i,j] == 101:
                if (edgeList.count([i,j])) >= 1:
                    msProbabilities[i,j] = round(msArr[i,j] / arrCount * 100)
                    # arrCount is likely wrong because of generateArrangements
                else:
                    if msGridExtra[i+1,j+1] < 10:
                        msProbabilities[i,j] = round(msArr[i,j] / arrCount * 100)
                        # arrCount is likely wrong because of generateArrangements


#############################################################################################################################################
def combinations(n, r):
    if (n == r) | (r == 0):
        return 1
    else:
        if (r < n - r):
            r = n - r
        return productRange(r + 1, n) / productRange(1, n - r)


#############################################################################################################################################
def productRange(a, b):
    prd = np.dtype('float128')
    prd = a
    a += 1
    while (a < b):
        #print(prd)
        prd *= a
        a += 1
    return prd


#############################################################################################################################################
# MAIN #
#############################################################################################################################################
setWindowTitle("Pixoo Script")
weatherData = [0,0]
[weatherData, precipArr] = fetchWeatherData()
try:
    if (datetime.now().hour <= 5) | (datetime.now().hour >= 20):
        pixoo16.set_system_brightness(1)
    else:
        pixoo16.set_system_brightness(100)
    pixoo16.draw_pic('amogloss.png') #meme
except OSError as err:
    print("OS error:", err)
    connected = pixoo16.check_connection(connected)
    if connected == False:
        print("CONNECTION ERROR")
        #system('popup.bat')
        #system("msdt -skip TRUE -id BluetoothDiagnostic -ep CortanaSearch")
while True:
    lastSubSecond = time.time()
    time.sleep(0.001)
    if (time.time()%1 - lastSubSecond%1) < 0:
        try:
            #pixoo16.draw_pic('frame_current.png')
            #t = time.time()
            if (time.time()%300 - lastSubSecond%300) < 0:
                [weatherData, precipArr] = fetchWeatherData()
                if (datetime.now().hour <= 7) | (datetime.now().hour >= 22):
                    pixoo16.set_system_brightness(1)
                else:
                    pixoo16.set_system_brightness(100)
            [msGrid, turn] = drawframe(weatherData, precipArr, msGrid, turn) # this saves the next frame
            pixoo16.draw_pic('frame_current.png')
            #print(time.time() - t,'elapsed time to compute')
            #time.sleep(0.8)
        except OSError as err:
            print("OS error:", err)
            connected = pixoo16.check_connection(connected)
            if connected == False:
                print("CONNECTION ERROR")
                #system("msdt -skip TRUE -id BluetoothDiagnostic -ep CortanaSearch")
