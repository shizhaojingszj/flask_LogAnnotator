# -*- coding: utf-8 -*-
from flask import (render_template, jsonify, request)
from app import app, db

from models import (LogFile, LogEntry)

import os, re, datetime
import hashlib

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

@app.route("/summaryFile/<int:logfile_id>")
def summaryFile(logfile_id):
    this_file = LogFile.query.get(logfile_id)
    all_entries = this_file.entries

    return render_template("logfile_entries_summary.html",
                           title="ALL entries for file %s" % this_file.name,
                           all_entries = all_entries,
                           filename = this_file.name,
                           fileid = logfile_id)

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
