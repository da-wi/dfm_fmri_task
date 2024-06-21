# -*- coding: utf-8 -*-
"""
Dynamic face-matching paradigm
Author: David Willinger, Developmental Neuroimaging Group, University Hospital of Psychiatry Zurich, University of Zurich

This programme is licensed under CC BY-NC-SA 4.0 
https://creativecommons.org/licenses/by-nc-sa/4.0/


Changes Version 5
- add python 3 compatibility

Changes Version 4
- add possibility to set probe faces manually

Changes Version 3.1.1
- add fixed objects 
- add possibility to use linear and non-linear objects
- add dependency on animatedobject (non-linear objects)

Changes Version 3.1 
- add flag for setting object presentation same as max. individual faces
- adjust condition order such that no emotion presentation is the same
- change difficulty of objects
"""


import sys, pygame
import random, copy
import os
import time #http://stackoverflow.com/questions/20023709/resetting-pygames-timer
import logging
from animatedsprite import AnimatedSprite
from animatedobject import AnimatedObject
import argparse
import gc
from xml.dom import minidom
from collections import Counter


############################################
########## READ MAPPING FILE ###############
############################################
emotion_list = []
xmldoc = minidom.parse('emotion_mapping.xml')
itemlist = xmldoc.getElementsByTagName('emotion')
for s in itemlist:
    targets = s.getElementsByTagName('target')
    tmp_list = []
    for t in targets:
        tmp_list.append(str(t.childNodes[0].nodeValue))
    emotion_list.append(tmp_list)

############################################
########## PARSE ARGUMENTS #################
############################################
parser = argparse.ArgumentParser(description="Dynamic face-matching task")
parser.add_argument('subjectid', help='subject id')
parser.add_argument('-b', '--baseline', help='the baseline in seconds', default='8')
parser.add_argument('-c', '--colortype', help='[1|2] colortype 1 = black/white, colortype 2 = grey/black', default='1')
parser.add_argument('-e', '--emotions', help='Input of emotion trials as string e.g. -e "0,5,6" \n\r 0...neutral\n\r 5...happy\n 6...sad', default='0,5,6,8')
parser.add_argument('--emulation', help='Sets emulation mode for use outside the scanner', action='store_true')
parser.add_argument('-f', help='Enforce order of face trials', action='store_true')
parser.add_argument('-l', '--forcelogdir', help='Force Logdir creation',action='store_true')
parser.add_argument('-i', '--initstim', help='NOT SUPPORTED. [faces|objects] Specifies whether the paradigm starts with faces or objects, default=random', default='random')
parser.add_argument('-L', help='EXPERIMENTAL! Will load all the trial images at the beginning, it will present without lag independent of baseline, but do this only if enough RAM is available!! Can crash the programme.', action='store_false')
parser.add_argument('-m', '--testmode', help='testmode', default='production')
parser.add_argument('-n', '--notrials', help='number of trials per block', default='5')
parser.add_argument('-o', '--objectman', help='insert interleaved object blocks (usually not needed when using -e "8" flag)', action='store_false')
parser.add_argument('-N', '--nonlinearobjects', help='setting non-linearity offset for objects, default=1', default='1')
parser.add_argument('-r', '--run', help='[1|2] determines the run number for the subject', default='1')
parser.add_argument('-R', '--repetitions', help='specifies the number of repetitions for each block, default=4', default='4')
parser.add_argument('-s', '--screenmode', help='[single|dual] dual or single screenmode', default='dual')
parser.add_argument('-t', '--taskmode', help='[dynamic|static] determines if the task is static', default='dynamic')
parser.add_argument('-tt', '--trialtime', help='the trialtime in seconds', default='4')
args = parser.parse_args()

if args.subjectid == "":
    print("\n\nNo subject ID was specified. Abort.")
    parser.exit(1, None)

# parameter: DUALSCREEN MODE (dual,single), COLOR_TYPE (1,2), RUN NUMBER ( 1,2 )

if args.screenmode == "dual":
    DUALSCREEN = True
else:
	DUALSCREEN = False

COLOR_GREY = (214,214,212)
COLOR_BLACK = (10,10,10)
COLOR_WHITE = (230,230,230)

try:
    baseline_time = int(args.baseline) #TODO: change that later to 7 or 8
except ValueError:
    print("No valid baseline given (enter in seconds), e.g. -b 7")
    sys.exit(1)

if args.colortype == "1":
    BG_COLOR = COLOR_BLACK
    FONT_COLOR = COLOR_WHITE
elif args.colortype == "2":
    BG_COLOR = COLOR_GREY
    FONT_COLOR = COLOR_BLACK
else:
	print('No valid color defined! Abort.')
	sys.exit()

if args.run == "1":
	RUNCOMMENT = "1"
elif args.run == "2":
	RUNCOMMENT = "2"
