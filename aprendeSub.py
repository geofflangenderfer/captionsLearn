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

if __name__ == "__main__":
    video = VideoFileClip("/home/geoff/Downloads/lcdp/S01/La.Casa.de.Papel.S01E04.720p.NF.WEB-DL.x265-HETeam.mkv")
    esSubs = file_to_subtitles('/home/geoff/Downloads/esLcdpSubtitles/La.casa.de.papel.S01E04.WEBRip.Netflix.srt')
    engSubs = file_to_subtitles('/home/geoff/Downloads/engLcdpSubtitles/Money.Heist.S01E04.XviD-AFG.srt')
    #user sees xs clip
    for _ in range(len(esSubs)): 
        a,b = esSubs[_][0]
        esSub = esSubs[_][1]
        engSub = engSubs[_][1]

        clip = video.subclip(a,b)
        clip.preview()
        pygame.quit()

        #want to replay clip?
        check = ''
        while check not in ['si','s']:
            replay = input('Replica la clip?').lower()
            if replay in ['si','s']:
                clip.preview()
                pygame.quit()
            else:
                check = 'si' 
        #user inputs translations
        esT = input("Que les dijeron en espanol? ")
        enT = input("Que les dijeron en ingles? ")
        print("\nTradduccion Espanol\n\n", esSub,'\n')
        print("\nTradducion Ingles\n\n", engSub,'\n')
        time.sleep(4)

#add english translation
#log accuracy
#give a save/quit option
#suppress warning: ALSA lib pcm.c:8306:(snd_pcm_recover) underrun occurred
#skip over subtitles without dialogue
#remove css <> tags
