#!/usr/bin/env python
import tempfile
import os
import sys
import dateutil.parser 
import datetime
from subprocess import call
import sqlite3
import colorama


def get_remote_ip():
    line = os.environ.get('SSH_CONNECTION', '')
    space = line.find(' ')
    if space != -1:
        return line[:space]
    print 'warning: remote ip could not be read'
    return ''


def get_hostname():
    import platform
    return platform.node()


def get_message():
    editor_command = os.environ.get('EDITOR', 'vim')
    initial_message = ""
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
        tmp.write(initial_message)
        tmp.flush()
        call([editor_command, tmp.name])
        tmp.seek(0)
        return tmp.read().strip()


def get_db():
    dbdir = os.path.join(os.path.expanduser("~"), '.vinotedb')
    conn = sqlite3.connect(dbdir)

    with conn:
        conn.execute('''create table if not exists notes
(date text, hostname text, ip text, message text)''')
    return conn


def add_note():
    db = get_db()
    new_msg = get_message()
    if len(new_msg) == 0:
        print 'Empty message not added'
        return
    
    current_date = datetime.datetime.now().isoformat()
    with db:
        db.execute('insert into notes (date, hostname, ip, message) values (?, ?, ?, ?)',
                   (current_date, get_hostname(), get_remote_ip(), new_msg))
    print 'OK'

    
def format_week(now, then):
    
    now -= datetime.timedelta(days=now.isocalendar()[2])
    then -= datetime.timedelta(days=then.isocalendar()[2])
    
    delta = now - then
    weeks = int(round(delta.days / 7.0))

    if weeks == 0:
        return 'this week'
    if weeks == 1:
        return 'last week'
    
    return '%g weeks ago' % weeks


def format_day(now, then):

    def get_year_and_week_number(d):
        y, w, _ = d.isocalendar()
        return y, w

    def weekday():
        _, _, dw = then.isocalendar()
        return ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][(6+dw) % 7]
    
    if get_year_and_week_number(now) != get_year_and_week_number(then):
        return weekday()

    day_delta = now.date() - then.date()
    if day_delta.days == 0:
        return 'today'
    if day_delta.days == 1:
        return 'yesterday'

    return weekday()


def show_notes():
    from colorama import Fore

    db = get_db()
    now = datetime.datetime.now()

    last_week_str = ''
    last_day_str = ''

    for date, hostname, ip, message in db.execute('select date, hostname, ip, message from notes order by date'):
        week_str = format_week(now, dateutil.parser.parse(date))
        day_str = format_day(now, dateutil.parser.parse(date))
        
        if (week_str != last_week_str or day_str != last_day_str) and last_week_str != '':
            print
        if week_str != last_week_str:
            print Fore.YELLOW + week_str + Fore.RESET
            last_week_str = week_str
        if day_str != last_day_str:
            print Fore.GREEN + day_str + Fore.RESET
            last_day_str = day_str

        print Fore.RED + '> ' + Fore.RESET + message.encode('utf-8')
    print


if __name__ == '__main__':
    colorama.init()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'list':
            show_notes()
        else:
            add_note()
    finally:
        colorama.deinit()
