import numpy as np
from PIL import Image
import heapq
import copy
from bitstring import BitArray
import struct
import os
import cv2


class Node:
    def __init__(self, Intval, left=None, right=None):
        self.intensityVal = Intval
        self.left = left
        self.right = right

    def __lt__(self, nxt):
        return self.frequency < nxt.frequency


def bstr(n):  # n in range 0-255
    return ''.join([str(n >> x & 1) for x in (7, 6, 5, 4, 3, 2, 1, 0)])
# read file into an array of binary formatted strings.


def read_binary(path):
    f = open(path, 'rb')
    binlist = []
    while True:
        # B stands for unsigned char (8 bits)
        byte = f.read(1)
        if not byte:
            break
        bin = struct.unpack('B', byte)[0]
        strBin = bstr(bin)
        binlist.append(strBin)
    f.close()
    return binlist


binlst = read_binary('compressedimg.bin')
finstr = ""
for t in binlst:
    finstr += t


IntensityCodeDictionary = {}
image_array = []


def decode(codedString, image_array, IntensityCodeDictionary):
    # no. of trash 0s at begin
    initialTrash = 8-int((codedString[-3:]), 2)
    codedString = codedString[:-3]  # removed ending 3 bits
    width = int(codedString[initialTrash:initialTrash+16], 2)  # width
    height = int(codedString[initialTrash+16:initialTrash+32], 2)  # height
    residue = codedString[initialTrash+32:]
    maxBitsforIntens = len((bin(width*height*3))[2:])
    # no of unique intensities
    UniqIntens = int(residue[:maxBitsforIntens], 2)
    residue = residue[maxBitsforIntens:]
    for t in range(UniqIntens):
        intensity = int(residue[:8], 2)
        codeLength = int(residue[8:16], 2)+1
        IntensityCodeDictionary[intensity] = residue[16:16+codeLength]
        residue = residue[16+codeLength:]
    # Codes to all intensity values collected
    IntensityCodeDictionary = dict((v, k)
                                   for (k, v) in IntensityCodeDictionary.items())
    # Now Decoding the intensity values
    IntensityList = []
    pseudocode = ""
    for t in residue:
        pseudocode += t
        if pseudocode in IntensityCodeDictionary.keys():
            if len(IntensityList) < 2:
                IntensityList.append(IntensityCodeDictionary[pseudocode])
                pseudocode = ""
            else:
                IntensityList.append(IntensityCodeDictionary[pseudocode])
                pseudocode = ""
                image_array.append(IntensityList)
                IntensityList = []

    return image_array, width, height


image_list, width, height = decode(
    finstr, image_array, IntensityCodeDictionary)
image_array = np.array(image_list)
image_array.astype(np.uint8)
imgarr = np.zeros((height, width, 3), np.uint8)
for h in range(height):
    for w in range(width):
        imgarr[h][w] = image_array[h*width+w]

imgg = Image.new('RGB', [width, height], 0x000000)

for h in range(height):
    for w in range(width):
        imgg.putpixel((w, h), (imgarr[h][w][0],
                      imgarr[h][w][1], imgarr[h][w][2]))
imgg.save('decompressedimg.bmp')

print("Image decompressed. Can be found in the same folder with name decompressedimg.bmp")
