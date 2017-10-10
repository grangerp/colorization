import sys
import handler

def get_stdin():
    buf = ""
    for line in sys.stdin:
        buf = buf + line
    return buf

def read_head():
    buf = ""
    while(True):
        line = sys.stdin.readline()
        buf += line

        if line == "\r\n":
            break
    return buf

if(__name__ == "__main__"):
    st = get_stdin()
    print(handler.handle(st))
