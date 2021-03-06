#! /usr/bin/env python

import re
import sets
import sqlite3
import textwrap
import git
import sys


def getappids(curs):
    rows = curs.execute("SELECT * FROM store_app WHERE href_name='matlab'")
    matlabid = rows.fetchone()['id']
    rows = curs.execute("SELECT * FROM store_app WHERE \
            href_name='matlab-toolboxes'")
    toolboxesid = rows.fetchone()['id']
    return (matlabid, toolboxesid)


def getuserids(curs, ids):
    userids = {'matlab': [], 'toolboxes': []}
    rows = curs.execute("SELECT * FROM store_user_apps WHERE \
            app_id=%s" % ids[0])
    apps = rows.fetchall()
    for row in apps:
        userids['matlab'].append(row['user_id'])
    rows = curs.execute("SELECT * FROM store_user_apps WHERE \
            app_id=%s" % ids[1])
    apps = rows.fetchall()
    for row in apps:
        userids['toolboxes'].append(row['user_id'])
    return userids


def getusers(curs, userids):
    matlabusers = []
    toolboxusers = []
    matlabuserset = sets.Set(userids['matlab'])
    toolboxuserset = sets.Set(userids['toolboxes'])
    matlabuserset.difference_update(toolboxuserset)
    for i in matlabuserset:
        row = curs.execute("SELECT * FROM store_user WHERE id=%s" % i)
        matlabusers.append(row.fetchone()['name'])
    for i in toolboxuserset:
        row = curs.execute("SELECT * FROM store_user WHERE id=%s" % i)
        toolboxusers.append(row.fetchone()['name'])
    return {'matlab': matlabusers, 'toolboxes': toolboxusers}


def outputfile(db_filename):
    lines = []
    conn = sqlite3.connect(db_filename)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    users = getusers(curs, getuserids(curs, getappids(curs)))
    curs.close()
    prevmatlab = sets.Set()
    prevtoolboxes = sets.Set()
    with open('/usr/local/matlab/src/matlab.opt', 'r') as fileh:
        for line in fileh:
            if re.match("GROUP matlabonly", line):
                prevmatlab = sets.Set([x.strip() for x in line.split(" ")[2:]])
            elif re.match("GROUP toolboxes", line):
                prevtoolboxes = sets.Set([x.strip() for x in line.split(" ")[2:]])
    matlabline = "GROUP matlabonly " + " ".join(users['matlab'])
    toolboxesline = "GROUP toolboxes " + " ".join(users['toolboxes'])
    for x in textwrap.wrap(matlabline):
        lines.append(x)
    for x in textwrap.wrap(toolboxesline):
        lines.append(x)
    lines.append("INCLUDEALL        GROUP toolboxes")
    lines.append("INCLUDE MATLAB    GROUP matlabonly")
    outlines = [x + "\n" for x in lines]
    with open('/usr/local/matlab/src/matlab.opt', 'w') as fileh:
        fileh.writelines(outlines)
    madded = sets.Set(users['matlab']).difference(prevmatlab)
    tadded = sets.Set(users['toolboxes']).difference(prevtoolboxes)
    mremoved = prevmatlab.difference(users['matlab'])
    tremoved = prevtoolboxes.difference(users['toolboxes'])
    repo = git.Repo("/usr/local/matlab/src")
    index = repo.index
    index.add(['/usr/local/matlab/src/matlab.opt'])
    commitmsg = []
    if len(madded) > 0:
        commitmsg.append("Added " + " ".join(madded) + " to matlabonly.")
    if len(tadded) > 0:
        commitmsg.append("Added " + " ".join(tadded) + " to toolboxes.")
    if len(mremoved) > 0:
        commitmsg.append("Removed " + " ".join(mremoved) + " from matlabonly.")
    if len(tremoved) > 0:
        commitmsg.append("Removed " + " ".join(tremoved) + " from toolboxes.")
    index.commit(" ".join(commitmsg))  # Need to set a remote!!!

if __name__ == '__main__':
    outputfile(sys.argv[1])
