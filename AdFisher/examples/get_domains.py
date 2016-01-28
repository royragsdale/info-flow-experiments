
import os
import sys
import json
from collections import namedtuple
import csv
import operator
from urlparse import urlparse

def load_ads_from_json(log_name,session):
    # The save file name format is "adb_logfile.session.json
    dirname = os.path.dirname(log_name)
    base=os.path.splitext(os.path.basename(log_name))[0][4:]
    json_name  = base+"."+session+".json" 
    json_file = os.path.join(dirname,json_name)
    with open(json_file, 'r') as infile:
        raw_ad_lines = json.load(infile)
    
    print("loaded {} lines from session: {}".format(len(raw_ad_lines),session))

    ad_lines =[]
    for line in raw_ad_lines:
        # parse line back into a named tuple, properly encoding to utf-8
        utf8_line  = map(lambda s: s.encode('utf-8') if not isinstance(s, dict) and not isinstance(s,int) else s, line)
        ad_lines.append(Ad(*utf8_line))

    return ad_lines
    
def find_json_logs(log_file):
    json_logs=[]
    with open(log_file,'r') as log:
        for line in log.readlines():
            if "save_data" in line:
                d = line.strip().split(":")[3:]
                json_logs.append(d)
    return json_logs

def combine_sessions(data):
    '''
    provided the loaded data (dict keyed on session) return all adlines in a list
    '''
    all_data = []
    for session in data:
        unit_id, treatment_id, ad_lines = data[session]
        for ad in ad_lines:
            all_data.append((session,ad))
    return all_data

Ad = namedtuple('Ad',['url','outerhtml','tag','link_text','link_location','on_site', 'reloads'])

def get_domain(url):
    parsed_uri = urlparse(url)
    return '{uri.netloc}/'.format(uri=parsed_uri)

def occurances(dom,data):
    return len([row for row in data if get_domain(row[1].url) == dom])

def uniq_domains(all_data):
    doms = set()
    for row in all_data:
        session,ad  = row
        doms.add(get_domain(ad.url))

    doms  = sorted(list(doms))
    dom_dict ={}
    for d in doms:
        dom_dict[d]=occurances(d,all_data)
    print "{} uniq domains".format(len(doms))
    
    cnt = sorted(list(dom_dict.items()),key=operator.itemgetter(1))

    for d in cnt:
        print d



def main(log_file):

    # A dictionary of sessions keyed by session_id
    # Values are [unit_id,treatment_id,[ad_line0,ad_line1,..,ad_lineN]]
    data  = {}

    json_logs = find_json_logs(log_file)
    for log in json_logs:
        unit_id, treatment_id, session_id = log
        print("Session: {} was treatment/unit {}/{}".format(session_id,treatment_id,unit_id))
        ad_lines = load_ads_from_json(log_file,session_id)
        data[session_id] = [unit_id, treatment_id,ad_lines]

    all_data = combine_sessions(data)

    print("### Simple Ad Data ###")
    uniq_domains(all_data)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("pass in log_file as an argument")
