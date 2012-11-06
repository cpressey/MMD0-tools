"""Intermediate representation of an MMD0 file under conversion.

This module was written by Chris Pressey, who hereby places it into the
public domain.

"""


from mmd0tools.mmd0 import lol, CMD_NAMES, NOTE_NAMES, MMD0Block


class IRSong(object):
    def __init__(self, mmd0):
        """Turn the event data in the blocks in the song sequence
        into one big block.

        """

        # create IRInstruments
        self.ir_instr = []
        i = 0
        while i < mmd0.song.numsamples:
            smplarr = mmd0.smplarr[i]
            sample = mmd0.song.sample[i]
            assert smplarr.type == 0
            assert smplarr.length == len(smplarr.data)
            self.ir_instr.append(
                IRInstrument(sample.rep, sample.replen,
                             sample.svol, sample.strans,
                             smplarr.data)
            )
            i += 1

        numtracks = None
        numlines = None
        for block in mmd0.blockarr:
            if numtracks is None:
                numtracks = block.numtracks
            else:
                assert numtracks == block.numtracks, \
                    "blocks have differing numbers of tracks"
            if numlines is None:
                numlines = block.lines
            else:
                assert numlines == block.lines, \
                    "blocks have differing numbers of lines"

        # XXX this is sort of an abuse of MMD0Block
        b = MMD0Block(None, 0)
        b.clear(numtracks, 0)
        for block_no in mmd0.song.playseq[:mmd0.song.songlen]:
            block = mmd0.blockarr[block_no]

            line_no = 0
            while line_no < numlines:
                track_no = 0
                end_block_now = False
                while track_no < numtracks:
                    e = block.track[track_no][line_no]
                    if e.command == 15 and e.databyte == 0:
                        end_block_now = True
                    b.track[track_no].append(e)
                    track_no += 1
                if end_block_now:
                    break
                line_no += 1

        b.lines = len(b.track[0])
        #b.dump(999)

        self.numtracks = numtracks
        self.mmd0_block = b
        self.ir_track = None

    def to_ir_events(self):
        ir_track = lol(self.numtracks)
        track_no = 0
        while track_no < self.numtracks:
            ir_track[track_no] = self.track_to_ir_events(track_no)
            track_no += 1
        self.ir_track = ir_track

    def track_to_ir_events(self, track_no):
        track = self.mmd0_block.track[track_no]
        ir_events = []
        pos = 0

        instr = None
        note = None
        effects = []
        start = 0
        dur = 0
        note_is_going = True

        while pos < len(track):
            e = track[pos]
            if e.instr > 0:
                if instr is not None:
                    ir = IREvent(instr, note, start, dur, track_no, effects)
                    ir_events.append(ir)
                instr = e.instr
                note = e.note
                dur = 0
                start = pos
                effects = []
                note_is_going = True
            if e.command > 0 or e.databyte > 0:
                if e.command == 12 and e.databyte == 0:
                    # The volume has been lowered to zero.  Assume the
                    # note has stopped.  (This is an approximation, as
                    # the volume may be raised again.  But we'll live with
                    # losing those effects for now.
                    note_is_going = False
                else:
                    # XXX record pos here
                    effects.append((e.command, e.databyte))
            if note_is_going:
                dur += 1
            pos += 1

        return ir_events

    def dump(self):
        for track in self.ir_track:
            print "IR TRACK"
            print "--------"
            for ir in track:
                print ir
            print


class IREvent(object):
    """An event in our intermediate representation.

    """
    def __init__(self, instr, note, start, dur, track, effects):
        self.instr = instr
        self.note = note
        self.start = start
        self.dur = dur
        self.track = track  # mmd0 track# that this came from
        self.effects = effects

    def __str__(self):
        return "i %02d %05d %02d %s %d/%s" % (
            self.instr, self.start, self.dur, NOTE_NAMES[self.note],
            self.track, self.effects
        )

    @property
    def pitch(self):
        n = self.note
        octave = n / 12
        step = n % 12
        val = (octave * 1.0) + (step * 0.01)
        return val


class IRInstrument(object):
    def __init__(self, rep, replen, svol, strans, data):
        self.rep = rep
        self.replen = replen
        self.svol = svol
        self.strans = strans
        self.data = data

    def write_to(self, filename):
        with open(filename, 'w') as f:
            for byte in self.data:
                f.write(chr(byte))
                # upsampled to 16-bit for aplay's benefit
                # usage: aplay instrument1.raw --rate=8287 --format=S16_BE
                # f.write(chr(0))

    def print_csound_instr(self, instr_num):      
        # /* 44100.0 / 8287.0 == 5.321588029443707 */
        rep = self.rep
        replen = self.replen
        
        # special case b/c I can't figure this out yet
        if rep == 0 and replen == 2:
            rep = len(self.data) - 2
        print """
instr %d  /* %d samples @ 8287 samples/sec */
aSig      loscil   0.25,                            /* xamp */ \ 
                   cpspch(p4),                   /* kcps */ \
                   %d,                           /* ifn */ \ 
                   cpspch(1.00) * 5.321588029443707,  /* ibas */ \ 
                   1,                            /* imod1 */ \ 
                   %d,                           /* ibeg1 */ \ 
                   %d,                           /* iend1 */ \
                   1,                            /* imod2 */ \ 
                   0,                            /* ibeg2 */ \ 
                   1                             /* iend2 */
          out      aSig

endin
""" % (instr_num, len(self.data), instr_num,
       rep,
       rep + self.replen)
