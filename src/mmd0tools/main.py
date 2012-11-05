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
    
    for e in ir_song.ir_track[2]:
        if e.instr == 1:
            print "i %d %.2f %.2f %.2f" % (e.instr,
              (e.start - 98) * 0.10, (e.dur) * 0.10, e.pitch)


def samples(args):
    m = load(args[1])
    for byte in m.smplarr[0].data:
        # upsample to 16-bit for aplay's benefit
        # usage: mmd0.py your.med | aplay --rate=8287 --format=S16_BE
        sys.stdout.write(chr(byte))
        sys.stdout.write(chr(0))