else:
	print('WARNING! Unusual run number!! Continuing...')
	RUNCOMMENT = args.run

if args.taskmode == "dynamic":
    morph = 1
elif args.taskmode == "static":
    morph = 0
else:
    print('No valid taskmode defined! Abort.')
    sys.exit(1)

if args.initstim == "random":
    start_with_faces = random.randint(0, 1)
elif args.initstim == "faces":
    start_with_faces = 1
elif args.initstim == "objects":
    start_with_faces = 0
else:
    print('No valid initstim defined! Abort.')
    sys.exit(1)

try:
    repetitions = int(args.repetitions)
    if repetitions < 1:
        raise ValueError('Number of repetitions must be > 1')
except ValueError:
    print('No valid repetitions defined! Abort.')
    sys.exit(1)

try:
    notrials = int(args.notrials)
    if notrials < 1:
        raise ValueError('Number of trials must be > 1')
except ValueError:
    print('No valid number of trials defined! Abort.')
    sys.exit(1)

objectman = args.objectman

input_ttl = args.emotions
ttl_list = input_ttl.split(',')

try:
    ttl_list = [int(i) for i in ttl_list]
except ValueError:
    print("Invalid trialtypes specified. They must be in the form of e.g. -e \"0,5,6\" or -e \"4\"")
    print("Abort.")
    sys.exit(1)

try:
    nonlinearobjects_offset = float(args.nonlinearobjects)
    if nonlinearobjects_offset != 0:
        random_objects = False
except ValueError:
    print("Invalid Offset for nonlinearobjects defined. Allowed values: 0-Inf, float ; e.g. -N 0.14")
    print("Abort.")
    sys.exit(1)  


enforce_order = args.f
load_in_blocks = args.L

sprite_face = None
face_stimuli = []

############################################
########## INIT LOGGER #####################
############################################
os.makedirs('logs', exist_ok=True)

logger = logging.getLogger()
output_handler = logging.StreamHandler()
content = ""
with open('logs/current.txt', "w+") as f:
	content = f.readlines()

content = args.subjectid
logdir = 'logs/'+content
logfile = '%s_edt_run_%s_%s.csv' %  (args.taskmode,RUNCOMMENT,str(time.time()))

created_logdir = False
if not os.path.exists(logdir):
	if args.forcelogdir == False:
		print("Logdir for subject %s does not exist, do you want to create it? [Y/n]" % args.subjectid, end=' ')
		yes = {'yes','y', 'ye', ''}
		no = {'no','n'}
		while True:
			choice = input().lower()
			if choice in yes:
				os.makedirs(logdir)
				created_logdir = True
				break
			elif choice in no:
				print("No Logdir created. Abort.")
				sys.exit(1)
			else:
				sys.stdout.write("Please respond with 'yes' or 'no'")
	else:
		os.makedirs(logdir)
		created_logdir = True


