# -*- coding: utf-8 -*-
from __future__ import print_function

from flask import (render_template, jsonify, request)
from app import app, db

from models import (LogFile, LogEntry)

import os, re, datetime, shlex, copy
from io import StringIO
import hashlib
from collections import OrderedDict

from functools import partial

@app.route('/')
def homepage():
    return render_template("layout.html", title="LogAnnotator")

@app.route("/updateAnnotate/<int:entry_id>/", methods=['POST'])
def updateAnnotate(entry_id):
    '''
    this view function is not AJAX
    '''
    this_entry = LogEntry.query.get(entry_id)
    annotate = request.form['annotate']  # magically get annotate.value
    this_entry.annotate = annotate
    db.session.commit()
    return ""

def beautiful_shell(line):
    items = shlex.split(line)
    text = StringIO()
    appendix = u' \\'
    prefix = u'\t'
    if len(items) <= 2:
        return u" ".join(items)
    else:
        print(u" ".join(items[:2]) + appendix, file=text)
    temp = []
    olditems = copy.deepcopy(items[2:])
    for n, item in enumerate(items[2:]):
        if n == len(olditems) - 1:
            if len(temp) == 0:
                print(prefix+item, file=text)
            else:
                temp.append(item)
                print(prefix+" ".join(temp), file=text)
            break
        if item.startswith("-"):
            if olditems[n+1].startswith("-"):
                print(prefix+item+appendix, file=text)
                temp = []
                continue
            else:
                temp.append(item)
        else:
            if len(temp) > 0:
                temp.append(item)
                print(prefix+" ".join(temp)+appendix, file=text)
                temp = []
            else:
                print(prefix+item+appendix, file=text)

    return '<pre><code class="bash">{}</code></pre>'.format(text.getvalue())

SECTION_PAT = re.compile("# \[(?P<section_name>[A-Z]+)\]")
DELETE_PAT = re.compile("(rm( -\w+)?|unlink) (?P<path>/[\w./*]+)")
TOUCH_PAT = re.compile("touch (?P<path>/[\w./*]+)")
OK_PAT = re.compile(".*(?P<is_good>.ok)$")
SUCCESS_PAT = re.compile(".*(?P<is_good>.success|.final)$")
RUN_PAT = re.compile(".*(?P<is_run>.run)$")
LN_PAT = re.compile("(ln) (?P<path>/[\w./*]+)")
def dispatch_colorize_body(thing):
    thing = thing.strip()
    ### header
    if SECTION_PAT.match(thing):
        return '<b style="color:blue;">{}</b>'.format(thing)
    ### delete a file
    m = DELETE_PAT.match(thing)
    if m:
        m2 = OK_PAT.match(m.groupdict()['path'])
        if m2:
            return '<span class="rm">{}<span style="color:green">' \
                '{}</span></span>'.format(thing[:-len(m2.groupdict()['is_good'])],
                                          thing[-len(m2.groupdict()['is_good']):])  # green indicates an ok
        m3 = RUN_PAT.match(m.groupdict()['path'])
        if m3:
            return '<span class="rm">{}<span style="color:cyan">' \
                '{}</span></span>'.format(thing[:-len(m3.groupdict()['is_run'])],
                                          thing[-len(m3.groupdict()['is_run']):])  # cyan indicates an intermediate file
        return '<span class="rm">{}</span>'.format(thing)  # red indicates an deletion
    ### create a file
    m = TOUCH_PAT.match(thing)
    if m:
        m2 = SUCCESS_PAT.match(m.groupdict()['path'])
        if m2:
            return '<span class="touch">{}<span style="color:green;">' \
                '{}</span></span>'.format(thing[:-len(m2.groupdict()['is_good'])],
                                          thing[-len(m2.groupdict()['is_good']):]) # green indicates a final
        m3 = RUN_PAT.match(m.groupdict()['path'])
        if m3:
            return '<span class="rm">{}<span style="color:cyan">' \
                '{}</span></span>'.format(thing[:-len(m3.groupdict()['is_run'])],
                                          thing[-len(m3.groupdict()['is_run']):])  # cyan indicates an intermediate file
        return '<span class="touch">{}</span>'.format(thing)
    ### hardlink a file (rename a file)
    m = LN_PAT.match(thing)
    if m:
        return '<span class="ln">{}</span>'.format(thing)
    ## use shlex to parse the line
    thing = beautiful_shell(thing)
    return thing

