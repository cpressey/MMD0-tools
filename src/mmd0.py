#!/usr/bin/env python

# This script was written by Chris Pressey, who hereby places it into the
# public domain.

# This script is also a mess and needs to be refactored.


import sys


class Buffer(object):
    def __init__(self, file):
        self.contents = file.read()

    def ubyte_at(self, pos):
        return ord(self.contents[pos])

    def ubytes_at(self, pos, count):
        ubytes = []
        i = 0
        while i < count:
            ubytes.append(self.ubyte_at(pos + i))
            i += 1
        return ubytes

    def byte_at(self, pos):
        u = ord(self.contents[pos])
        if u >= (256 / 2):
            u = -1 * (256 - u)
        return u

    def uword_at(self, pos):
        return ord(self.contents[pos]) * 256 + ord(self.contents[pos + 1])

    def word_at(self, pos):
        u = self.uword_at(pos)
        if u >= (65536 / 2):
            u = -1 * (65536 - u)
        return u

    def ulong_at(self, pos):
        return (ord(self.contents[pos]) * 256 * 256 * 256 +
                ord(self.contents[pos + 1]) * 256 * 256 +
                ord(self.contents[pos + 2]) * 256 +
                ord(self.contents[pos + 3]))

    def offset_at(self, pos):
        return self.ulong_at(pos)

    def offsets_at(self, pos, count):
        offsets = []
        i = 0
        while i < count:
            offsets.append(self.offset_at(pos + i * 4))
            i += 1
        return offsets


class MMD0(object):
    def __init__(self, buffer):
        self.buffer = buffer
        self.id = buffer.ulong_at(0)
        self.modlen = buffer.ulong_at(4)
        self.song_offset = buffer.offset_at(8)
        # offset to table of offsets
        self.blockarr_offset = buffer.offset_at(16)
        # offset to table of offsets
        self.smplarr_offset = buffer.offset_at(24)
        self.expdata_offset = buffer.offset_at(32)
        self.pstate = buffer.uword_at(40)
        self.pblock = buffer.uword_at(42)
        self.pline = buffer.uword_at(44)
        self.pseqnum = buffer.uword_at(46)
        self.actplayline = buffer.word_at(48)
        self.counter = buffer.ubyte_at(50)
        self.extra_songs = buffer.ubyte_at(51)

        # load the MMD0song structure
        self.song = MMD0song(buffer, self.song_offset)

        # load the block offset table, now that we know numblocks
        self.blockarr_offsets = buffer.offsets_at(self.blockarr_offset,
                                          self.song.numblocks)

        self.blockarr = []
        for block_offset in self.blockarr_offsets:
            self.blockarr.append(MMD0Block(buffer, block_offset))

        # ditto samples
        self.smplarr_offsets = buffer.offsets_at(self.smplarr_offset,
                                         self.song.numsamples)

        self.smplarr = []
        for smpl_offset in self.smplarr_offsets:
            self.smplarr.append(InstrHdr(buffer, smpl_offset))

    def flatten(self):
        """Turn the event data in the blocks in the song sequence
        into one big block.

        """
        numtracks = None
        numlines = None
        for block in self.blockarr:
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

        b = MMD0Block(None, 0)
        b.clear(numtracks, 0)
        for block_no in self.song.playseq[:self.song.songlen]:
            block = self.blockarr[block_no]

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

        return b

    def dump(self):
        print "MMD0 Header"
        print "-----------"
        for attr in ('id', 'modlen', 'song_offset', 'blockarr_offset',
                     'smplarr_offset', 'expdata_offset',
                     'pstate', 'pblock', 'pline', 'pseqnum',
                     'actplayline', 'counter', 'extra_songs',
                     'blockarr_offsets', 'smplarr_offsets'):
            print "%s: %r" % (attr, getattr(self, attr))
        print
        self.song.dump()

        print "Blocks"
        print "------"
        i = 0
        while i < self.song.numblocks:
            self.blockarr[i].dump(i)
            i += 1
        print

        print "Instruments"
        print "-----------"
        i = 0
        while i < self.song.numsamples:
            self.smplarr[i].dump(i)
            i += 1
        print


class MMD0song(object):
    def __init__(self, buffer, offset):
        self.buffer = buffer

        sample_offset = offset
        self.sample = []
        i = 0
        while i < 63:
            self.sample.append(MMD0sample(buffer, sample_offset))
            sample_offset += 8
            i += 1

        self.numblocks = buffer.uword_at(offset + 504)
        self.songlen = buffer.uword_at(offset + 506)
        self.playseq = buffer.ubytes_at(offset + 508, 256)
        self.deftempo = buffer.uword_at(offset + 764)
        self.playtransp = buffer.byte_at(offset + 766)
        self.flags = buffer.ubyte_at(offset + 767)
        self.flags2 = buffer.ubyte_at(offset + 768)
        self.tempo2 = buffer.ubyte_at(offset + 769)
        self.trkvol = buffer.ubytes_at(offset + 770, 16)
        self.mastervol = buffer.ubyte_at(offset + 786)
        self.numsamples = buffer.ubyte_at(offset + 787)

    def dump(self):
        print "MMD0song"
        print "--------"
        for attr in ('numblocks', 'songlen', 'playseq', 'deftempo',
                     'playtransp', 'flags', 'flags2', 'tempo2',
                     'trkvol', 'mastervol', 'numsamples'):
            print "%s: %r" % (attr, getattr(self, attr))
        i = 0
        while i < self.numsamples:
            self.sample[i].dump(i)
            i += 1
        print


