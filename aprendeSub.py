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
    """ convierte un .srt archivo en subtitulos

    la lista devuelta es de la forma ``[((ta,tb),'some text'),...]``
    y puede alimentar a SubtitleClip

    solo funciona para el formato .srt por el momento
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
    """eliminar subtitulos sin dialogo"""
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
    """coordinar timestamps para ambas traducciones""" 
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
        print("No reconoce la forma de {}".format(f))

def syncAccuracy(s1, s2, m):
    """comprobar la calidad de la sincronizacion de subtitulos"""
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
        print("Intenta ir a https://myaccount.google.com/lesssecureapps y convirtiendo 'less secure apps' a 'on'. Esto permite la programa para enviar correos electronicos desde tu cuenta de gmail.")
        print("Envia un mensaje a geoffro2888@gmail.com si lo no funciona")
        raise
    mailServer.send_message(msg)
    mailServer.quit()
    print("correo enviado")

if __name__ == "__main__":
    print(30*'-','\n')
    #print("Bienvenido a aprendeSub. Se te mostrara clips con dialogo, despues te pedira a dar traducciones en ambos linguajes")
    #Tk().withdraw()
    #print("Que archivo de video quieres usar?")
    #vidFile = askopenfilename()
    #print("Que es el primero archivo de subtitulo para usar?")
    #sub1File = askopenfilename()
    #print("Que es el segundo archivo de subtitulos para usar?")
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
            replay = input('Replica la Clip? ').lower()
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
        
        check3=''
        while check3 not in ['si','s']:
            wait= input('Continua aprendiendo? ').lower()
            if wait in ['si','s','']:
                break
            else:
                print("Listo, regresa pronto!")
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
