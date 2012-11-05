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

    # dump all instruments to files
    i = 1
    for smplarr in m.smplarr:
        with open("instrument%d.raw" % i, 'w') as f:
            for byte in smplarr.data:
                f.write(chr(byte))
                # upsampled to 16-bit for aplay's benefit
                # usage: aplay instrument1.raw --rate=8287 --format=S16_BE
                # f.write(chr(0))
        i += 1

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
0dbfs = 1"""
    i = 1
    for smplarr in m.smplarr:
        sample = m.song.sample[i-1]
        # XXX going to need to be cleverer than this
        kloopstart = sample.replen / 8287.0
        kloopend = (sample.rep + sample.replen) / 8287.0
        kloopstart = 0.0
        kloopend = 2.0
        # 0.1879138321995465 = 44100 / 8287
        print """
instr %d
aSig      flooper2 0.25,                         /* kamp */ \ 
                   (cpspch(p4) / cpspch(1.00)) * 0.1879138321995465, /* kpitch */ \ 
                   %.8f,                           /* kloopstart */ \ 
                   %.8f,                           /* kloopend */ \ 
                   0,                            /* kcrossfade */ \ 
                   %d,                           /* ifn */ \ 
                   0, 0, 0, 0
          out      aSig

endin
""" % (i, kloopstart, kloopend, i)
        i += 1
    print """</CsInstruments>
<CsScore>
"""
    i = 1
    for smplarr in m.smplarr:
        print """f %d 0 0 1 "instrument%d.raw" 0 1 0""" % (i, i)
        i += 1
    tempo = 0.12
    for track in ir_song.ir_track:
        for e in track:
            print "i %d %.2f %.2f %.2f" % (e.instr,
              e.start * tempo, (e.dur) * tempo, e.pitch)
    print """
</CsScore>
</CsoundSynthesizer>
"""
