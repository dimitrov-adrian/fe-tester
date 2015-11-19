#!/usr/bin/env python

"""
fe-tester.py v0.1

Copyright (c) 2015, e01 <dimitrov.adrian@gmail.com>

fe-tester.py free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

fe-tester.py is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
fe-tester. If not, see http://www.gnu.org/licenses/.
"""

import argparse
import os
import subprocess
import difflib
import filecmp
import time
import hashlib
from subprocess import call
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display


# General
CONF_URL_FILE_PATH                  = 'urls.txt'
CONF_REPORTS_DIRECTORY              = 'reports'
CONF_REPORTS_DIRECTORY_ARCHIVE      = CONF_REPORTS_DIRECTORY + '/archive'
CONF_REPORTS_DIRECTORY_DIFF         = CONF_REPORTS_DIRECTORY + '/diff'
CONF_CLEAR_OLD_DIFFS                = True

# Image comparing
CONF_SCREENSHOT_COMPARE_FUZZ        = '2%'

# Browser setup
CONF_BROWSER_ENGINE                 = 'chrome'
CONF_BROWSER_DELAY                  = 0.8
CONF_BROWSER_VIEWPORT_AUTOSIZE      = False
CONF_BROWSER_VIEWPORT_WIDTH         = '1280'
CONF_BROWSER_VIEWPORT_HEIGHT        = '4096'


##
# Application code begin here
#

# Prepare Test Directories
def prepareDirectories(report = ''):
    global CONF_REPORTS_DIRECTORY
    global CONF_REPORTS_DIRECTORY_ARCHIVE
    global CONF_REPORTS_DIRECTORY_DIFF

    if report:
        if not os.path.isdir(CONF_REPORTS_DIRECTORY_ARCHIVE + '/' + report):
            os.mkdir(CONF_REPORTS_DIRECTORY_ARCHIVE + '/' + report)
        return CONF_REPORTS_DIRECTORY_ARCHIVE + '/' + report

    else:
        if not os.path.isdir(CONF_REPORTS_DIRECTORY):
            os.makedirs(CONF_REPORTS_DIRECTORY)

        if not os.path.isdir(CONF_REPORTS_DIRECTORY_ARCHIVE):
            os.mkdir(CONF_REPORTS_DIRECTORY_ARCHIVE)

        if not os.path.isdir(CONF_REPORTS_DIRECTORY_DIFF):
            os.mkdir(CONF_REPORTS_DIRECTORY_DIFF)

    return CONF_REPORTS_DIRECTORY


# Clear old diffs
def clearDiffs():
    for f in os.listdir(CONF_REPORTS_DIRECTORY_DIFF):
        os.remove(CONF_REPORTS_DIRECTORY_DIFF + '/' + f);
    return True


# Simple method to increase the last report number
def getReportID():
    global CONF_REPORTS_DIRECTORY_ARCHIVE
    m = 0
    for n in os.listdir(CONF_REPORTS_DIRECTORY_ARCHIVE):
        if (n.isdigit() and int(n) >= m):
            m = int(n)
    m += 1
    return str(m)


