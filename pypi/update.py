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
    bigProjectList = _getBigProjectList(os.path.join(stateDir, "big-projects.json"))
    print("Find %d big projects:" % len(bigProjectList))
    for p in bigProjectList:
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
        for p in bigProjectList:
            buf += "    %s\n" % (p)
        f.write(buf)

    # it sucks that aiohttp depends on "~/.netrc", so we disable it
    subprocess.run(["/usr/bin/bandersnatch", "-c", "/tmp/bandersnatch.conf", "mirror"], env={"NETRC": "/dev/null"})


def _getBigProjectList(recordFile):
    statsUrl = "https://pypi.org/stats"
    now = datetime.now()

    # read data
    dataObj = dict()
    if os.path.exists(recordFile):
        with open(recordFile, "r") as f:
            buf = f.read()
            if buf != "":
                dataObj = json.loads(buf)
                for k in dataObj:
                    dataObj[k] = datetime.strptime(dataObj[k], "%Y.%m.%d")

    # read top 100 projects based on the sum of their packages' sizes
    resp = urllib.request.urlopen(statsUrl, timeout=60, cafile=certifi.where())
    root = lxml.html.parse(resp)
    for tr in root.xpath(".//table/tbody/tr")[1:]:      # ignore the first line
        thTag = tr.xpath("./th")[0]
        dataObj[thTag.text] = now

    # remove projects that are not on list for 1 year
    for packageName, lastUpdateTime in dataObj.items():
        if now - lastUpdateTime > timedelta(days=365):
            del dataObj[packageName]

    # save data
    with open(recordFile, "w") as f:
        for k in dataObj:
            dataObj[k] = dataObj[k].strftime("%Y.%m.%d")
        json.dump(dataObj, f)

    # return value
    return list(dataObj.keys())


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
