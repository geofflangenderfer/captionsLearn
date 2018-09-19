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
    """ convierte un .srt archivo en subtitulos

    la lista devuelta es de la forma ``[((ta,tb),'some text'),...]``
    y puede alimentar a SubtitleClip

    solo funciona para el formato .srt por el momento
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
    """eliminar subtitulos sin dialogo"""
    ex=[]
    paren = re.compile('\([\w\s,.-]+\)') #find text in parenthss
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
        print("No reconoce la forma del archivo de toFile")

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
        print("leer desde credentials.txt no funciono, entonces vamos a hacerlo de nuevo ", sys.exc_info()[0])
        print("\nTu correo electronico es usado para enviar archivos de registro, que incluye: tiempo para terminar un clip, traducciones, y respuestas ")
        email = raw_input("Que es tu correo electronico? ")
        username = raw_input("Que es tu usuario? ")
        password = raw_input("Que es tu contrasena? ")

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
        print("No reconoce tu correo electronico. Envia la mensaje de error y la data.log archivo a geoffro2888@gmail.com para ayuda")

    USER = username
    PW = password 
    FROM = email
    TO = 'geoffro2888@gmail.com'

    #grab log message from file and wipe 
    path = os.getcwd() + '/data.log'
    with open(path, 'r') as f:
        msg = EmailMessage()
        msg.set_content(f.read())
    msg['Subject'] = "captionsLearn: User-{} : Date-{}".format( 
            os.getcwd(), datetime.datetime.today().strftime('%Y-%m-%d') )
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
        print("Intenta ir a https://myaccount.google.com/lesssecureapps y convirtiendo 'less secure apps' a 'on'. Esto permite la programa para enviar correos electronicos desde tu cuenta de gmail.")
        print("Envia un mensaje a geoffro2888@gmail.com si lo no funciona")
        raise
    mailServer.send_message(msg)
    mailServer.quit()
    print("correo enviado")

def quickCheckSubs(s1, s2, s3):
    print( 'len(s1)', len(s1), 
           'len(s2)', len(s2), 
           'len(s3)', len(s3) )   

if __name__ == "__main__":
    print(30*'-','\n')

    #pedir por los archivos
    print("Bienvenido a aprendeSub. Se te mostrara clips con dialogo, despues te pedira a dar traducciones en ambos linguajes")
    Tk().withdraw()
    print("Que archivo de video quieres usar?")
    vidFile = askopenfilename()
    print("Que es el primero archivo de subtitulo para usar?")
    sub1File = askopenfilename()
    print("Que es el segundo archivo de subtitulos para usar?")
    sub2File = askopenfilename()

    
    video = VideoFileClip(vidFile)
    sub1 = cleanSubs( file_to_subtitles(sub1File) )
    sub2 = cleanSubs( file_to_subtitles(sub2File) )
    master = sync(sub1, sub2)
    syncAccuracy( sub1, sub2, master)

    #Empezar logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(filename)s:%(message)s')
    file_handler = logging.FileHandler('data.log') 
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(30*'-'+'(start session)'+30*'-')
    logger.info("version:{}".format(os.getcwd()))
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
        print("\nMarca de tiempo: [{0},{1}]".format(a,b),'\n')
        while check not in ['si','s']:
            replay = input('Repite la Clip? ').lower()
            if replay in ['si','s']:
                i+=1
                clip.preview()
                pygame.quit()
            else:
                check = 'si' 
        #user inputs translations
        esT = input("Que ellos dijeron en espanol? ")
        enT = input("Que ellos dijeron en ingles? ")
        
        #time spent on each clip
        end = time.time() - start

        logger.info("clip Timestamp:[{0},{1}]".format(a,b))
        logger.info("Time spent on clip:{0:.2f}s".format(end))
        logger.info("replay clip {} times".format(i))
        logger.info("spanish translation:{} ".format(esT))
        logger.info("spanish translation (ans):{} ".format(esSub))
        logger.info("english translation:{} ".format(enT))
        logger.info("english translation (ans):{}\n ".format(engSub))
        
        print("\nTraduccion Espanol:\n\n", esSub,'\n')
        print("\nTraduccion Ingles:\n\n", engSub,'\n')
        
        #check whether or not to quit
        check3=''
        while check3 not in ['si','s']:
            wait= input('Continua aprendiendo? ').lower()
            if wait in ['si','s','']:
                break
            else:
                print("Listo, regresa pronto!")
                sendLogs()
                sys.exit(0)

        print(30*'-','\n')