# Main QA tester worker
class testingBrowser:

    # Do initializations.
    def __init__(self, appOpts):

        self.appOpts = appOpts

        if self.appOpts.report:
            self.reportID = self.appOpts.report
        else:
            self.reportID = getReportID()

        self.reportsDirectory = prepareDirectories(self.reportID)
        self._display = Display(visible=0, size=(CONF_BROWSER_VIEWPORT_WIDTH, CONF_BROWSER_VIEWPORT_HEIGHT))
        self._display.start()

        if CONF_BROWSER_ENGINE == 'firefox':
            self._driver = webdriver.Firefox()
        else:
            #self._webdriver_options = webdriver.ChromeOptions()
            #self._webdriver_options.add_argument('--user-agent=')
            #self._driver = webdriver.Chrome(chrome_options=self._webdriver_options)
            self._driver = webdriver.Chrome();

        self._driver.maximize_window()

        self._browserLogFile = open(self.reportsDirectory + '/browser-log.txt', 'w')

    # Clear app.
    def __del__(self):
        self.shutDown()

    # Force object shutdown
    def shutDown(self):
        if self._browserLogFile:
            self._browserLogFile.close()
        self._driver.close()
        self._driver.quit()
        self._display.stop()

    # Handle Browser logs.
    def _logBrowserLog(self, url):
        if self._driver.get_log('browser'):
            self._browserLogFile.write(url)
        return True

    # Make Browser screenshot
    def _makeScreenShot(self, fileName):

        if CONF_BROWSER_VIEWPORT_AUTOSIZE:
            width = self._driver.execute_script('return document.documentElement.offsetWidth')
            height = self._driver.execute_script('return document.documentElement.offsetHeight')
            self._driver.set_window_size(width, height)

        self._driver.execute_script('document.documentElement.style.overflow="hidden"')

        time.sleep(CONF_BROWSER_DELAY)
        self._driver.save_screenshot(self.reportsDirectory + '/' + fileName)

        return fileName

    # Make screenshot comparsion diffs.
    def _doScreenshotReport(self, fileName):

        lastReportID = str(int(self.reportID)-1)
        curRepFilePath = CONF_REPORTS_DIRECTORY_ARCHIVE + '/' + self.reportID + '/' + fileName
        prevRepFilePath = CONF_REPORTS_DIRECTORY_ARCHIVE + '/' + lastReportID + '/' + fileName
        cmpRepFilePath = CONF_REPORTS_DIRECTORY_DIFF + '/' + lastReportID + ':' + self.reportID + '_' + fileName

        if not os.path.isfile(prevRepFilePath) or not os.path.isfile(curRepFilePath):
            return False

        # Simple check for similarity
        if not filecmp.cmp(curRepFilePath, prevRepFilePath):
            callCMD = ['compare']
            if not CONF_BROWSER_VIEWPORT_AUTOSIZE:
                callCMD.append('-subimage-search')
            if CONF_SCREENSHOT_COMPARE_FUZZ:
                callCMD.extend(['-fuzz', CONF_SCREENSHOT_COMPARE_FUZZ])
            callCMD.extend(['-metric', 'RMSE'])
            callCMD.extend([prevRepFilePath, curRepFilePath, cmpRepFilePath])
            call(callCMD, stdout=open(os.devnull, 'wb'), stderr=subprocess.STDOUT)

        return True

    # Make browser log diff
    def diffBrowserLog(self):
        fileName = 'browser-log.txt'
        lastReportID = str(int(self.reportID)-1)
        curRepFilePath = CONF_REPORTS_DIRECTORY_ARCHIVE + '/' + self.reportID + '/' + fileName
        prevRepFilePath = CONF_REPORTS_DIRECTORY_ARCHIVE + '/' + lastReportID + '/' + fileName
        cmpRepFilePath = CONF_REPORTS_DIRECTORY_DIFF + '/' + lastReportID + ':' + self.reportID + '_' + ('.').join(fileName.split('.')[:-1]) + '.html'

        # Close browser log file
        if self._browserLogFile:
            self._browserLogFile.close()
            self._browserLogFile = None

        if os.path.isfile(prevRepFilePath) and os.path.isfile(curRepFilePath) and filecmp.cmp(prevRepFilePath, curRepFilePath):
            return False

        if os.path.isfile(prevRepFilePath):
            fromLines = open(prevRepFilePath, 'U').readlines()
        else:
            fromLines = []

        if os.path.isfile(curRepFilePath):
            toLines = open(curRepFilePath, 'U').readlines()
        else:
            toLines = []

        if (not fromLines and not toLines):
            return False

        diff = difflib.HtmlDiff().make_file(fromLines, toLines)
        fh = open(cmpRepFilePath, 'w')
        fh.write(diff)
        fh.close()

        return True

    def doQA(self, url):
        urlHash = hashlib.md5()
        urlHash.update(url)

        self._driver.get(url)

        if not self.appOpts.noscreenshot:
            fileName = 'screen-' + urlHash.hexdigest() + '.png'
            self._makeScreenShot(fileName);

            if not self.appOpts.skipdiff:
                self._doScreenshotReport(fileName)

        self._logBrowserLog(url)


