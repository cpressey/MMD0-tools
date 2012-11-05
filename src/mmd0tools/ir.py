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
            ir_track[track_no] = self.track_to_ir_events(self.mmd0_block.track[track_no])
            track_no += 1
        # XXX IRBlock?
        self.ir_track = ir_track

    def track_to_ir_events(self, track):
        # XXX handle rests (at beginning of track, and after
        # VOLM/00 commands.)
        # XXX handle effects

        ir_events = []

        line_no = 0
        instr = None
        note = None
        dur = 0

        while line_no < len(track):
            e = track[line_no]
            if e.instr > 0:
                if instr is not None:
                    ir = IREvent(instr, note, dur, None)
                    ir_events.append(ir)
                instr = e.instr
                note = e.note
                dur = 1
            else:
                dur += 1
            line_no += 1

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
    def __init__(self, instr, note, dur, effects):
        self.instr = instr
        self.note = note
        self.dur = dur
        self.effects = effects

    def __str__(self):
        c = ""
        if self.effects:
            c = "/*"
        return "[%02d/%s/%d%s]" % (
            self.instr, NOTE_NAMES[self.note], self.dur, c
        )
