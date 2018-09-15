#!/home/geoff/miniconda3/bin/python
from moviepy.editor import VideoFileClip
from moviepy.tools import cvsecs
import pygame

import re, time, sys, logging

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import smtplib, os
from email.message import EmailMessage
import datetime

def file_to_subtitles(filename):
    """ Converts a srt file into subtitles.

    The returned list is of the form ``[((ta,tb),'some text'),...]``
    and can be fed to SubtitlesClip.

    Only works for '.srt' format for the moment.
    """

    with open(filename,'r') as f:
        lines = f.readlines()

    times_texts = []
    current_times , current_text = None, ""

    for line in lines:
        times = re.findall("([0-9]*:[0-9]*:[0-9]*,[0-9]*)", line)
        if times != []:
            current_times = list(map(cvsecs, times))
        elif line.strip() == '': 
            times_texts.append((current_times, current_text.strip('\n')))
            current_times, current_text = None, ""
        elif current_times is not None:
            current_text = current_text + line
    return times_texts

def cleanSubs(s):
    """get rid of non-dialogue subs"""
    ex=[]
    paren = re.compile('\\([a-zA-z\\s]+\\)') #find text in parenthss
    for i,v in enumerate(s):
        m = paren.match(v[1])
        #get rid of all cap subs
        if v[1].isupper():
            ex.append(i)     
        #whole sub is in (), which are usually sound/noise subs
        elif  m and len(m.group()) == len(v[1]):
            ex.append(i)
        #empty cells
        elif len(v[1]) == 0:
            ex.append(i)
    s = [x for i,x in enumerate(s) if i not in ex]
    return s 

def sync(s1, s2):
    """sync timestamps of both translations""" 
    #the order of s1, s2 affects the returned value. Why?

    #find the file with least entries
    less  = min( (len(s2), s2), (len(s1), s1), key = lambda x: x[0] )[1]
    more = max( (len(s2), s2), (len(s1), s1), key = lambda x: x[0] )[1]

    # x is abso% from y 
    abso = lambda x,y: abs( (x-y)/y )

    master = []
    i =0 
    for x in less:
        while i < len(more):
            y = more[i]
            #check beg, end ts
            xB=x[0][0]; xE=x[0][1]
            yB=y[0][0]; yE=y[0][1]

            if abs( (xB-yB) ) < .5 and abs( (xE-yE) ) < .5: 
                master.append( (x[0], x[1], y[1]) )
                i+=1
                break

            #merge subs to make a match
            elif abs( (xB-yB) ) < .5 and abs( (xE-yE) ) > .5:    
                z = i
                while  abs( (xE-yE) ) > .5:
                    y = more[z]; yE = y[0][1]
                    z+=1
                entry = ( x[0],  x[1],  "\n".join(x[1] for x in more[i:z+1]) )
                master.append(entry)
                i = z
                break
            else:
                i+=1
    return master

def toFile(s, dest = None):
    if len(s[0]) == 3: 
        with open("cEngS1E04.txt", "w") as f:
            for i, item in enumerate(s):
                f.write( '{}\n'.format(i) )
                f.write( "{}\n".format(item[0]) )
                f.write( "{}\n\n".format(item[1]) )

        with open("cEsS1E04.txt","w") as f:
            for i, item in enumerate(s):
                f.write( '{}\n'.format(i) )
                f.write( "{}\n".format(item[0]) )
                f.write( "{}\n\n".format(item[2]) )

    elif len(s[0]) == 2:
        with open(dest, "w") as f:
            for i, item in enumerate(s):
                f.write( '{}\n'.format(i) )
                f.write( "{}\n".format(item[0]) )
                f.write( "{}\n\n".format(item[1]) )

    else:
        print("Don't recognize structure of {}".format(f))

def syncAccuracy(s1, s2, m):
    """check the quality of the subtitle sync"""
    pass

