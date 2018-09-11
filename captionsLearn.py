#!/home/geoff/miniconda3/bin/python
from moviepy.editor import VideoFileClip
from moviepy.tools import cvsecs
import re, pygame, time

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

def cleanSubs(es, eng):
    """get rid of non-dialogue subs"""
    #get rid of all cap english subtitles
    ex=[]
    for i,v in enumerate(eng):
        if v[1].isupper():
            ex.append(i)     

    eng = [x for i,x in enumerate(eng) if i not in ex]

    #get rid of sound/noise spanish subtitles

    paren = re.compile('\\([a-zA-z\\s]+\\)') #find text in parentheses
    rem=[]
    for i,v in enumerate(es):
        m = paren.match(v[1])
        #if len(match) is same len(string), then it's a noise/sound sub
        if  m and len(m.group()) == len(v[1]):
            rem.append(i)

    es = [x for i,x in enumerate(es) if i not in rem]
    return es, eng 

def sync(esSubs, engSubs):
    """sync timestamps of both translations""" 

    #find the file with least entries
    less  = min( (len(engSubs), engSubs), (len(esSubs), esSubs), key = lambda x: x[0] )[1]
    more = max( (len(engSubs), engSubs), (len(esSubs), esSubs), key = lambda x: x[0] )[1]

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
                    #if z ==70: import pdb; pdb.set_trace()
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
    
if __name__ == "__main__":
    video = VideoFileClip(/path/to/video)
    sub1=file_to_subtitles(/path/to/sub1) 
    sub2= file_to_subtitles(/path/to/sub2)
    sub1, sub2= cleanSubs(sub1, sub2)
    master = sync(sub1, sub2)

    #user sees clips with subtitles
    print(30*'-','\n')
    for _ in range(len(master)): 
        a,b = master[_][0]
        engSub = master[_][1]
        esSub = master[_][2]

        clip = video.subclip(a,b)
        clip.preview()
        pygame.quit()

        #boundary(UI)
        #want to replay clip?
        check = ''
        print("\nTimestamp: [{0},{1}]".format(a,b),'\n')
        while check not in ['yes','y']:
            replay = input('Replay Clip? ').lower()
            if replay in ['yes','y']:
                clip.preview()
                pygame.quit()
            else:
                check = 'yes' 
        #user inputs translations
        esT = input("What did they say in spanish? ")
        enT = input("What did they say in english? ")
        print("\nSpanish Translation:\n\n", esSub,'\n')
        print("\nEnglish Translation:\n\n", engSub,'\n')
        print(30*'-','\n')
        time.sleep(4)

#add a way to watch whole video
#log accuracy
#give a save/quit option
#remove css <> tags from subs
#easy way to select video and subtitle files
