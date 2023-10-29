import os
from gooey import Gooey, GooeyParser

@Gooey
def main():
    parser = GooeyParser()
    parser.add_argument('Filename', widget="FileChooser")
    args = parser.parse_args()
    print(args)

if __name__=='__main__':
    os.environ['PYTHONUTF8']="1"
    main()