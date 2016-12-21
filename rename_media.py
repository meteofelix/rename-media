#!/usr/bin/python3
"""Rename files according to creation timestamp"""
import sys
import os
import getopt
import logging
import subprocess
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

def getCameraModel(filename, mimeType):
    """Get camera model from file exif data."""
    cmd = "exiftool -s3 -Model 'filename'"
    args = shlex.split(cmd)
    returnValue = subprocess.check_output(args, universal_newlines=True)
    cameraModel = returnValue.rstrip()
    print(cameraModel)
    pass

def getCreationDate(filename, mimeType, cameraModel):
    """Get unix timestamp creation date."""
    pass

def base26(creationTimestamp):
    """Convert unix timestamp to base26 string."""
    pass

def rotateImage(filename):
    """Rotate image if necessary"""
    pass

def renameFile(filename, dateString, cameraModel):
    """Rename file"""
    pass

def setFileMode(filename, fileMode):
    """Set filemode"""
    pass

def setModifyDate(filename, creationTimestamp):
    """Set modify date of file"""
    pass

def moveFile(filename, mimeType, dstimgdir, dstviddir):
    """Move file to destination directory"""
    pass

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
    (_, _, filenames) = os.walk(srcdir).next()
    filequeue = deque(filenames)
    while True:
      try:
        filename = filequeue.popleft()
        # dateityp
        # nein mimeType = magic.from_file(filename, mime=True)
        file -i -b SOELSCWCL_iPhone_6.jpg
        logging.info(mimeType)
        cameraModel = getCameraModel(filename, mimeType)
        logging.info(cameraModel)
        creationTimestamp = getCreationDate(filename, mimeType, cameraModel)
        logging.info(creationTimestamp)
        dateString = base26(creationTimestamp)
        logging.info(dateString)
        rotateAction = rotateImage(filename)
        logging.info(rotateAction)
        renameResult = renameFile(filename, dateString, cameraModel)
        logging.info(renameResult)
        setFileModeResult = setFileMode(filename, '660')
        logging.info(setFileModeResult)
        setModifyDateResult = setModifyDate(filename, creationTimestamp)
        logging.info(setModifyDateResult)
        moveFileResult = moveFile(filename, mimeType, dstimgdir, dstviddir)
        logging.info(moveFileResult)
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