class MMD0sample(object):
    def __init__(self, buffer, offset):
        self.buffer = buffer
        # rep and replen are shifted right one bit
        self.raw_rep = buffer.uword_at(offset)
        self.rep = self.raw_rep * 2
        self.raw_replen = buffer.uword_at(offset + 2)
        self.replen = self.raw_replen * 2
        self.midich = buffer.ubyte_at(offset + 4)
        self.midipreset = buffer.ubyte_at(offset + 5)
        self.svol = buffer.ubyte_at(offset + 6)
        self.strans = buffer.byte_at(offset + 7)

    def dump(self, num):
        print "Sample %d:" % num
        for attr in ('rep', 'replen',
                     #'midich', 'midipreset',
                     'svol', 'strans'):
            print "  %s: %r" % (attr, getattr(self, attr))


# deceptive name -- contains instrument sample data too
class InstrHdr(object):
    def __init__(self, buffer, offset):
        self.buffer = buffer
        self.length = buffer.ulong_at(offset)
        self.type = buffer.word_at(offset + 4)
        self.data = buffer.ubytes_at(offset + 6, self.length)

    def dump(self, num):
        print "InstrHdr %d:" % num
        for attr in ('length', 'type', 'data'):
            print "  %s: %r" % (attr, getattr(self, attr))


def lol(count):
    l = []
    i = 0
    while i < count:
        l.append([])
        i += 1
    return l


class MMD0Block(object):
    def __init__(self, buffer, offset):
        self.buffer = buffer
        if buffer is None:
            return
        self.numtracks = buffer.ubyte_at(offset)
        # lines is zero based, so # of lines == self.lines + 1
        self.raw_lines = buffer.ubyte_at(offset + 1)
        self.lines = self.raw_lines + 1

        self.track = lol(self.numtracks)

        offset = offset + 2
        line_no = 0
        while line_no < self.lines:
            track_no = 0
            while track_no < self.numtracks:
                event = buffer.ubytes_at(offset, 3)
                self.track[track_no].append(
                    MMD0Event(event[0], event[1], event[2])
                )
                offset += 3
                track_no += 1
            line_no += 1

    def clear(self, numtracks, lines):
        """For constructing blocks manually.

        """
        self.buffer = None
        self.numtracks = numtracks
        self.lines = lines
        self.track = lol(self.numtracks)

    def track_to_ir_events(self, track_no):
        track = self.track[track_no]

        ir_events = []

        line_no = 0
        instr = None
        note = None
        dur = None

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

    def dump(self, num):
        print "Block %d:" % num
        for attr in ('numtracks', 'lines'):
            print "  %s: %r" % (attr, getattr(self, attr))
        print "  Lines:"
        line_no = 0
        while line_no < self.lines:
            track_no = 0
            print "    ",
            while track_no < self.numtracks:
                s = str(self.track[track_no][line_no])
                print s.ljust(18),
                track_no += 1
            print
            line_no += 1


STEP_NAMES = ('C-', 'C#', 'D-', 'D#', 'E-', 'F-',
              'F#', 'G-', 'G#', 'A-', 'A#', 'B-')
NOTE_NAMES = ['----']
i = 0
while i < 128:
    octave = (i / 12) + 1
    step = i % 12
    octstr = str(octave).rjust(2)
    NOTE_NAMES.append('%s%s' % (STEP_NAMES[step], octstr))
    i += 1
NOTE_NAMES = NOTE_NAMES[:128]
CMD_NAMES = (
    'ARPG',
    'SLUP',
    'SLDN',
    'PORT',
    'VIBR',
    'SLFD',
    'SLVB',
    'TREM',
    'HLDC',
    'TMP2',
    '????',
    'JUMP',
    'VOLM',
    'VLSL',
    'SYNJ',
    'MISC',
)


class MMD0Event(object):
    """A single event in a slot on an MMD0 track.

    """
    def __init__(self, byte0, byte1, byte2):
        self.note = byte0 & 63
        x = byte0 & 128
        y = byte0 & 64
        i = (byte1 & (128 + 64 + 32 + 16)) >> 4
        if x:
            i += 32
        if y:
            i += 64
        self.instr = i
        self.command = byte1 & 15
        self.databyte = byte2

    def __str__(self):
        c = "%s/%02d" % (CMD_NAMES[self.command], self.databyte)
        if self.command == 0 and self.databyte == 0:
            c = "----/--"
        return "[%02d/%s/%s]" % (self.instr, NOTE_NAMES[self.note], c)


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


if __name__ == '__main__':
    b = None
    with open(sys.argv[1], 'r') as f:
        b = Buffer(f)
    m = MMD0(b)
    #m.dump()
    b = m.flatten()

    ir_events = b.track_to_ir_events(2)
    for ir in ir_events:
        print ir

    if False:
        for byte in m.smplarr[0].data:
            # upsample to 16-bit for aplay's benefit
            # usage: mmd0.py your.med | aplay --rate=8287 --format=S16_BE
            sys.stdout.write(chr(byte))
            sys.stdout.write(chr(0))
