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
    return(mimeType)

def getCameraModel(filename, mimeType):
    """Get camera model from file exif data."""
    if mimeType == 'image/jpeg; charset=binary':
        cmd = 'exiftool -s3 -Model ' + filename
        args = shlex.split(cmd)
        returnValue = subprocess.check_output(args, universal_newlines=True)
        cameraModel = returnValue.rstrip()
        return(cameraModel.replace(" ","_"))
    else:
        pass

def getCreationDate(filename, mimeType, cameraModel):
    """Get unix timestamp creation date."""
    cmd = 'exiftool -s3 -CreateDate ' + filename
    args = shlex.split(cmd)
    returnValue = subprocess.check_output(args, universal_newlines=True)
    createDate = returnValue.rstrip()
    #return(time.mktime(datetime.datetime.strptime(createDate, "%Y:%m:%d %H:%M:%S").timetuple()))
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

def renameFile(filename, dateString, mimeType, cameraModel):
    """Rename file"""
    if mimeType == 'image/jpeg; charset=binary':
        fileExtension = 'jpg'
    elif mimeType == 'video':
        fileExtension = 'vid'
    else:
        return(1)
    newFilename = dateString + '_' + cameraModel + '.' + fileExtension
    os.rename(filename, newFilename)

def setFileMode(filename, fileMode):
    """Set filemode"""
    os.chmod(filename, fileMode)

def setModifyDate(filename, creationTimestamp):
    """Set modify date of file"""
    timeStampSeconds = int(time.mktime(time.strptime(str(creationTimestamp), "%Y%m%d%H%M%S")))
    os.utime(filename, (timeStampSeconds, timeStampSeconds))

def moveAndRenameFile(filename, dateString, mimeType, cameraModel, dstimgdir, dstviddir):
    """Rename file and move to destination directory"""
    if mimeType == 'image/jpeg; charset=binary':
        fileExtension = 'jpg'
        dstDirectory = dstimgdir
    elif mimeType == 'video':
        fileExtension = 'vid'
        dstDirectory = dstviddir
    else:
        return(1)
    newFilename = dstDirectory + dateString + '_' + cameraModel + '.' + fileExtension
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
        mimeType = getMimeType(filename)
        logging.info(mimeType)
        if mimeType == 'image/jpeg; charset=binary':
            cameraModel = getCameraModel(filename, mimeType)
            logging.info(cameraModel)
            creationTimestamp = getCreationDate(filename, mimeType, cameraModel)
            logging.info(creationTimestamp)
            # we don't need the 1st character
            dateString = baseN(creationTimestamp,26)[1:]
            logging.info(dateString)
            # rotate images only
            if mimeType == 'image/jpeg; charset=binary':
                rotateAction = rotateImage(filename)
                logging.info(rotateAction)
            #renameFile(filename, dateString, mimeType, cameraModel)
            setFileMode(filename, 0o660)
            setModifyDate(filename, creationTimestamp)
            moveAndRenameFile(filename, dateString, mimeType, cameraModel, dstimgdir, dstviddir)
            #logging.info(moveFileResult)
      except IndexError:
        break

# check, ob root rechte
# eine funktion getCreationDate, die unabhaengig vom typ das erstellungsdatum ermittelt
# eine funktion fuer umrechnung in base24
# fuer jede datei in srcdir
#  pruefe dateityp
#   bild
#    erstellungsdatum
#    kameramodell
#    drehen
#    umbenennen+verschieben - ziel nicht ueberschreiben - abbruch
#   video
#    erstellungsdatum lesen
#    umbenennen+verschieben - ziel nicht ueberschreiben - abbruch
#   other
#    ignore

if __name__ == '__main__':
    main(sys.argv[1:])