file_handler = logging.FileHandler(os.path.join(logdir,logfile))
#formatter = logging.Formatter('%(asctime)s;%(name)-12s %(levelname)-8s %(message)s')
formatter = logging.Formatter('%(message)s')
output_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(output_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
logger.debug('Timestamp;Event;Target_stim;Good_stim;Bad_stim;position;answer(4=L,1=R);answer_type')
formatter = logging.Formatter('%(created)s;%(message)s')
output_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

if  created_logdir == True:
	logger.debug('create_logdir;%s',args.subjectid )


size = width, height = 800, 600

######## set paths to folders for faces and objects    ##################
facespath = 'assets/edt'
odtpath = 'odt'
morphpath = 'assets/animated' #'animated'

########   initializations for edt    ##################
emotions = ['neutral', 'angry', 'contemptuous','disgusted', 'fearful','happy', 'sad', 'surprised']

morphemotions = emotion_list

#morphemotions =  [
#    ['neutral','surprised'],
#    ['angry','fearful'],
#    ['contemptuous','sad'],
#    ['disgusted','sad'],
#    ['fearful','angry'],
#    ['happy','surprised','neutral'],
#    ['sad','disgusted'],
#    ['surprised','neutral']]  

#['angry', 'contemptuous']

#negative_emotions =  ['angry','contemptuous', 'disgusted', 'fearful', 'sad']

# emotions to match with a specific target emotion
#angry_fearful_emotions =  ['angry', 'fearful']

#sad_emotions =  ['disgusted','neutral']
#happy_emotions =  ['surprised','neutral']
#neutral_emotions = ['neutral','surprised']
#surprised_emotions = ['neutral','surprised']
angry_fearful_emotions = morphemotions[1]
sad_emotions = morphemotions[6]
happy_emotions = morphemotions[5]
neutral_emotions = morphemotions[0]

print(morphemotions)

################################################################
########  TRIAL TYPE DEFINITION            #######################
################################################################

# 8 = object
trial_type_list = []

# check if two subsequent blocks are same
print(ttl_list)
diff_list = [ttl_list[i+1]-ttl_list[i] for i in range(len(ttl_list)-1)]
contains_zero = True

ttl_list = ttl_list * repetitions

permutations = 0
if enforce_order == False:
    while contains_zero and permutations < 100:
        random.shuffle (ttl_list) # shuffle blocks
        #print ttl_list
        diff_list = [ttl_list[i+1]-ttl_list[i] for i in range(len(ttl_list)-1)]
        if 0 in diff_list:
            contains_zero = True
        else:
            contains_zero = False
        permutations = permutations + 1    

if permutations == 100:
    print("No permutations found. Continuing with normal randomization...")
    random.shuffle(ttl_list)
print("TTL",ttl_list)

# add object trials
tmp_list = []
if objectman == True:
    print("Manual object setting.")
    for i in range(0, len(ttl_list)):
        tmp_list.extend([ttl_list[i]])
else:    
    for i in range(0, len(ttl_list)):
        tmp_list.extend([ttl_list[i],8])
print(tmp_list)

# generate trials in block
new_list = []
for i in range(0,len(tmp_list)):
    new_list.append( [tmp_list[i]]*notrials)
print("New List",new_list)

matrix = new_list 
print("Matrix",matrix)

# here we generate a balanced list of target emotion
mapping_targetemo = [[7,0],[],[],[],[],[5,7,0],[6,3],[7,0],[8]]
out = copy.deepcopy(matrix)
for i in range(0,len(out)):
    trial_emo = out[i][0]
    for j in range(0,len(out[i])):
        # e.g. a[i][j] = 5
        out[i][j] = mapping_targetemo[trial_emo][j%len(mapping_targetemo[trial_emo])]

for i in range(0,len(out)):
    random.shuffle(out[i])

print("Targetemotions",out)
target_emotion_list = out
# print trial_type_list
#if start_with_faces:
    #print 'Let us start with faces today'
#    trial_type_list = matrix[0] + [8] * (len(matrix[0])) + trial_type_list
#else:
    #print 'Let us start with objects today'
#    trial_type_list = [8] * (len(matrix[0])) + trial_type_list + matrix[0]
trial_type_list = copy.deepcopy(matrix)

# flatten the list / make it 1D
trial_type_list = [j for i in trial_type_list for j in i]
target_emotion_list = [j for i in target_emotion_list for j in i]

print('Trial type list: ',trial_type_list)
index_trial = 0
face_index_trial = 0

num_trials_blocks = [notrials] * len(matrix) * 2
index_trials_blocks = 0

faceslist =  [f for f in os.listdir(facespath) if os.path.isfile(os.path.join(facespath,f)) ]
peoplenumbers = [face[8:10] for face in faceslist] # get all numbers from filenames
peoplenumbers = sorted(list(set(peoplenumbers))) # get unique numbers
peoplenumbers.remove('b') # for some weird reason there is a "b" in the list --> remove it or it crashes

corners = ['_5', '_6','_7','_8']
corners_numbers = [ 5, 6, 7, 8] #, 7, 8]


# directories in morphpath
morphlist = [f for f in os.listdir(morphpath) if os.path.isdir(os.path.join(morphpath,f)) ]
morphnumbers = [obj[8:10] for obj in morphlist] # get all numbers from filenames
morphnumbers = sorted(list(set(morphnumbers))) # get unique numbers

################################################################
########  TIMING PARAMETERS             #######################
################################################################
try:
    ttrial = int(args.trialtime)
except ValueError:
    print("Please provide a valid trial time (in seconds). Abort.")
    sys.exit(1)

block_duration_morphing = ttrial * len(matrix[0])
m, s = divmod(len(trial_type_list)*ttrial + len(matrix)*baseline_time, 60)
print("# Blocks:      ", len(matrix))
print("Block duration:", ttrial*len(matrix[0]),"s")
print("Baseline:      ", baseline_time,"s")
print("Task duration:  %02d:%02d" % (m,s))
################################################################
########  INITIALIZTION OF PYGAME SCREEN #######################
################################################################
pygame.init()
size = width, height = 800,600

if DUALSCREEN == True:
	# THIS IS A HACK FOR DUAL SCREEN
    x = 1920
    y = 0
    screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h # call before set_mode to get screen size
    print('Dual screen enabled: '+str(screen_width)+'x'+str(screen_height))
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (screen_width,y)
    screen = pygame.display.set_mode(size,pygame.NOFRAME)
else:
	screen = pygame.display.set_mode(size)

screen.fill(BG_COLOR)

#####################################################################
#############     DEFINE FUNCTIONS     ##############################
#####################################################################
def show_cross(): # can only be called when initialized
    logger.debug('showing_crossfade')
    screen.fill(BG_COLOR)
    # font = pygame.font.SysFont('Arial', 200)
    font = pygame.font.Font(None, 150)
    text = font.render("•", 1, FONT_COLOR)
    textpos = text.get_rect()
    textpos.centerx = screen.get_rect().centerx
    textpos.centery = screen.get_rect().centery
    screen.blit(text, textpos)
    pygame.display.flip()


def start_screen():
    logger.debug('showing_start_screen')
    screen.fill(BG_COLOR)
    font = pygame.font.Font(None, 60)
    text = font.render("Gesichter und Objekte unterscheiden", 1, FONT_COLOR)
    textpos = text.get_rect()
    textpos.centerx = screen.get_rect().centerx
    textpos.centery = screen.get_rect().centery-50
    screen.blit(text, textpos)
    font = pygame.font.Font(None, 36)
    text = font.render("Ordnen Sie dem oberen Bild das passende untere Bild zu", 1, FONT_COLOR)
    textpos = text.get_rect()
    textpos.centerx = screen.get_rect().centerx
    textpos.centery = screen.get_rect().centery+50
    screen.blit(text, textpos)

    if args.emulation == True:
        font = pygame.font.Font(None, 20)
        ustr = "★"
        text = font.render("Zum Starten \"t\" drücken", 1, FONT_COLOR)
        textpos = text.get_rect()
        textpos.centerx = screen.get_rect().centerx
        textpos.centery = screen.get_rect().centery + 200
        screen.blit(text, textpos)

        font = pygame.font.Font(None, 20)
        ustr = "★"
        text = font.render("Um das linke/rechte Gesicht/Object auszuwählen 1 bzw. 4 drücken", 1, FONT_COLOR)
        textpos = text.get_rect()
        textpos.centerx = screen.get_rect().centerx
        textpos.centery = screen.get_rect().centery + 230
        screen.blit(text, textpos)

    pygame.display.flip()

# target INDEX (not emotion) for positive, negative and neutral
# [target,probe,distractor,emotion_type(0 or 1)]
#targets = [[1,4,1,0],[3,1,5,0],[5,3,4,1],[2,5,3,1],[4,5,2,1],[5,1,5,0],[1,2,2,1],[3,4,1,1],[2,3,4,0],[4,2,3,0],[1,4,1,1],[5,3,4,0],[2,5,3,0],[3,1,5,1],[4,5,2,0],[5,1,5,1],[3,4,1,0],[1,2,2,0],[2,3,4,1],[4,2,3,1]]
#targets_positive = [[1,4,1,0],[5,3,4,0],[2,5,3,1],[3,1,5,1],[4,5,2,1],[5,1,5,1],[3,4,1,1],[1,2,2,0],[2,3,4,0],[4,2,3,0],[1,4,1,1],[5,3,4,0],[2,5,3,0],[3,1,5,1],[4,5,2,0],[5,1,5,1],[3,4,1,0],[1,2,2,0],[2,3,4,1],[4,2,3,1]]
#targets_neutral  = [[1,4,1,1],[5,3,4,0],[2,5,3,1],[3,1,5,0],[4,5,2,1],[5,1,5,0],[3,4,1,1],[1,2,2,1],[2,3,4,0],[4,2,3,0],[1,4,1,1],[5,3,4,0],[2,5,3,0],[3,1,5,1],[4,5,2,0],[5,1,5,1],[3,4,1,0],[1,2,2,0],[2,3,4,1],[4,2,3,1]]

targets = [ [1,2,3,1],[1,2,3,0],[4,5,1,0],[1,2,3,1],[1,2,3,0],[4,5,1,0],[4,5,1,1],[2,3,4,1],[2,3,4,0],[5,1,2,0],[5,1,2,1],[3,4,5,1],[3,4,5,0],[2,4,1,1],[2,4,1,0],[1,3,5,0],[1,3,5,1],[5,2,4,1],[5,2,4,0],[3,5,2,0],[3,5,2,1],[4,1,3,1],[4,1,3,0] ]

# emotional_faces (emotion_type 0 and emotion type 1, e.g. sadness and disgust)
faces_negative = [ [ 'Rafd090_47_Caucasian_male_sad_frontal','Rafd090_03_Caucasian_male_sad_frontal','Rafd090_16_Caucasian_female_sad_frontal','Rafd090_57_Caucasian_female_sad_frontal', 'Rafd090_14_Caucasian_female_sad_frontal'], ['Rafd090_21_Caucasian_male_disgusted_frontal','Rafd090_01_Caucasian_female_disgusted_frontal','Rafd090_23_Caucasian_male_disgusted_frontal','Rafd090_36_Caucasian_male_disgusted_frontal','Rafd090_04_Caucasian_female_disgusted_frontal']  ]
faces_positive = [ [ 'Rafd090_56_Caucasian_female_happy_frontal', 'Rafd090_71_Caucasian_male_happy_frontal','Rafd090_37_Caucasian_female_happy_frontal','Rafd090_24_Caucasian_male_happy_frontal','Rafd090_38_Caucasian_male_happy_frontal' ], ['Rafd090_08_Caucasian_female_surprised_frontal','Rafd090_15_Caucasian_male_surprised_frontal','Rafd090_12_Caucasian_female_surprised_frontal','Rafd090_26_Caucasian_female_surprised_frontal','Rafd090_47_Caucasian_male_surprised_frontal' ]  ]
#faces_neutral  = [ [ 'Rafd090_15_Caucasian_male_contemptuous_frontal', 'Rafd090_30_Caucasian_male_contemptuous_frontal','Rafd090_07_Caucasian_male_contemptuous_frontal','Rafd090_03_Caucasian_male_contemptuous_frontal','Rafd090_33_Caucasian_male_contemptuous_frontal'], ['Rafd090_46_Caucasian_male_neutral_frontal','Rafd090_15_Caucasian_male_neutral_frontal','Rafd090_08_Caucasian_female_neutral_frontal','Rafd090_08_Caucasian_female_neutral_frontal','Rafd090_12_Caucasian_female_neutral_frontal' ]  ]
faces_neutral  = [ [ 'Rafd090_32_Caucasian_female_contemptuous_frontal','Rafd090_30_Caucasian_male_contemptuous_frontal','Rafd090_07_Caucasian_male_contemptuous_frontal','Rafd090_03_Caucasian_male_contemptuous_frontal','Rafd090_33_Caucasian_male_contemptuous_frontal'], ['Rafd090_46_Caucasian_male_neutral_frontal','Rafd090_22_Caucasian_female_neutral_frontal','Rafd090_10_Caucasian_male_neutral_frontal','Rafd090_18_Caucasian_female_neutral_frontal','Rafd090_19_Caucasian_female_neutral_frontal'] ]
tmp_index_negative = 0
tmp_index_positive = 0
tmp_index_neutral  = 0
# shuffle?

def get_facemorph_triple(emotion,target):
    global tmp_index_negative,tmp_index_neutral,tmp_index_positive
    #print indices, emotion, face_index     
    if emotion == 6:
        indices = targets[tmp_index_negative]
        targetpicturename = faces_negative[indices[3]][indices[0]-1]
        goodpicturename = faces_negative[indices[3]][indices[1]-1]
        badpicturename = faces_negative[1-indices[3]][indices[2]-1]
        tmp_index_negative += 1
    elif emotion == 5:
        indices = targets[tmp_index_positive]
        targetpicturename = faces_positive[indices[3]][indices[0]-1]
        goodpicturename = faces_positive[indices[3]][indices[1]-1]
        badpicturename = faces_positive[1-indices[3]][indices[2]-1]
        tmp_index_positive += 1
    elif emotion == 0:
        indices = targets[tmp_index_neutral]
        targetpicturename = faces_neutral[indices[3]][indices[0]-1]
        goodpicturename = faces_neutral[indices[3]][indices[1]-1]
        badpicturename = faces_neutral[1-indices[3]][indices[2]-1]
        tmp_index_neutral += 1

    goodpicturepath = os.path.join(facespath, goodpicturename+".png")
    badpicturepath = os.path.join(facespath, badpicturename+".png")
    targetpicturepath = os.path.join(morphpath, targetpicturename)
    left = random.sample([0,1], 1)[0]
    return (targetpicturepath, goodpicturepath, badpicturepath, left)


# args emotion ... type of trial (describes triplet / duo of possible combinations, e.g. 5 = ['happy', 'neutral', 'surprised']) 
#      target  ... target emotion within the trial [0-7]
def get_facemorph_triple_old(emotion,target):
    # find random eedt triple
    targetperson = random.sample(morphnumbers,1)[0]
    targetemotion =  emotions[target] #random.sample( morphemotions[emotion],1 )[0]
    picture_found = False
    while not picture_found:
        targetpicturename = [pict for pict in morphlist if targetperson in pict if targetemotion in pict]
        if len(targetpicturename) < 1:
            picture_found = False
            #print('target search did not work, for ' + str(targetperson) + ' and ' + str(targetemotion))
            targetperson = random.sample(morphnumbers,1)[0]
            #print('new pair: '+str(targetperson)+' and '+targetemotion)
        else: picture_found = True
    targetpicturename = targetpicturename[0]
    targetpicturepath = os.path.join(morphpath, targetpicturename)

    goodemotion = targetemotion
    goodperson = targetperson
    ####### stability insert:
    didnotwork=0
    while (goodperson == targetperson or didnotwork):
        goodperson = random.sample( peoplenumbers, 1)[0] 
        goodpicturename = [pict for pict in faceslist if goodperson in pict if goodemotion in pict]
        if len(goodpicturename) < 1:
            didnotwork = 1
        else:
            didnotwork = 0
    goodpicturename = goodpicturename[0]
    goodpicturepath = os.path.join(facespath, goodpicturename)

    badpicturepath = []
    while not os.path.isfile(str(badpicturepath)):
        while True:
            if (emotion == 1 or emotion == 4):
                bademotion = random.sample(angry_fearful_emotions, 1)[0]  # TODO: gehoert dann angepasst auf positiv oder negativ
            if (emotion == 2):
                bademotion = 'sad'
            if (emotion == 3):
                #bademotion = 'sad'
                if (targetemotion!='sad'): bademotion = 'sad'
                else: bademotion = random.sample(sad_emotions, 1)[0]
            if (emotion == 5):
                if (targetemotion!='happy'): bademotion = 'happy'
                else: bademotion = random.sample(happy_emotions, 1)[0]
            if (emotion == 6):
               if (targetemotion!='disgusted'): bademotion = 'disgusted'
               else: bademotion = random.sample(sad_emotions, 1)[0]
                 #random.sample(sad_emotions, 1)[0]
            if (emotion == 0) or (emotion == 7):
                bademotion = random.sample(neutral_emotions, 1)[0]

            badperson = random.sample(peoplenumbers,1)[0]
            if bademotion != targetemotion:
                break
        try:
            badpicturename = [pict for pict in faceslist if badperson in pict if bademotion in pict][0]
        except IndexError:
            continue
        badpicturepath = os.path.join(facespath, badpicturename)

    left = random.sample([0,1], 1)[0]
    #print emotion,targetemotion,bademotion
    return (targetpicturepath, goodpicturepath, badpicturepath, left)


corners_pairs = [ [4,5],[4,6],[4,7],[4,8],[5,4],[5,6],[5,7],[5,8],[6,4],[6,5],[6,7],[6,8],[7,4],[7,5],[7,6],[7,8],[8,4],[8,5],[8,6],[8,7] ]
random.shuffle(corners_pairs)
corners_tgt = 0
corners_good = 0
corners_bad = 0
object_sprites = []
object_index = -1
random_objects = False

def get_objectmorph_triple():
    global object_sprites, corners_tgt, corners_good, corners_bad,corners_pairs,object_index

    object_index += 1
    if random_objects == True:
        corners_tgt = random.sample(corners_numbers,1)[0]
        corners_good = corners_tgt
        corners_bad = random.sample(corners_numbers,1)[0]

        while corners_bad == corners_tgt:
            corners_bad = random.sample(corners_numbers,1)[0]
    else:
        corners_tgt = corners_pairs[object_index%len(corners_pairs)][0]
        corners_good = corners_pairs[object_index%len(corners_pairs)][0]
        corners_bad = corners_pairs[object_index%len(corners_pairs)][1]   

    # define target image
    # 1. animated, 2. static
    object_sprites = []
    frames = 70.0
    if morph == 0:
        object_sprites.append(AnimatedObject(float(ttrial/frames),70.0,corners_tgt, False, True))
    elif morph == 1:
        if nonlinearobjects_offset == 0:
            object_sprites.append(AnimatedObject(float(ttrial/frames),70.0, corners_tgt, True, False))
        else:
            object_sprites.append(AnimatedObject(float(ttrial/frames),70.0, corners_tgt, True, True))    
    else:
        print('Exception occured, invalid state of morph flag')
        sys.exit(1)

    # define probe images
    object_sprites.append(AnimatedObject(0.1, 1, corners_good, False, False))
    object_sprites.append(AnimatedObject(0.1, 1, corners_bad, False, False))
    targetpicturepath = 'quirl_alpha.png'
    goodpicturepath = targetpicturepath
    badpicturepath = targetpicturepath
    left = random.sample([0,1], 1)[0]
    return(targetpicturepath, goodpicturepath, badpicturepath, left)

def get_triple(i):
    global trial_type_list, index_trial, faces_type_list, face_index_trial, sprite_face, sprite_face_list
    print('Index trial: ' + str(index_trial))
    #[a,b,c,d] = None
    if i==3: # 3: moprhing faces and objects
        #facemorph = random.sample([0,1], 1)[0]
        facemorph = trial_type_list[index_trial]
        if facemorph < 8:
            #[a,b,c,d] = get_facemorph_triple(trial_type_list[index_trial])
            [a, b, c, d] = face_paths[face_index_trial]
            [x,y,z] = [a,b,c]
            stim = 'morph_face'
            if load_in_blocks == True:
                sprite_face = sprite_face_list[face_index_trial % notrials]
            else:
                sprite_face = sprite_face_list[face_index_trial]
            sprite_face.restart()
            face_index_trial += 1
        else:
            [a,b,c,d] = get_objectmorph_triple()
            [x,y,z] = [str(corners_tgt), str(corners_good), str(corners_bad)]
            stim = 'morph_object'
        index_trial = index_trial + 1

    logger.debug('new_triple_'+stim+';%s;%s;%s;%s',x,y,z,'L' if d == 1 else 'R')
    return [a,b,c,d]


def display_triple(targetpicturepath, goodpicturepath, badpicturepath, left):
    global sprite_face, object_sprites, is_object
    target = None
    if os.path.isdir (targetpicturepath):
        # face morph - then we will animate
        target = sprite_face.image
        good = pygame.image.load(goodpicturepath)
        bad = pygame.image.load(badpicturepath)
        is_object = False
    else:
        # object morph
        is_object = True 
        if targetpicturepath == goodpicturepath and goodpicturepath == badpicturepath:
            target = object_sprites[0].image
            good = object_sprites[1].image
            bad = object_sprites[2].image
        else:
            target = pygame.image.load(targetpicturepath)
            good = pygame.image.load(goodpicturepath)
            bad = pygame.image.load(badpicturepath)

    # heighttowidth = double(target.get_size()[1]) / double(target.get_size()[0])   # for python 2
    heighttowidth = float(target.get_size()[1]) / float(target.get_size()[0])   # for python 3

    # 1- set target height
    if is_object:
        picsheight = int(height*0.58)
    else:
        picsheight = int(height*0.7)

    picswidth = int(picsheight/heighttowidth)

    target = pygame.transform.smoothscale(target, (picswidth, picsheight))

    # 2- set probe pic height
    heighttowidth = float(good.get_size()[1]) / float(good.get_size()[0])  # in case lower pictures have different dimensions
    if is_object:
        picsheight = int(height*0.58)
    else:
        picsheight = int(height*0.7)

    picswidth = int(picsheight/heighttowidth)

    good = pygame.transform.smoothscale(good, (picswidth, picsheight))
    bad = pygame.transform.smoothscale(bad, (picswidth, picsheight))

    target_rect = target.get_rect()
    good_rect = good.get_rect()
    bad_rect = bad.get_rect()
    target_rect.x = width/2 - target_rect.width/2
    target_rect.y = height/4 - target_rect.height/2
    good_rect.y = bad_rect.y = height*3/4 - good_rect.height/2 - 20
    if left:
        good_rect.x = width/4 - good_rect.width/2
        bad_rect.x = width*3/4 - bad_rect.width/2
    else:
        bad_rect.x = width/4 - bad_rect.width/2
        good_rect.x = width*3/4 - good_rect.width/2
    screen.fill(BG_COLOR)
    screen.blit(target, target_rect)
    screen.blit(good, good_rect)
    screen.blit(bad, bad_rect)
    pygame.display.flip()


def loading_bar (percentage, width):
    progress = int (percentage * width / 100.0 )
    x = '='
    y = ' '
    result = '[' + str( progress * x) + str( (width - progress) *y ) + '] ' + str(percentage) +"%"
    return result

####################################################
########### START OF PARADIGM ######################
####################################################
print('ATTENTION: THIS SCRIPT USES CONTEMPTUOUS NEUTRAL FACES')

start_screen()
trigger = 0
current_block = 0
trigger_time = 0

target_faces_type_list = []
face_paths = []
target_faces_type_list = [i for i in target_emotion_list if i < 8]  # get only faces from list e.g. [1 1 1 1 1 6 6 6 6 6 4 4 4 4 4 ]
faces_type_list = [i for i in trial_type_list if i < 8]  # get only faces from list e.g. [1 1 1 1 1 6 6 6 6 6 4 4 4 4 4 ]

print("facetypelist",faces_type_list)
print("targetfacelist",target_faces_type_list)

for i in range(0,len(faces_type_list)) :
    face_paths.append(get_facemorph_triple(faces_type_list[i],target_faces_type_list[i]))

sprite_face_list = []
framerate_inv =  float(ttrial/30.0)

ta = time.time()
if args.testmode=='test':
    faces_type_list = [ 5,2,2,4,5 ]


####################################################################
## ONLY DO THAT IF ENOUGH RAM IS AVAILABLE > 1GB !!
## It is usually a bad idea for many blocks ( > 10 ) and with many trials (>8)
## For the static condition it should be fine (-t static option)
####################################################################
if load_in_blocks == False:
    for i in range(0, len(faces_type_list)):
        tmp_as = AnimatedSprite(face_paths[i][0], framerate_inv, bool(morph))
        sprite_face_list.append(tmp_as)
        print(loading_bar(int(float((i + 1) / float(len(faces_type_list))) * 100), 50), "           \r", end=' ')
    print("")
    loaded_old = 0
    print("Loading of faces into memory...")
    while True:
        testlist = []
        for i in range(0, len(faces_type_list)):
            testlist.append(sprite_face_list[i].get_loaded())
        loaded = sum(testlist) / float(len(testlist)) * 100
        if loaded == 0 or loaded > loaded_old:
            print(loading_bar(int(loaded), 50), "           \r", end=' ')
            loaded_old = loaded
            gc.collect()
        if all(loading == 1.0 for loading in testlist):
            break
    te = time.time()
    print("")
    print("Loading of faces into memory [OK] (", '{:0.2f}'.format(te - ta), "s )")
####################################################################

print("Waiting for scanner trigger...")
while trigger == 0:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                trigger = 1
                logger.debug('trigger')
                trigger_time = time.time()

#blocks = [3] * len(matrix) * 2
blocks = [3] * len(matrix)

for i in blocks:
        # wait baseline duration
        show_cross()

        if load_in_blocks == True:
            print("Current index", trial_type_list[index_trial])
            # at baseline, load the images for each block into memory for immediate presentation without lag
            sprite_face_list = [None] * notrials
            if (trial_type_list[index_trial] < 8):
                for i in range(face_index_trial,face_index_trial + notrials) :
                    # i is index of trial_type_lis
                    tmp_as = AnimatedSprite(face_paths[i][0],framerate_inv, bool(morph))
                    sprite_face_list[i  % notrials] = tmp_as
                    #print "Loading %s" % str(face_paths[i][0])

        # waiting in baseline
        pygame.time.delay(baseline_time*1000)

        block_type = 'morph_faces_and_objects'
        logger.debug('starting_block_%s', block_type)

        # setting timers and init first triple of block
        go = 1
        key_pressed = 0
        t0 = time.time()
        remaining_time = block_duration_morphing
        facetimer = time.time()
        index_trials_blocks = 0
        [a, b, c, d] = get_triple(3) # first triple

        while go:
            t1 = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN and (t1-t0)>0.5: # (ignore presses during baseline)
                    if event.key == pygame.K_9:
                        go = 0
                    #
                    # Response of the subject
                    if event.key == pygame.K_b or event.key == pygame.K_y:
                        #if key_pressed == 0:
                        if (t1 - facetimer) > 0.2:
                            if (block_type == 'morph_obj'):
                                object_index += 1
                                if event.key == pygame.K_b:
                                    logger.debug('key_1_pressed;%d;%d;%d;;4;%s',corners_tgt,corners_bad,corners_good,'correct' if d == 0 else 'wrong')
                                if event.key == pygame.K_y:
                                    logger.debug('key_4_pressed;%d;%d;%d;;1;%s', corners_tgt, corners_bad, corners_good,'correct' if d == 1 else 'wrong')
                            else:
                                if event.key == pygame.K_b:
                                    logger.debug('key_1_pressed;%s;%s;%s;;4;%s',str(a),str(b),str(c),'correct' if d == 1 else 'wrong')
                                if  event.key == pygame.K_y:
                                    logger.debug('key_4_pressed;%s;%s;%s;;1;%s', str(a), str(b), str(c),'correct' if d == 0 else 'wrong')

                            key_pressed = 1

            #
            # Time of the trial is up
            if (t1 - facetimer) > ttrial:
                index_trials_blocks += 1
                if key_pressed == 0:
                    if (block_type == 'morph_obj'):
                        logger.debug('no_key_pressed;%d;%d;%d;;%s', corners_tgt, corners_bad, corners_good,
                                     'no_key_pressed')          
                    else:
                        logger.debug('no_key_pressed;%s;%s;%s;;%s', str(a), str(b), str(c), 'no_key_pressed')

                if (t1-t0) > block_duration_morphing:
                    print((str(block_duration_morphing)+'s up'))
                    go = 0
                    index_trial = sum(num_trials_blocks[:current_block+1])
                    logger.debug('time_up;%d;%d;%d;;%s',corners_tgt,corners_bad,corners_good,'time_up')
                    break

                if index_trials_blocks == num_trials_blocks[current_block]:
                    print('all trials of the block completed')
                    go = 0
                    logger.debug('block_completed;%d;%d;%d;;%s', corners_tgt, corners_bad, corners_good, 'block_completed')
                    break

                [a, b, c, d] = get_triple(3)
                facetimer = time.time()
                key_pressed = 0

                if (t1-t0) > block_duration_morphing:
                    go = 0
            
            display_triple(a, b, c, d)

        logger.debug('finished_block_%s', block_type)
        remaining_time = remaining_time - (t1 - t0)
        print('Remaining time: ' + str(remaining_time))
        #if (remaining_time > 0):
        #    pygame.time.wait(int(remaining_time * 1000))
        current_block += 1

# wait baseline duration
show_cross()
pygame.time.delay(baseline_time*2600)


end_time = time.time()
duration_task = end_time - trigger_time
print(str('Duration of the task:'+(str(int(duration_task)))))
logger.debug('task_duration;'+str(int(duration_task)))
logger.debug('end_of_task')
pygame.time.wait(500)
pygame.quit()
