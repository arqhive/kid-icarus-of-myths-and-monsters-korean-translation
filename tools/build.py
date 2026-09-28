"""Build all three localization stages and copy the final ROM to Windows Desktop."""
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', nargs='?', help='Original USA/Europe .gb file')
    args = parser.parse_args()
    if args.rom:
        os.environ['KID_ICARUS_ROM'] = str(Path(args.rom).resolve())
    import build_demo
    import build_title
    import build_full
    from desktop import copy_to_desktop
    build_demo.main()
    build_title.main()
    build_full.main()
    copy_to_desktop(build_full.OUTPUT)


if __name__ == '__main__':
    main()
