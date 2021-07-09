#Compresses the 8bit BMP image using huffman encoding

#imports
import numpy as np
from PIL import Image
import heapq
import copy
from bitstring import BitArray
import os
import struct

#Reading pixel RGB data from the image
an_image = Image.open("images/visa-logo.bmp")
width, height = an_image.size
image_sequence = an_image.getdata()
image_array = np.array(image_sequence)  #is of the form [[r1,g1,b1],[r2,g2,b2],[r3,g3,b3],...] where ri,bi and gi are intensity values of respective rgb colors

#Counting the number of times an intensity value has been repeated in the image_array
IntensityCounter = {}
for eachPixel in range(len(image_array)):
    for color in range(2):
        if image_array[eachPixel][color] not in IntensityCounter:
            IntensityCounter[image_array[eachPixel][color]] = 1
        else:
            IntensityCounter[image_array[eachPixel][color]] += 1
#Dictionary is ready, in which keys are intensities and values are the frequency of their occurence 


#The class structure of each Node in the Huffman Tree
class Node:
    def __init__(self, Intval, freq, left=None, right=None):
        self.intensityVal = Intval  #Intensity value
        self.frequency = freq       #Frequency that the intensity value occurs in the image
        self.left = left            #Left child of this node in the huffman tree
        self.right = right          # Right child of this node in the huffman tree
        self.code = ""              #The new code obtained after doing huffman encoding

    #Operations which are helpful for comparisions of two Node objects which we have created
    def __lt__(self, nxt):
        return self.frequency < nxt.frequency

    def __le__(self, nxt):
        return self.frequency <= nxt.frequency


ListOfAllNodes = []                     #All Nodes with unique intensity values will be stored in this list
for pixVal in IntensityCounter.keys():
    ListOfAllNodes.append(Node(pixVal, IntensityCounter[pixVal]))

ListOfAllNodes2 = copy.deepcopy(ListOfAllNodes) #The above list will be used to build the tree. So,let's have a copy in which we update the huffman codes

heapq.heapify(ListOfAllNodes)           #Heapifying the list gives the Node with the smallest frequency

while len(ListOfAllNodes) > 1:
    Child1 = heapq.heappop(ListOfAllNodes)  #Popping Node with least frequency
    Child2 = heapq.heappop(ListOfAllNodes)  #Popping Node with least frequency
    #We now have 2 Nodes with least frequencies among all. Now join those 2 nodes to a node whose frequency is sum of the frequencies of the 2
    NewNode = Node(-1, Child1.frequency+Child2.frequency, Child1, Child2)
    heapq.heappush(ListOfAllNodes, NewNode) #Push this new subtree into the heap
#Everytime, 2 nodes are removed and joined to build a tree and its added to the heap. Finally, only 1 node is left in the list
#which is nothing but the Huffman tree

HuffmanTree = ListOfAllNodes[0]

#The following printH function is just used for testing purpose which prints the intensity values of the nodes in the preorder fashion
preOrder = []
def printH(root):
    if root == None:
        return
    preOrder.append(root.intensityVal)
    printH(root.left)
    printH(root.right)
printH(HuffmanTree)


#Searches for a given node in the list and return the index of that node in the list
def search(ListOfNodes, Node):
    for t in range(len(ListOfNodes)):
        if ListOfNodes[t].intensityVal == Node.intensityVal:
            return t
    return 1000000000000


#A recursive function to encode the intensity values. This is the main stage of huffman encoding that produces the encoded strings
def encode(root, encodedString):
    #if it's a leaf return the encoded string
    if root.left == None and root.right == None:
        index = search(ListOfAllNodes2, root)
        ListOfAllNodes2[index].code = encodedString
        return
    enc1 = encodedString + "0"
    enc2 = encodedString + "1"
    encode(root.left, enc1)  # Add a 0 if you go to left
    encode(root.right, enc2)  # Add a 1 if you go to left
    return


encode(HuffmanTree, "")


def DictionaryOfCodes(IntensityCounter, ListOfAllNodes2):
    for t in ListOfAllNodes2:
        IntensityCounter[t.intensityVal] = t

