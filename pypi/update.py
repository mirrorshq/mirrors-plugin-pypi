#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import sys
import time
import json
import subprocess


def run():
    args = json.loads(sys.argv[1])
    dataDir = args["storage-file"]["data-directory"]

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
        buf += "    tf-nightly-gpu\n"
        buf += "	tf-nightly\n"
        buf += "	tensorflow-io-nightly\n"
        buf += "	tf-nightly-cpu\n"
        buf += "    pyagrum-nightly\n"
        f.write(buf)

    subprocess.run(["/usr/bin/bandersnatch", "-c", "/tmp/bandersnatch.conf", "mirror"])


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
