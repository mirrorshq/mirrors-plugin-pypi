#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import sys
import time
import json
import certifi
import lxml.html
import urllib.request
import subprocess
from datetime import datetime
from datetime import timedelta


def run():
    args = json.loads(sys.argv[1])
    stateDir = args["state-directory"]
    dataDir = args["storage-file"]["data-directory"]

    # big projects
    bpm = BigProjectManager(os.path.join(stateDir, "big-projects.json"))
    print("Find big projects:")
    for p in bpm.getProjectList():
        print("    %s" % (p))
    print("")

    # from https://github.com/tuna/tunasync-scripts/blob/master/pypi.sh
    url = "https://pypi.org"
    with open("/tmp/bandersnatch.conf", "w") as f:
        buf = ""
        buf += "[mirror]\n"
        buf += "directory = %s\n" % (dataDir)
        buf += "master = %s\n" % (url)
        buf += "json = true\n"
        buf += "timeout = 300\n"
        buf += "workers = 5\n"
        buf += "hash-index = false\n"
        buf += "stop-on-error = false\n"
        buf += "delete-packages = true\n"
        buf += "[plugins]\n"
        buf += "enabled =\n"
        buf += "    blacklist_project\n"
        buf += "[blacklist]\n"
        buf += "packages =\n"
        for p in bpm.getProjectList():
            buf += "    %s\n" % (p)
        f.write(buf)

    subprocess.run(["/usr/bin/bandersnatch", "-c", "/tmp/bandersnatch.conf", "mirror"])


class BigProjectManager:

    def __init__(self, recordFile):
        statsUrl = "https://pypi.org/stats"
        now = datetime.now()

        self.recordFile = recordFile
        self.dataObj = self._parseRecordFile()

        # read top 100 projects based on the sum of their packages' sizes
        resp = urllib.request.urlopen(statsUrl, timeout=60, cafile=certifi.where())
        root = lxml.html.parse(resp)
        i = 0
        for tr in root.xpath(".//table/tbody/tr"):
            # igonre the first line
            if i == 0:
                continue
            thTag = tr.xpath("./th")[0]
            self.dataObj[thTag.text] = now
            i += 1

        # remove projects that are not on list for 1 year
        for packageName, lastUpdateTime in self.dataObj.items():
            if now - lastUpdateTime > timedelta(years=1):
                del self.dataObj[packageName]

        self._saveRecordFile(self.dataObj)

    def getProjectList(self):
        return list(self.dataObj.keys())

    def _parseRecordFile(self):
        if os.path.exists(self.recordFile):
            with open(self.recordFile, "r") as f:
                return json.load(f)
        return {}

    def _saveRecordFile(self, dataObj):
        with open(self.recordFile, "w") as f:
            json.dump(f, dataObj)


class Util:

    @staticmethod
    def shellCall(cmd):
        # call command with shell to execute backstage job
        # scenarios are the same as FmUtil.cmdCall

        ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             shell=True, universal_newlines=True)
        if ret.returncode > 128:
            # for scenario 1, caller's signal handler has the oppotunity to get executed during sleep
            time.sleep(1.0)
        if ret.returncode != 0:
            ret.check_returncode()
        return ret.stdout.rstrip()


if __name__ == "__main__":
    run()