#Creating a dictionary with keys as intensities and values as their huffman codes
DictionaryOfCodes(IntensityCounter, ListOfAllNodes2)

#To communicate with the decoder effectively, we need to send the data in specific sizes. This function comes handy to extend a string with 0s in front, so that the total string size becomes as argument no. 1
def extraPaddingOf0sInFront(FinalNoOfBits, CurrentString):
    l = len(CurrentString)
    DesiredNoOfBitsToAdd = FinalNoOfBits-l
    st = ''
    for t in range((DesiredNoOfBitsToAdd)):
        st += '0'
    st += CurrentString
    return st

'''
    This function reads the complete image_array and outputs the binary string which can be decoded by the decoder.
    The format the string is produced::
    |Some 0s such that total string becomes a multiple of 8(required to write in a file)|8 bits representing width of the image|
    8 bits representing height of the image|(no. of bits in(width*height*3(i.e;total no. of individual intensities))) no. of bits
    to represent no. of unique intensity values are encoded||8 bits intensityVal|3 bits size of code|code||.......until final code||
    encoded string of the image_array|3 bits->no. of 0s to add in front|
'''
def CodeTheImage(imageArray, ListOfAllNodes2, width, height):
    encodedImageString = ""
    widthbin = bin(width)[2:]
    widthStr = extraPaddingOf0sInFront(16, widthbin)
    assert(len(widthStr) == 16)

    heightbin = bin(height)[2:]
    heightStr = extraPaddingOf0sInFront(16, heightbin)
    assert(len(heightStr) == 16)

    encodedImageString += (widthStr+heightStr)
    assert(len(encodedImageString) == 32)
    # Maximum possible bits of no. of different intensity values
    maxBitsInt = len((bin(width*height*3)[2:]))
    l = len(ListOfAllNodes2)  # no of different intensity values
    encodedImageString += extraPaddingOf0sInFront(maxBitsInt, ((bin(l))[2:]))
    for t in ListOfAllNodes2:
        encodedImageString += (extraPaddingOf0sInFront(8,
                               bin(t.intensityVal)[2:]))  # 8 bits
        assert(len(bin(t.intensityVal)[2:]) <= 8)
        # 3 bits
        encodedImageString += extraPaddingOf0sInFront(
            8, bin(len(t.code)-1)[2:])
        encodedImageString += t.code
    aaaa = len(encodedImageString)
    for i in range(len(imageArray)):
        for j in range(3):
            intensity = imageArray[i][j]
            encodedImageString += (IntensityCounter[intensity].code)

    Length = len(encodedImageString)
    extraBits = (Length+3) % 8
    encodedImageString += extraPaddingOf0sInFront(3, bin(extraBits)[2:])
    encodedImageString = extraPaddingOf0sInFront(
        Length+(8-extraBits)+3, encodedImageString)

    return encodedImageString


CodedImageString = CodeTheImage(image_array, ListOfAllNodes2, width, height)
print("encoded")


#Writing it in a binary file
def writeToFile(mystr):
    # path of the file after compression
    fileobj = open('compressedimg.bin', 'wb')
    b = BitArray(bin=mystr)
    b.tofile(fileobj)
    fileobj.close()

#Another version to write(not used )
def writeToFile2(chars):
    BITS_IN_BYTE = 8
    bytes = bytearray(int(chars[i:i+BITS_IN_BYTE], 2)
                      for i in range(0, len(chars)-7, BITS_IN_BYTE))
    open('filename', 'wb').write(bytes)


writeToFile(CodedImageString)

#Checking how much the file has been compressed
file_sizeorig = os.path.getsize('test.bmp')
print("Original File Size is :", file_sizeorig, "bytes")


file_size = os.path.getsize('compressedimg.bin')
print("Compressed File Size is :", file_size, "bytes")
print("Compressed by ", (file_sizeorig-file_size)*100.0/file_sizeorig, "%")
print("Compressed file can be found in the same folder with name 'compressedimg.bin' ")

# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
