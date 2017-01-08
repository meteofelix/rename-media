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
from pathlib import Path

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
    if cameraModel == 'NIKON_D3200':
        cameraModel = 'NIK_D3200'
    if cameraModel == 'Canon_EOS_400D_DIGITAL':
        cameraModel = 'EOS400D'
    if cameraModel == 'Canon_IXUS_220HS':
        cameraModel = 'IXUS220HS'
    if len(cameraModel) > 9:
        print('Camera model string too long.')
        sys.exit(2)
    return(cameraModel)

def getCreationDate(filename, mimeType):
    """Get unix timestamp creation date."""
    returnValue = '9999'
    cmd = 'exiftool -s3 -CreateDate'
    args = shlex.split(cmd)
    args.append((filename))
    createDate = subprocess.check_output(args, universal_newlines=True)
    cmd = 'exiftool -s3 -DateTimeOriginal'
    args = shlex.split(cmd)
    args.append((filename))
    dateTimeOriginal = subprocess.check_output(args, universal_newlines=True)
    try:
        if isinstance(createDate,str) and isinstance(dateTimeOrignal,str):
            if createDate != dateTimeOriginal:
                print('createDate not equal to dateTimeOriginal')
                returnValue = '9999'
            else:
                returnValue = createDate
    except NameError:
        pass
    if createDate:
        returnValue = createDate
    if dateTimeOriginal:
        returnValue = dateTimeOriginal
    if ':' not in returnValue:
        returnValue = '9999'
    # in case the year is before 2000
    if returnValue[:2] == '19':
        returnValue = '9999'
    creationDate = returnValue.rstrip()
    creationDate = creationDate.replace(" ","")
    return(int(creationDate.replace(":","")))

def baseN(num,b,numerals="ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def rotateImage(filename):
    """Rotate image if necessary"""
    autorotResult = ''
    cmd = 'exiftool -s3 -m -Orientation'
    args = shlex.split(cmd)
    args.append((filename))
    returnValue = subprocess.check_output(args, universal_newlines=True)
    orientationTagValue = returnValue.rstrip()
    if orientationTagValue:
        # save owner and group
        uid = os.stat(filename).st_uid
        gid = os.stat(filename).st_gid
        cmd = 'jhead -autorot'
        args = shlex.split(cmd)
        args.append((filename))
        returnValue = subprocess.check_output(args, universal_newlines=True)
        autorotResult = returnValue.rstrip()
        # set owner and group
        os.chown(filename, uid, gid)
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

    newFilename = dstDirectory + '/' + dateString + cameraModelString + '.' + fileExtension
    if os.path.isfile(newFilename):
        print('Target already exists.', end="")
        return(0)
    else:
        os.rename(filename, newFilename)
        return(1)

def main(argv):
    """Main entry point for the script."""
    srcdir = ''
    dstimgdir = ''
    dstviddir = ''
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    countImagesProcessed = 0
    countVideosProcessed = 0
    countUnableToProcess = 0
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
    srcdir = str(Path(srcdir).resolve())
    checkdir(dstimgdir)
    dstimgdir = str(Path(dstimgdir).resolve())
    checkdir(dstviddir)
    dstviddir = str(Path(dstviddir).resolve())
    print('Quelle    : ', srcdir)
    print('BilderZiel: ', dstimgdir)
    print('VideoZiel : ', dstviddir)

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
            countUnableToProcess += 1
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
        moveAndRenameFileResult = moveAndRenameFile(filename, dateString, mimeType, cameraModel, dstimgdir, dstviddir)
        if not moveAndRenameFileResult:
            print(FAIL + 'ERROR.' + ENDC)
            countUnableToProcess += 1
            continue
        print(OKGREEN + 'OK.' + ENDC)
        if mimeType == 'jpeg':
            countImagesProcessed += 1
        if mimeType in ('quicktime', 'mp4', 'avi'):
            countVideosProcessed += 1
        #logging.info(moveFileResult)
      except IndexError:
        break
    print('Done renaming ' + str(countImagesProcessed) + ' images and ' + str(countVideosProcessed) + ' videos. ' + str(countUnableToProcess) + ' files could not be renamed.')
if __name__ == '__main__':
    main(sys.argv[1:])
