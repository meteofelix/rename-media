#!/usr/bin/python3
"""Rename files according to creation timestamp"""
import sys
import os
import getopt
import logging
import subprocess
import shlex
import time
from collections import deque

# TODO: check if user has root permissions
# TODO: don't overwrite target
# TODO: check necessary binaries

def checkdir(path):
    """Check if string is existing path."""
    try:
        if os.path.isdir(path):
            pass
        else:
            logging.critical('%s ist kein Verzeichnis', path)
            sys.exit(2)
    except TypeError:
        logging.critical('%s ist kein Verzeichnis', path)
        sys.exit(2)
def getMimeType(filename):
    """Get mimetype of file"""
    cmd = 'file -i -b ' + filename
    args = shlex.split(cmd)
    returnValue = subprocess.check_output(args, universal_newlines=True)
    mimeType = returnValue.rstrip()
    #TODO: valid return values should be like: jpeg, x-msvideo, quicktime, mp4, 3gpp (video/...; charset=binary)
    if 'jpeg' in mimeType:
        return('jpeg')
    elif 'quicktime' in mimeType:
        return('quicktime')
    else:
        sys.exit(2)

def getCameraModel(filename, mimeType):
    """Get camera model from file exif data."""
    if mimeType == 'jpeg':
        cmd = 'exiftool -s3 -Model ' + filename
        args = shlex.split(cmd)
        returnValue = subprocess.check_output(args, universal_newlines=True)
        cameraModel = returnValue.rstrip()
        return(cameraModel.replace(" ","_"))
    else:
        pass

def getCreationDate(filename, mimeType):
    """Get unix timestamp creation date."""
    cmd = 'exiftool -s3 -CreateDate ' + filename
    args = shlex.split(cmd)
    returnValue = subprocess.check_output(args, universal_newlines=True)
    createDate = returnValue.rstrip()
    createDate = createDate.replace(" ","")
    return(int(createDate.replace(":","")))

def baseN(num,b,numerals="ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def rotateImage(filename):
    """Rotate image if necessary"""
    cmd = 'jhead -autorot ' + filename
    args = shlex.split(cmd)
    returnValue = subprocess.check_output(args, universal_newlines=True)
    autorotResult = returnValue.rstrip()
    return(autorotResult)


def setFileMode(filename, fileMode):
    """Set filemode"""
    os.chmod(filename, fileMode)

def setModifyDate(filename, creationTimestamp):
    """Set modify date of file"""
    timeStampSeconds = int(time.mktime(time.strptime(str(creationTimestamp), "%Y%m%d%H%M%S")))
    os.utime(filename, (timeStampSeconds, timeStampSeconds))

def moveAndRenameFile(filename, dateString, mimeType, cameraModel, dstimgdir, dstviddir):
    """Rename file and move to destination directory"""
    if mimeType == 'jpeg':
        fileExtension = 'jpg'
        dstDirectory = dstimgdir
    elif mimeType == 'quicktime':
        fileExtension = 'mov'
        dstDirectory = dstviddir
    else:
        return(1)

    if cameraModel:
        cameraModelString = '_' + cameraModel
    else:
        cameraModelString = ''

    newFilename = dstDirectory + dateString + cameraModelString + '.' + fileExtension
    os.rename(filename, newFilename)

def main(argv):
    """Main entry point for the script."""
    srcdir = ''
    dstimgdir = ''
    dstviddir = ''
    try:
      opts, args = getopt.getopt(argv,"hs:i:v:",["srcdir=","dstimgdir=","dstviddir="])
    except getopt.GetoptError:
      logging.warning('%s -s <srcdirectory> -i <dstimgdir> -v <dstviddir>', sys.argv[0])
      sys.exit(2)
    for opt, arg in opts:
      if opt == '-h':
         print(sys.argv[0] , '-s <srcdirectory> -i <dstimagedir> -v <dstvideodir>')
         sys.exit()
      elif opt in ("-s", "--srcdir"):
         srcdir = arg
      elif opt in ("-i", "--dstimgdir"):
         dstimgdir = arg
      elif opt in ("-v", "--dstviddir"):
         dstviddir = arg
    # check directories
    checkdir(srcdir)
    checkdir(dstimgdir)
    checkdir(dstviddir)
    print('Quelle: ', srcdir)
    print('Ziel: ', dstimgdir)
    print('Ziel: ', dstviddir)

    os.chdir(srcdir)
    # for each file
    (_, _, filenames) = os.walk(srcdir).__next__()
    filequeue = deque(filenames)
    while True:
      try:
        filename = filequeue.popleft()
        print('Processing ' + filename + ': ', end="")
        print('mimeType: ', end="")
        mimeType = getMimeType(filename)
        print(mimeType, end="")
        logging.info(mimeType)
        print('created: ', end="")
        creationTimestamp = getCreationDate(filename, mimeType)
        print(creationTimestamp, end="")
        logging.info(creationTimestamp)
        # we don't need the 1st character
        dateString = baseN(creationTimestamp,26)[1:]
        logging.info(dateString)
        # for images only
        cameraModel = ''
        if mimeType == 'jpeg':
            print('cameraModel: ', end="")
            cameraModel = getCameraModel(filename, mimeType)
            print(cameraModel, end="")
            logging.info(cameraModel)
            print('rotating: ', end="")
            rotateAction = rotateImage(filename)
            logging.info(rotateAction)
        
        print('setPermissions. ', end="")
        setFileMode(filename, 0o660)
        print('setTime. ', end="")
        setModifyDate(filename, creationTimestamp)
        print('moveRename. ', end="")
        moveAndRenameFile(filename, dateString, mimeType, cameraModel, dstimgdir, dstviddir)
        print('OK')
        #logging.info(moveFileResult)
      except IndexError:
        break

if __name__ == '__main__':
    main(sys.argv[1:])