def get_all_sections(entries):
    result = OrderedDict()
    for entry in entries:
        body = entry.body.strip()
        if SECTION_PAT.match(body):
            if body not in result:
                result[body] = ['<a href="#{}">#{}</a>'.format(entry.line_num, entry.line_num)]
            else:
                result[body].append('<a href="#{}">#{}</a>'.format(entry.line_num, entry.line_num))
    return [(key, len(value), " ".join(value)) for (key, value) in result.items()]


@app.route("/summaryFile/<int:logfile_id>")
def summaryFile(logfile_id):
    this_file = LogFile.query.get(logfile_id)
    all_entries = this_file.entries

    return render_template("logfile_entries_summary.html",
                           title="ALL entries for file %s" % this_file.name,
                           all_entries = all_entries,
                           pipelines = [x for x in all_entries if x.body == "# [RUNPIPELINE]"],
                           sections = get_all_sections(all_entries),
                           filename = this_file.name,
                           fileid = logfile_id,
                           body_colorizer = dispatch_colorize_body)


@app.route("/summaryFile/all")
def summaryFileAll():
    files = LogFile.query.all()
    return render_template("logfile_list.html",
                           title="ALL files",
                           all_files = files)

## |2017-06-16 10:28:44|...
##  datetime.datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
LOG_PAT = re.compile(r"\|(?P<timestamp>.*?)\|(?P<body>.*)")
def read_logfile_entries(filename, file_id):
    entries=[]
    with open(filename) as IN:
        for n, line in enumerate(IN, 1):
            line = line.strip()
            if not line:
                continue
            m = LOG_PAT.match(line)
            if m:
                timestamp =  datetime.datetime.strptime(m.groupdict()['timestamp'], "%Y-%m-%d %H:%M:%S")
                entry = LogEntry(line_num = n,
                                 timestamp = timestamp,
                                 body = m.groupdict()['body'],
                                 annotate = "",
                                 logfile_id = file_id)
                entries.append(entry)
    if not entries:
        print("entries is", entries)
    return entries

@app.route("/addFile")
def addFile():
    filename = request.args.get("filename")
    rebuild = request.args.get("rebuild")
    verbose = request.args.get("verbose")
    if filename:
        if not os.path.isfile(filename):
            print("Cannot find file %s" % filename)
            return jsonify({"res": "-1"})

        m = hashlib.md5()
        with open(filename, 'rb') as IN:
            m.update(IN.read())
        file_md5 = m.hexdigest()
        logfile = LogFile(name=filename, hash=file_md5)
        ## if logfile has already upload to the server, don't do it again
        old_in_db = LogFile.query.filter(LogFile.hash == file_md5).first()
        if verbose:
            print("old_in_db is", old_in_db)
            print("rebuild is", rebuild)
        if old_in_db:
            if rebuild != "yes":
                logfile = old_in_db
                return jsonify({"res": logfile.id})
            else:
                # if rebuild == "yes"
                for entry in old_in_db.entries:
                    db.session.delete(entry)
                db.session.delete(old_in_db)
                db.session.commit()
        db.session.add(logfile)
        db.session.commit()

        # Now add all the entries
        all_entries = read_logfile_entries(filename, logfile.id)
        if verbose:
            print("all_entries is", all_entries)
        db.session.add_all(all_entries)
        db.session.commit()

        return jsonify({"res": logfile.id})
