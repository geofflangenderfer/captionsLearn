from moviepy.editor import VideoFileClip
from moviepy.tools import cvsecs
import pygame

import re, time, sys, logging

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import smtplib, os
from email.message import EmailMessage
import datetime

import codecs

def findEncoding(filename):
    """goes through encodings to find one that will decode filename. Goes
       with first one that works"""

    encodings = [ 'utf-8', 'latin-1', 'windows-1250', 'windows-1252', 'ascii' ]

    for e in encodings: 
        try:
            lines = codecs.open(filename, 'r', encoding= e)
            lines.readlines()
            lines.seek(0)
            break 
        except UnicodeDecodeError:
            print('got unicode error with %s , trying different encoding' % e)
    return e

def file_to_subtitles(filename):
    """ Coonverts a srt file into subtitles.

    The returned list is of the form ``[((ta,tb),'some text'),...]``
    and can be fed to SubtitlesClip.

    Only works for '.srt' format for the moment.
    """

    enc = findEncoding(filename)
    with open(filename, encoding = enc) as f:
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
    paren = re.compile('\([\w\s,.-]+\\)') #find text in parenthss
    for i,v in enumerate(s):
        m = paren.match(v[1])
        #get rid of all cap subs
        if v[1].isupper():
            ex.append(i)     
        #whole sub is in (), which are usually sound/noise subs
        elif  m and len(m.group()) == len(v[1]):
            ex.append(i)

        #2 lines of parentheses
         #- (Sighs)
         #- (Laughing) 

        #empty cells
        elif len(v[1]) == 0:
            ex.append(i)
        #cell is None
        elif v[1] == None:
            ex.append(i)
    s = [x for i,x in enumerate(s) if i not in ex]
    return s 

def sync(s1, s2):

    thresh = lambda a,b: abs( (a[0]-b[0]) ) + abs( (a[1] - b[1]) )

    subs = [s1, s2]
    less, more = sorted(subs, key = lambda x: len(x))

    def minDiff(r):
        """compute diff between tsB and tsE for r and every entry in other subFile.
           Add these diffs up and return the index with the smallest value"""

        diffsB = [ ( i, thresh( r[0], y[0] ) ) for i,y in enumerate(more) ]
        diffsB.sort( key = lambda r: r[1] )
        minDiff = diffsB[0]
        return minDiff

    master = []
    for i, x in enumerate(less):

        #more[index] is best fit for x
        index = minDiff(x)[0]

        #build entry
        tsB = min( less[i][0][0], more[index][0][0] ) 
        master.append( ([tsB, x[0][1]], x[1], more[index][1]) )

    return master

def toFile(s, path1= None, path2 = None):
    """Save subtitles to file"""
    if path1 == None: path1 = 'sub1.txt'
    if path2 == None: path2 = 'sub2.txt'

    if len(s[0]) == 3: 
        with open(path1, "w") as f:
            for i, item in enumerate(s):
                f.write( '{}\n'.format(i) )
                f.write( "{}\n".format(item[0]) )
                f.write( "{}\n\n".format(item[1]) )

        with open(path2,"w") as f:
            for i, item in enumerate(s):
                f.write( '{}\n'.format(i) )
                f.write( "{}\n".format(item[0]) )
                f.write( "{}\n\n".format(item[2]) )

    elif len(s[0]) == 2:
        with open(path1, "w") as f:
            for i, item in enumerate(s):
                f.write( '{}\n'.format(i) )
                f.write( "{}\n".format(item[0]) )
                f.write( "{}\n\n".format(item[1]) )

    else:
        print("Don't recognize structure of the file called by toFile")

def syncAccuracy(s1, s2, m):
    """comprobar la calidad de la sincronizacion de subtitulos"""
    subs = [s1, s2]
    less, more = sorted(subs, key = lambda x: len(x))
    if len(less) != len(m):
        print("There was a problem syncing the subtitles. Email both .srt files to geoffro2888@gmail.com for support")
        sys.exit(0)

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
        print("try going to https://myaccount.google.com/lesssecureapps and \
              turning less secure apps on. This allows the program to send emails through your gmail account")
        print("email geoffro2888@gmail.com if that doesn't work")
        raise
    mailServer.send_message(msg)
    mailServer.quit()
    print("mail sent")

def quickCheckSubs(s1, s2, s3):
    print( 'len(s1)', len(s1), 
           'len(s2)', len(s2), 
           'len(s3)', len(s3) )   

if __name__ == "__main__":
    print(30*'-','\n')

    #prompt for files 
    print("Welcome to captionsLearn. You will be shown clips with dialogue, then you will be asked to provide translations in both languages")
    Tk().withdraw()
    print("what video file do you want to use?")
    vidFile = askopenfilename()
    print("what's the first subtitle file to use?")
    sub1File = askopenfilename()
    print("what's the second subtitle file to use?")
    sub2File = askopenfilename()
    

    video = VideoFileClip(vidFile)
    sub1 = cleanSubs( file_to_subtitles(sub1File) )
    sub2 = cleanSubs( file_to_subtitles(sub2File) )
    master = sync(sub1, sub2)
    syncAccuracy( sub1, sub2, master)

    #setup logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(filename)s:%(message)s')
    file_handler = logging.FileHandler('data.log') 
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

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
        
        #log to data.log
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

        print(30*'-','\n')
