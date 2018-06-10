import re
from struct import *
import socket
import config as cf
from pprint import pprint

def make_request(sock, req):
    req_struct = pack('64s', req)
    sock.sendall(req_struct)
def recv_data(sock,size):
    data = b''
    needed=size
    while(needed>0):
        data += sock.recv(needed)
        needed=size-len(data)
    return data[:data.find(b'\x00')]

def printer_get_data(h,p=53742):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4.0)
        try:
            s.connect((h, p))  
            make_request(s,b'GetFile')
            make_request(s,b'status.sts')
            make_request(s,b'NA')
            recv_data(s,64)
            recv_data(s,64)
            make_request(s,b'OK')
            respsz=int(recv_data(s,64).decode('ascii'))
            make_request(s,b'OK')
            outdat=recv_data(s,respsz)
        except(socket.timeout):
            outdat = None
        s.close()
        return outdat;

def parse_output(input_str):
    if not(input_str):
        return None
    #Compile regex, handles headers and removes first brace layer
    stanza_r = re.compile(r"^set (?P<category>machineStatus\([^\s]+\)) \{(?P<value>.*)\}$")
    #Normalize input: -\t -> \t, strip CR and LF
    normalized=input_str.replace(b'\n',b'').replace(b'\r',b'').replace(b'\t-',b'\t').decode('ascii')
    #Split semicolon delimited stanzas
    stanzas=normalized.split(';')
    out_dict={}
    for stanza in stanzas:
        #Parse the top level of each stanza
        match=stanza_r.match(stanza)
        if not match:
            continue
        out_dict[match.group('category')] = parse_stanza(match.group('value'))
    return out_dict

def parse_stanza(stanza):
    #Compile regex
    list_r = re.compile(r'\}\s*\{')
    #Strip leading or trailing tabs
    norm_stanza=stanza.strip('\t')
    if(norm_stanza[0] == '{'):
        #If the stanza starts with a brace, this is a list.
        output = list()
        prelist = norm_stanza[1:-1]
        for item in list_r.split(prelist):
            output.append(parse_stanza(item))
    else:
        #Otherwise, this is a normal dict of items
        output = dict()
        for item in norm_stanza.split('\t'):
            if len(item) == 0:
                continue
            key, val = item.split(' ', 1)
            output[key]=normalize_value(val)
    return output

def normalize_value(val):
    decimal_r = re.compile(r'^-?(\d*\.)?\d+$')
    int_r = re.compile(r'^-?\d+$')
    val = val.strip('{}"')
    if int_r.match(val):
        val=int(val)
    elif decimal_r.match(val):
        val=float(val)
    return val

def output_postproc(indata):
    #Mappings from codenames to friendly/actual names
    friendlyname_map = {'lffs' : 'Fortus', 'paia' : 'uPrint', 'mariner' : 'Dimension' , 'solo' : 'Mojo', 'dimension' : 'Original Dimension'}
    #Add the modelerName attribute
    codename=indata['machineStatus(general)']['modelerType']
    if codename in friendlyname_map:
        indata['modelerName'] = friendlyname_map[codename]
    else:
        indata['modelerName'] = 'Other'
    return indata

if( __name__ == "__main__"):
     pprint(output_postproc((parse_output(printer_get_data(cf.printer_ip)))))
