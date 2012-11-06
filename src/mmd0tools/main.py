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

    # dump all instruments to files
    for (instr_num, ir_instr) in enumerate(ir_song.ir_instr):
        ir_instr.write_to("instrument%d.raw" % (instr_num + 1))

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
    for (instr_num, ir_instr) in enumerate(ir_song.ir_instr):
        ir_instr.print_csound_instr(instr_num + 1)
    print """</CsInstruments>
<CsScore>
"""
    for (instr_num, ir_instr) in enumerate(ir_song.ir_instr):
        print """f %d 0 0 1 "instrument%d.raw" 0 1 0""" % (instr_num + 1, instr_num + 1)

    tempo = 0.12
    for track in ir_song.ir_track:
        for e in track:
            print "i %d %.2f %.2f %.2f" % (e.instr,
              e.start * tempo, (e.dur) * tempo, e.pitch)
    print """
</CsScore>
</CsoundSynthesizer>
"""
