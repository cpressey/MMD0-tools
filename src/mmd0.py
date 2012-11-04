#!/usr/bin/env python

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
        self.blockarr = buffer.offsets_at(self.blockarr_offset,
                                          self.song.numblocks)

    def dump(self):
        print "MMD0 Header"
        print "-----------"
        for attr in ('id', 'modlen', 'song_offset', 'blockarr_offset',
                     'smplarr_offset', 'expdata_offset',
                     'pstate', 'pblock', 'pline', 'pseqnum',
                     'actplayline', 'counter', 'extra_songs',
                     'blockarr'):
            print "%s: %r" % (attr, getattr(self, attr))
        print
        self.song.dump()


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
        self.rep = buffer.uword_at(offset)
        self.replen = buffer.uword_at(offset + 2)
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


if __name__ == '__main__':
    import sys
    b = None
    with open(sys.argv[1], 'r') as f:
        b = Buffer(f)
    m = MMD0(b)
    m.dump()
