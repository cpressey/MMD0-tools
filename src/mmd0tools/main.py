from mmd0tools.mmd0 import Buffer, MMD0


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
    b = m.flatten()
    for track in b.to_ir_events():
        print "IR TRACK"
        for ir in track:
            print ir


def samples(args):
    m = load(args[1])
    for byte in m.smplarr[0].data:
        # upsample to 16-bit for aplay's benefit
        # usage: mmd0.py your.med | aplay --rate=8287 --format=S16_BE
        sys.stdout.write(chr(byte))
        sys.stdout.write(chr(0))
