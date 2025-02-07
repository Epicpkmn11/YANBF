"""
YANBF
Copyright © 2022-present lifehackerhansol

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import argparse
import os
import requests
import subprocess
import unicodedata
from struct import unpack
from sys import exit
from typing import Optional

from PIL import Image

from bannergif import bannergif, crc16


class Generator():
    def __init__(self, infile: str, *, boxart: Optional[str], output: Optional[str], sound: Optional[str], path: Optional[str]):
        self.boxart = boxart
        self.infile = infile
        self.output = output
        self.sound = sound
        self.path = path
        self.cmdarg = ""
        if os.name != "nt":
            self.cmdarg = "./"

    title: dict = None
    gamecode: str = None
    boxartcustom: bool = False
    uniqueid: int = None

    def message(self, output: str):
        """Outputting text. Defaults to print(). Can be replaced with other frontends (i.e. a GUI?)"""
        return print(output)

    def makeicon(self):
        im = bannergif(self.infile)
        im.putpalette(b"\xFF\xFF\xFF" + im.palette.palette[3:])
        im = im.convert('RGB')
        im = im.resize((48, 48), resample=Image.LINEAR)
        im.save('data/icon.png')
        return 0

    def get_title(self) -> dict:
        # get banner title
        rom = open(self.infile, "rb")
        rom.seek(0x68, 0)
        banneraddrle = rom.read(4)
        banneraddr = unpack("<I", banneraddrle)[0]
        rom.seek(banneraddr, 0)
        bannerversion = unpack("<H", rom.read(2))[0] & 3
        langnum = 6
        if bannerversion == 2:
            langnum = 7
        elif bannerversion == 3:
            langnum = 8

        # crc checking, ignore banner version 1
        if bannerversion >= 2:
            rom.seek(banneraddr + 0x4)
            crc093F = unpack("<H", rom.read(2))[0]
            rom.seek(banneraddr + 0x20)
            data = rom.read(0x940 - 0x20)
            calcrc = crc16(data)
            if crc093F != calcrc:
                langnum = 6
            else:
                if bannerversion == 3:
                    rom.seek(banneraddr + 0x6)
                    crc0A3F = unpack("<H", rom.read(2))[0]
                    rom.seek(banneraddr + 0x20)
                    data = rom.read(0xA40 - 0x20)
                    calcrc = crc16(data)
                    if crc0A3F != calcrc:
                        langnum = 7
        title = []
        titles = {}
        for x in range(langnum):
            offset = 0x240 + (0x100 * x)
            rom.seek(banneraddr + offset, 0)
            title.append(str(rom.read(0x100), "utf-16-le"))
            title[x] = title[x].split('\0', 1)[0]
        titles['jpn'] = title[0].split('\n')
        titles['eng'] = title[1].split('\n')
        titles['fra'] = title[2].split('\n')
        titles['ger'] = title[3].split('\n')
        titles['ita'] = title[4].split('\n')
        titles['spa'] = title[5].split('\n')
        if langnum >= 7:
            titles['chn'] = title[6].split("\n")
        if langnum >= 8:
            titles['kor'] = title[7].split("\n")
        for lang in titles:
            if len(titles[lang]) == 1:
                titles[lang] = None
        self.title = titles
        return 0

    def makesmdh(self):
        bannertoolarg = f'{self.cmdarg}bannertool makesmdh -i "data/icon.png" '
        title = self.title

        if len(title['eng']) == 3:
            bannertoolarg += f'-s "{title["eng"][0]} {title["eng"][1]}" -l "{title["eng"][0]} {title["eng"][1]}" -p "{title["eng"][2]}" '
        else:
            bannertoolarg += f'-s "{title["eng"][0]}" -l "{title["eng"][0]}" -p "{title["eng"][1]}" '

        if title['jpn'] is not None:
            if len(title['jpn']) == 3:
                bannertoolarg += f'-js "{title["jpn"][0]} {title["jpn"][1]}" -jl "{title["jpn"][0]} {title["jpn"][1]}" -jp "{title["jpn"][2]}" '
            else:
                bannertoolarg += f'-js "{title["jpn"][0]}" -jl "{title["jpn"][0]}" -jp "{title["jpn"][1]}" '

        if title['fra'] is not None:
            if len(title['fra']) == 3:
                bannertoolarg += f'-fs "{title["fra"][0]} {title["fra"][1]}" -fl "{title["fra"][0]} {title["fra"][1]}" -fp "{title["fra"][2]}" '
            else:
                bannertoolarg += f'-fs "{title["fra"][0]}" -fl "{title["fra"][0]}" -fp "{title["fra"][1]}" '

        if title['ger'] is not None:
            if len(title['ger']) == 3:
                bannertoolarg += f'-gs "{title["ger"][0]} {title["ger"][1]}" -gl "{title["ger"][0]} {title["ger"][1]}" -gp "{title["ger"][2]}" '
            else:
                bannertoolarg += f'-gs "{title["ger"][0]}" -gl "{title["ger"][0]}" -gp "{title["ger"][1]}" '

        if title['ita'] is not None:
            if len(title['ita']) == 3:
                bannertoolarg += f'-is "{title["ita"][0]} {title["ita"][1]}" -il "{title["ita"][0]} {title["ita"][1]}" -ip "{title["ita"][2]}" '
            else:
                bannertoolarg += f'-is "{title["ita"][0]}" -il "{title["ita"][0]}" -ip "{title["ita"][1]}" '

        if title['spa'] is not None:
            if len(title['spa']) == 3:
                bannertoolarg += f'-ss "{title["spa"][0]} {title["spa"][1]}" -sl "{title["spa"][0]} {title["spa"][1]}" -sp "{title["spa"][2]}" '
            else:
                bannertoolarg += f'-ss "{title["spa"][0]}" -sl "{title["spa"][0]}" -sp "{title["spa"][1]}" '

        if 'chn' in title and title['chn'] is not None:
            if len(title['chn']) == 3:
                bannertoolarg += f'-scs "{title["chn"][0]} {title["chn"][1]}" -scl "{title["chn"][0]} {title["chn"][1]}" -scp "{title["chn"][2]}" '
            else:
                bannertoolarg += f'-scs "{title["chn"][0]}" -scl "{title["chn"][0]}" -scp "{title["chn"][1]}" '

        if 'kor' in title and title['kor'] is not None:
            if len(title['kor']) == 3:
                bannertoolarg += f'-ks "{title["kor"][0]} {title["kor"][1]}" -kl "{title["kor"][0]} {title["kor"][1]}" -kp "{title["kor"][2]}" '
            else:
                bannertoolarg += f'-ks "{title["kor"][0]}" -kl "{title["kor"][0]}" -kp "{title["kor"][1]}" '

        bannertoolarg += '-o "data/output.smdh"'
        bannertoolrun = subprocess.run(bannertoolarg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if bannertoolrun.returncode != 0:
            self.message(f"{bannertoolrun.stdout}\n{bannertoolrun.stderr}")
            exit()
        return 0

    def getgamecode(self):
        rom = open(self.infile, "rb")
        rom.seek(0xC, 0)
        code = str(rom.read(0x4), "ascii")
        rom.close()
        self.gamecode = code
        return 0

    def downloadfromapi(self):
        r = requests.get(f"https://yanbf.api.hansol.ca/banner/{self.gamecode}")
        if r.status_code == 200:
            data = r.json()
            if not self.boxart:
                if 'image' in data:
                    r = requests.get(data['image'])
                    if r.status_code == 200:
                        f = open("data/banner.png", "wb")
                        f.write(r.content)
                        f.close()
                        self.boxart = os.path.abspath("data/banner.png")
                        self.boxartcustom = True
            if not self.sound:
                if 'sound' in data:
                    r = requests.get(data['sound'])
                    if r.status_code == 200:
                        f = open("data/customsound.wav", 'wb')
                        f.write(r.content)
                        f.close()
                        self.sound = os.path.abspath("data/customsound.wav")
        return 0

    def downloadboxart(self):
        # get boxart for DS, to make banner
        gametdbregions = {
            'D': "DE",
            'E': "US",
            'F': "FR",
            'H': "NL",
            'I': "IT",
            'J': "JA",
            'K': "KO",
            'R': "RU",
            'S': "ES",
            'T': "US",
            'U': "AU",
            '#': "HB"
        }
        ba_region = gametdbregions[self.gamecode[3]] if self.gamecode[3] in gametdbregions else "EN"
        r = requests.get(f"https://art.gametdb.com/ds/coverM/{ba_region}/{self.gamecode}.jpg")
        if r.status_code != 200:
            r = requests.get(f"https://art.gametdb.com/ds/coverM/EN/{self.gamecode}.jpg")
            if r.status_code != 200:
                return 1
        f = open("data/boxart.jpg", "wb")
        f.write(r.content)
        f.close()
        self.boxart = os.path.abspath("data/boxart.jpg")
        return 0

    def resizebanner(self):
        banner = Image.open(self.boxart)
        width, height = banner.size
        new_height = 128
        new_width = new_height * width // height
        banner = banner.resize((new_width, new_height), resample=Image.ANTIALIAS)
        new_image = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
        upper = (256 - banner.size[0]) // 2
        new_image.paste(banner, (upper, 0))
        new_image.save('data/banner.png', 'PNG')
        self.boxart = os.path.abspath('data/banner.png')
        self.message(f"Reformatted banner image: {self.boxart}")
        return 0

    def makebanner(self):
        bannertoolarg = f'bannertool makebanner -i "data/banner.png" -a "{self.sound}" -o "data/banner.bin"'
        self.message(f"Using arguments: {bannertoolarg}")
        bannertoolrun = subprocess.run(f'{self.cmdarg}{bannertoolarg}', shell=True, capture_output=True, universal_newlines=True)
        if bannertoolrun.returncode != 0:
            self.message(f"{bannertoolrun.stdout}\n{bannertoolrun.stderr}")
            exit()
        return 0

    def getrompath(self, path) -> str:
        root: str = ""
        if os.name == 'nt':
            root = os.path.abspath(path)[:2]
        else:
            temp = path
            orig_dev = os.stat(temp).st_dev
            while temp != '/':
                direc = os.path.dirname(temp)
                if os.stat(direc).st_dev != orig_dev:
                    break
                temp = direc
            root = temp
        if root == "C:" or root == "/":
            self.message("This ROM is not on your SD card!\nPlease use a ROM on your SD card, or set a custom path.")
            exit()
        path = unicodedata.normalize("NFC", os.path.abspath(path))
        path = path.replace(root, "")
        if os.name == 'nt':
            path = path.replace('\\', '/')
        return path

    def makeromfs(self):
        try:
            os.mkdir('romfs')
        except FileExistsError:
            pass
        romfs = open('romfs/path.txt', 'w', encoding="utf8")
        romfs.write(f"sd:{self.path}")
        romfs.close()
        return 0

    def makeuniqueid(self):
        try:
            f = open("id.txt", "r")
        except FileNotFoundError:
            self.uniqueid = 0xFF400
            return 0
        # we are going to use the 0xFF400-0xFF7FF range
        index = int(f.read())
        self.uniqueid = 0xFF400 + index + 1
        return 0

    def makecia(self):
        makeromarg = f'{self.cmdarg}makerom -f cia -target t -exefslogo -rsf data/build-cia.rsf -elf data/forwarder.elf -banner data/banner.bin -icon data/output.smdh -DAPP_ROMFS=romfs -major 1 -minor 6 -micro 2 -DAPP_VERSION_MAJOR=1 -o "{self.output}" '
        makeromarg += f'-DAPP_PRODUCT_CODE=CTR-H-{self.gamecode} -DAPP_TITLE="{self.title["eng"][0]}" -DAPP_UNIQUE_ID={self.uniqueid}'
        self.message(f"Using arguments: {makeromarg}")
        makeromrun = subprocess.run(makeromarg, shell=True, capture_output=True, universal_newlines=True)
        if makeromrun.returncode != 0:
            self.message(f"{makeromrun.stdout}\n{makeromrun.stderr}")
            exit()
        f = open("id.txt", "w")
        f.write(str(self.uniqueid - 0xFF400))
        f.close()
        return 0

    def start(self):
        if not os.path.exists(os.path.abspath(self.infile)):
            self.message("Failed to open ROM. Is the path valid?")
            exit()
        if not self.path:
            self.message("Custom path is not provided. Using path for input file.")
            self.path = self.getrompath(os.path.abspath(self.infile))
        if not self.output:
            self.output = f"{os.path.basename(self.infile)}.cia"
        self.message(f"Using ROM path: {self.path}")
        self.message(f"Output file: {self.output}")
        self.message("Getting gamecode...")
        self.getgamecode()
        self.message("Extracting and resizing icon...")
        self.makeicon()
        self.message("Getting ROM titles...")
        self.get_title()
        self.message("Creating SMDH...")
        self.makesmdh()
        if not self.boxart or not self.sound:
            self.message("Checking API if a custom banner or sound is provided...")
            self.downloadfromapi()
            if not self.sound:
                self.sound = os.path.abspath("data/dsboot.wav")
            if not self.boxart:
                self.message("No banner provided. Checking GameTDB for standard boxart...")
                if self.downloadboxart() != 0:
                    self.message("Banner was not found. Exiting.")
                    exit()
        self.message(f"Using sound file: {self.sound}")
        self.message(f"Using banner image: {self.boxart}")
        if not self.boxartcustom:
            self.message("Resizing banner...")
            self.resizebanner()
        self.message("Creating banner...")
        self.makebanner()
        self.message("Creating romfs...")
        self.makeromfs()
        self.message("Generating UniqueID...")
        self.makeuniqueid()
        self.message("Running makerom...")
        self.makecia()
        self.message("CIA generated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YANBF Generator")
    parser.add_argument("input", metavar="input.nds", type=str, nargs=1, help="DS ROM path")
    parser.add_argument("-p", "--path", metavar="<custom path>.nds", type=str, nargs=1, help="Custom ROM path")
    parser.add_argument("-o", "--output", metavar="input.nds.cia", type=str, nargs=1, help="output CIA")
    parser.add_argument("-b", "--boxart", metavar="boxart.png", type=str, nargs=1, help="Custom banner box art")
    parser.add_argument("-s", "--sound", metavar="sound.wav", type=str, nargs=1, help="Custom icon sound (WAV only)")

    args = parser.parse_args()
    infile = None
    path = None
    boxart = None
    output = None
    sound = None
    tidlow = None
    if args.boxart:
        boxart = args.boxart[0]
    if args.input:
        infile = args.input[0]
    if args.output:
        output = args.output[0]
    if args.sound:
        sound = args.sound[0]
    if args.path:
        path = args.path[0]

    generator = Generator(infile, boxart=boxart, output=output, sound=sound, path=path)
    generator.start()
    exit()