# URL iterators
def urlIterator(args, urls):

    leyaTheSlave = testingBrowser(args)
    for line in urls:
        print '* Check ' + line
        leyaTheSlave.doQA(line)

    if not args.skipdiff:
        leyaTheSlave.diffBrowserLog()

    return True


# Main
def __main__():

    global CONF_REPORTS_DIRECTORY
    global CONF_REPORTS_DIRECTORY_ARCHIVE
    global CONF_REPORTS_DIRECTORY_DIFF
    global CONF_BROWSER_ENGINE
    global CONF_CLEAR_OLD_DIFFS
    global CONF_BROWSER_VIEWPORT_AUTOSIZE
    global CONF_BROWSER_VIEWPORT_WIDTH
    global CONF_BROWSER_VIEWPORT_HEIGHT

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,epilog="Version 0.1\nCheckout project repo at https://github.com/dimitrov-adrian/fe-tester")

    parser.add_argument('-d', '--outputdir', help='Change output directory for this test, default: ' + CONF_REPORTS_DIRECTORY)
    parser.add_argument('-r', '--report', help='Force the report ID to given numner')
    parser.add_argument('-g', '--clearolddiff', help='Clear old diffs (yes|no), default: ' + ('yes' if CONF_CLEAR_OLD_DIFFS else 'no'))
    parser.add_argument('-s', '--skipdiff', action='count', default=0, help='Skip making diffs for this time, useful with -r')
    parser.add_argument('-t', '--delay', type=float, help='Delay after URL is open and making screenshot and JSerror handling (float)')
    parser.add_argument('-b', '--browser', default=CONF_BROWSER_ENGINE,help='Set browser engine (firefox, chrome)')
    parser.add_argument('-n', '--noscreenshot', action='count', default=0, help='Do not make screenshot of tests and screenshot diffs')
    parser.add_argument('-a', '--autosize', help='Make browser viewport to page viewport (yes|no), default: ' + ('yes' if CONF_BROWSER_VIEWPORT_AUTOSIZE else 'no'))
    parser.add_argument('-x', '--width', type=int, default=CONF_BROWSER_VIEWPORT_WIDTH, help='Browser viewport width, default: ' + CONF_BROWSER_VIEWPORT_WIDTH)
    parser.add_argument('-y', '--height', type=int, default=CONF_BROWSER_VIEWPORT_HEIGHT, help='Browser viewport height, default: ' + CONF_BROWSER_VIEWPORT_HEIGHT)

    args = parser.parse_args()

    if args.outputdir:
        CONF_REPORTS_DIRECTORY = args.outputdir
        CONF_REPORTS_DIRECTORY_ARCHIVE = CONF_REPORTS_DIRECTORY + '/archive'
        CONF_REPORTS_DIRECTORY_DIFF = CONF_REPORTS_DIRECTORY + '/diff'

    if args.clearolddiff:
        CONF_CLEAR_OLD_DIFFS = (True if args.clearolddiff.upper() == 'YES' else False)

    if args.autosize:
        CONF_BROWSER_VIEWPORT_AUTOSIZE = (True if args.autosize.upper() == 'YES' else False)

    if args.width:
        CONF_BROWSER_VIEWPORT_WIDTH = args.width

    if args.height:
        CONF_BROWSER_VIEWPORT_HEIGHT = args.height

    if args.browser:
        CONF_BROWSER_ENGINE = args.browser

    if args.delay:
        CONF_BROWSER_DELAY = args.delay


    # Checks
    if not os.path.isfile(CONF_URL_FILE_PATH):
        print 'URLs file not exists.'
        return False

    # Do the cycle
    urlsRaw = open(CONF_URL_FILE_PATH, 'U').readlines();
    urls = []
    for line in urlsRaw:
        line = line.strip()
        if (not line.startswith('#') and line):
            urls.append(line)

    if len(urls) < 1:
        print 'No URLs to check'
        return False

    prepareDirectories()

    if CONF_CLEAR_OLD_DIFFS:
        clearDiffs()

    print 'Start testing ' + str(len(urls)) + ' URLs in ' + CONF_BROWSER_ENGINE + ' as ReportID ' + (args.report if args.report else getReportID())
    urlIterator(args, urls);
    print 'Done'

# Begin
__main__()