def sendLogs():

    #you need to turn on access for less secure apps to do this. 
    #https://myaccount.google.com/lesssecureapps
                

    #pull mail client login info or create file
    try:
        with open('credentials.txt') as f:
            email, username, password = f.readlines()
           
        email= email.strip('\n')
        username = username.strip('\n')
        password = password.strip('\n')
            
    except:
        print("reading from credentials.txt didn't work, so we will create it from scratch", sys.exc_info()[0])
        print("\nYour email is used to send log files, which include: time to complete a clip, translations, and answers")
        email = raw_input("whats your email address? ")
        username = raw_input("what's your username? ")
        password = raw_input("what's your password? ")

        with open('credentials.txt', 'w') as f:
            f.write(email+'\n')
            f.write(username+'\n')
            f.write(password+'\n')

    #determine mail server
    gmailRe= re.compile('@gmail.com')
    outlookRe = re.compile('@outlook.com')

    if gmailRe.search(email): SERVER, PORT = 'smtp.gmail.com',587
    elif outlookRe.search(email): SERVER, PORT = 'smtp-mail.outlook.com',587 
    else:
        print("Don't recognize your email. Email the error message and the data.log file to geoffro2888@gmail.com for help")

    USER = username
    PW = password 
    FROM = email
    TO = 'geoffro2888@gmail.com'

    #grab log message from file and wipe 
    path = os.getcwd() + '/data.log'
    with open(path, 'r') as f:
        msg = EmailMessage()
        msg.set_content(f.read())
    msg['Subject'] = "captionsLearn: User-{} : Date-{}".format( os.getcwd(), datetime.datetime.today().strftime('%Y-%m-%d') )
    msg['From'] = FROM 
    msg['To'] = TO 
    open(path, 'w').close()



    mailServer = smtplib.SMTP(SERVER, PORT)
    mailServer.ehlo()
    mailServer.starttls()

    #email login
    try:
        mailServer.login(USER, PW)
    except SMTPAuthenticationError:
        print("try going to https://myaccount.google.com/lesssecureapps and turning less secure apps on. This allows the program to send emails through your gmail account")
        print("email geoffro2888@gmail.com if that doesn't work")
        raise
    mailServer.send_message(msg)
    mailServer.quit()
    print("mail sent")

if __name__ == "__main__":
    print(30*'-','\n')
    #print("Welcome to captionsLearn. You will be shown clips with dialogue, then you will be asked to provide translations in both languages")
    #Tk().withdraw()
    #print("what video file do you want to use?")
    #vidFile = askopenfilename()
    #print("what's the first subtitle file to use?")
    #sub1File = askopenfilename()
    #print("what's the second subtitle file to use?")
    #sub2File = askopenfilename()
    vidFile = '/home/geoff/captionsLearn/lcdp/S01/La.Casa.de.Papel.S01E04.720p.NF.WEB-DL.x265-HETeam.mkv'
    sub2File = '/home/geoff/captionsLearn/engLcdpSubtitles/Money.Heist.S01E04.XviD-AFG.srt'
    sub1File = '/home/geoff/captionsLearn/esLcdpSubtitles/La.casa.de.papel.S01E04.WEBRip.Netflix.srt'
    video = VideoFileClip(vidFile)
    sub1, sub2 =cleanSubs( file_to_subtitles(sub1File) ), cleanSubs( file_to_subtitles(sub2File) )
    master = sync(sub1, sub2)
    
    #setup logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(filename)s:%(message)s')
    file_handler = logging.FileHandler('data.log') 
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    #logging.basicConfig(filename = 'data.log', level = logging.DEBUG, format = '%(asctime)s:%(levelname)s:%(message)s')
    #initialize data.log
    logger.info(30*'-'+'(start session)'+30*'-')
    logger.info("video file:{}".format(vidFile))
    logger.info("sub1 file:{}".format(sub1File))
    logger.info("sub2 file:{}\n".format(sub2File))

    #user sees clips with subtitles
    for _ in range(len(master)): 
        start = time.time()
        a,b = master[_][0]
        engSub = master[_][1]
        esSub = master[_][2]

        clip = video.subclip(a,b)
        clip.preview()
        pygame.quit()

        #want to replay clip?
        check = ''
        i=1
        print("\nTimestamp: [{0},{1}]".format(a,b),'\n')
        while check not in ['yes','y']:
            replay = input('Replay Clip? ').lower()
            if replay in ['yes','y']:
                i+=1
                clip.preview()
                pygame.quit()
            else:
                check = 'yes' 
        #user inputs translations
        esT = input("What did they say in spanish? ")
        enT = input("What did they say in english? ")
        
        #time spent on each clip
        end = time.time() - start

        logger.info("clip Timestamp:[{0},{1}]".format(a,b))
        logger.info("Time spent on clip:{0:.2f}s".format(end))
        logger.info("replay clip {} times".format(i))
        logger.info("spanish translation:{} ".format(esT))
        logger.info("spanish translation (ans):{} ".format(esSub))
        logger.info("english translation:{} ".format(enT))
        logger.info("english translation (ans):{}\n ".format(engSub))
        
        print("\nSpanish Translation:\n\n", esSub,'\n')
        print("\nEnglish Translation:\n\n", engSub,'\n')
        
        check3=''
        while check3 not in ['yes','y']:
            wait= input('Continue learning? ').lower()
            if wait in ['yes','y','']:
                break
            else:
                print("Ok, come back soon!")
                sendLogs()
                sys.exit(0)
        #check whether user wants to review answer before moving on
        #check2=''
        #while check2 not in ['yes','y']:
        #    wait= input('Continue? ').lower()
        #    if wait in ['yes','y']:
        #        check2 = 'yes' 
        #    else:
        #        time.sleep(4)

        print(30*'-','\n')
