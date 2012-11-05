from mmd0tools.mmd0 import Buffer, MMD0
from mmd0tools.ir import IRSong

def load(filename):
    b = None
    with open(filename, 'r') as f:
        b = Buffer(f)
    return MMD0(b)


def dump(args):
    m = load(args[1])
    m.dump()


def convert(args):
    m = load(args[1])
    ir_song = IRSong(m)
    ir_song.to_ir_events()
    #ir_song.dump()

    print """
<CsoundSynthesizer>
<CsOptions>
-odac
</CsOptions>
<CsInstruments>
sr = 44100
ksmps = 32
nchnls = 1
0dbfs = 1

instr 1
iFreq     = cpspch(p4)

aEnv      line     1, p3, 0
aSig      oscils   0dbfs/4, iFreq, 0
          out      aSig * aEnv

endin

</CsInstruments>
<CsScore>
"""
    for e in ir_song.ir_track[2]:
        if e.instr == 1:
            print "i %d %.2f %.2f %.2f" % (e.instr,
              (e.start - 96) * 0.10, (e.dur) * 0.10, e.pitch)
    print """
</CsScore>
</CsoundSynthesizer>
"""

def samples(args):
    m = load(args[1])
    for byte in m.smplarr[0].data:
        # upsample to 16-bit for aplay's benefit
        # usage: mmd0.py your.med | aplay --rate=8287 --format=S16_BE
        sys.stdout.write(chr(byte))
        sys.stdout.write(chr(0))
