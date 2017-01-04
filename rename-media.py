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

# TODO: don't overwrite target
# TODO: print summary

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
    cmd = 'file -i -b'
    args = shlex.split(cmd)
    args.append((filename))
    returnValue = subprocess.check_output(args, universal_newlines=True)
    mimeType = returnValue.rstrip()
    if 'jpeg' in mimeType:
        return('jpeg')
    elif 'quicktime' in mimeType:
        return('quicktime')
    elif 'mp4' in mimeType:
        return('mp4')
    elif 'x-msvideo' in mimeType:
        return('avi')
    else:
        print('Unknown media format.')
        sys.exit(2)

def getCameraModel(filename, mimeType):
    """Get camera model from file exif data."""
    cmd = 'exiftool -s3 -Model'
    args = shlex.split(cmd)
    args.append((filename))
    returnValue = subprocess.check_output(args, universal_newlines=True)
    cameraModel = returnValue.rstrip()
    cameraModel = cameraModel.replace(" ","_")
    if cameraModel == 'Canon_EOS_550D':
        cameraModel = 'EOS550D'
    return(cameraModel)

def getCreationDate(filename, mimeType):
    """Get unix timestamp creation date."""
    cmd = 'exiftool -s3 -CreateDate'
    args = shlex.split(cmd)
    args.append((filename))
    returnValue = subprocess.check_output(args, universal_newlines=True)
    # in case the year is before 2000
    if returnValue[:2] == '19':
        returnValue = '9999'
    if ':' not in returnValue:
        cmd = 'exiftool -s3 -DateTimeOriginal ' + filename
        args = shlex.split(cmd)
        returnValue = subprocess.check_output(args, universal_newlines=True)
        # in case the year is before 2000
        if returnValue[:2] == '19':
            returnValue = '9999'
    if ':' not in returnValue:
        # in case the year is before 2000
        if returnValue[:2] == '19':
            returnValue = '9999'
        returnValue = '9999'
    createDate = returnValue.rstrip()
    createDate = createDate.replace(" ","")
    return(int(createDate.replace(":","")))

def baseN(num,b,numerals="ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def rotateImage(filename):
    """Rotate image if necessary"""
    cmd = 'jhead -autorot -se'
    args = shlex.split(cmd)
    args.append((filename))
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
    elif mimeType == 'mp4':
        fileExtension = 'mp4'
        dstDirectory = dstviddir
    elif mimeType == 'avi':
        fileExtension = 'avi'
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
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    uid = os.getuid()
    # check for root permissions
    if uid != 0:
        print('You need root permissions to run that script.')
        sys.exit(2)
    # check necessary binaries
    fileBinary = '/usr/bin/file'
    exiftoolBinary = '/usr/bin/exiftool'
    jheadBinary = '/usr/bin/jhead'
    if not os.path.isfile(fileBinary):
        print('Missing file binary.')
        sys.exit(2)
    if not os.path.isfile(exiftoolBinary):
        print('Missing exiftool binary.')
        sys.exit(2)
    if not os.path.isfile(jheadBinary):
        print('Missing jhead binary.')
        sys.exit(2)
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
        print('Processing ' + filename[:10] + ': ', end="")
        print('\tmimeType: ', end="")
        mimeType = getMimeType(filename)
        print(mimeType, end="")
        logging.info(mimeType)
        print('\tcreated: ', end="")
        creationTimestamp = getCreationDate(filename, mimeType)
        if creationTimestamp == 9999:
            print('unknown createDate. ' + FAIL + 'ERROR.' + ENDC)
            continue
        print(creationTimestamp, end="")
        logging.info(creationTimestamp)
        # we don't need the 1st character
        dateString = baseN(creationTimestamp,26)[1:]
        logging.info(dateString)
        # for images only
        cameraModel = ''
        if mimeType == 'jpeg':
            print('\tcameraModel: ', end="")
            cameraModel = getCameraModel(filename, mimeType)
            print(cameraModel, end="")
            logging.info(cameraModel)
            print('\trotating.', end="")
            rotateAction = rotateImage(filename)
            logging.info(rotateAction)
        
        print(' setPermissions. ', end="")
        setFileMode(filename, 0o660)
        print('setTime. ', end="")
        setModifyDate(filename, creationTimestamp)
        print('moveRename. ', end="")
        moveAndRenameFile(filename, dateString, mimeType, cameraModel, dstimgdir, dstviddir)
        print(OKGREEN + 'OK.' + ENDC)
        #logging.info(moveFileResult)
      except IndexError:
        break

if __name__ == '__main__':
    main(sys.argv[1:])
