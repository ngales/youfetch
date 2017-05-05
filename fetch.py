#! /usr/bin/env python

#
# youmail bulk voicemail downloader
#

# as of 2017-03, field filtering is only available when the API is returning XML, so use XML responses over JSON
# ElementTree is not secure against maliciously constructed XML data, so be careful if reusing this code later in e.g. server context

import argparse
import urllib2
import sys
try:
  import xml.etree.cElementTree as ElementTree
except ImportError:
  import xml.etree.ElementTree as ElementTree
import os

# GLOBAL CONFIG
API_BASE = "https://api.youmail.com/api/v4/"
USER_AGENT = "Mozilla/5.0"
OUTPUT_DIR = "data"
DATA_FORMAT = "MP3"

def doRequest(url):
  request = urllib2.Request(url, headers={'User-Agent' : USER_AGENT})
  try:
    return urllib2.urlopen(request)
  except ValueError, e:
    print "unable to do " + str(request) + ", " + str(e)
    return None
  except urllib2.HTTPError, e:
    # TODO: more specific error messages given HTTPError, e.g. InvalidPIN
    print "unable to do " + str(request) + ", " + str(e)
    return None
  except urllib2.URLError, e:
    print "unable to do " + str(request) + ", " + str(e)
    return None

def getAuthToken(user, password):
  url = API_BASE + "authenticate/" + str(user) + "/" + str(password)
  response = doRequest(url)
  if response is None:
    return None
  content = response.read()
  return ElementTree.fromstring(content).text

def printFolderInfo(authToken):
  url = API_BASE + "messagebox/folders/" + "?auth=" + str(authToken)
  response = doRequest(url)
  tree = ElementTree.fromstring(response.read())
  for folder in tree.iter('folder'):
    print folder.find('name').text + "\t" + folder.find('visibleEntryCount').text

def getVoicemail(authToken):
  url = API_BASE + "messagebox/entry/query" + "?auth=" + str(authToken) + "&folderId=-1" + "&deleteType=0" + "&dataFormat=" + str(DATA_FORMAT) + "&securedDataUrl=true" + "&pageLength=1000" + "&fields=id,created,source,status,length,folderId,createSource,callerName,organization,phonebookSourceType,messageDataUrl"
  print "vm api request url: " + str(url)
  return doRequest(url)

def createDirIfMissing(directoryPath):
  if not os.path.exists(directoryPath):
    os.makedirs(directoryPath)

def downloadFile(url, path):
  response = doRequest(url)
  if response is None:
    print "unable to download file from " + str(url)
    return
  save(response.read(), path)

def save(content, path):
  f = open(path, 'wb')
  f.write(content)
  f.close()
  
if __name__ != '__main__':
  exit
  
# process CLI arguments
parser = argparse.ArgumentParser(description='youmail voicemail bulk downloader.')
parser.add_argument('user', help='user for authentication, either username or phone number.', metavar='USER')
parser.add_argument('password', help='password for authentication, a numeric PIN.', metavar='PASSWORD')
# TODO: make above non-required, and instead require EITHER user + pass OR the authToken itself
args = parser.parse_args()
  
authToken = getAuthToken(args.user, args.password)
if authToken is None:
  sys.exit("unable to authenticate, exiting")
print authToken

printFolderInfo(authToken)

response = getVoicemail(authToken)
content = response.read()

createDirIfMissing(OUTPUT_DIR)
save(content, OUTPUT_DIR + "/response.xml")

tree = ElementTree.fromstring(content)
for entry in tree.iter('entry'):
  #for child in entry:
  #  print child.tag + "\t" + child.text
  filename = str(entry.find('callerName').text) + "_" + str(entry.find('source').text) + "_" + str(entry.find('created').text)
  print "downloading " + str(filename)
  # TODO: convert epoch timestamp to readable local time
  # TODO: output files in folders according to their Youmail folders
  downloadFile(entry.find('messageDataUrl').text, OUTPUT_DIR + "/" + filename + "." + DATA_FORMAT)
