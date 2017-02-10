import re
import json
from struct import *
import socket
import time
import config as cf

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

def objproc(key, value):
        if(key == "machineStatus(queue)" or key == "machineStatus(cassette)"):
            v1 = value[1:-1].split('}\t')
            ol=[]
            for i in v1:
                if(len(i)<1):
                    continue
                lst = i.replace('{','').replace('}','').split("\t-")
                lst = map(lambda each:each.strip("\t"), lst)
                lst = [x for x in lst if len(x)>0]
                od = {}
                for a in lst:
                    sloc = a.find(" ")
                    od[a[:sloc]] = a[sloc:].strip().replace('"','')
                ol.append(od)
            return ol
        else:
            lst = value.replace('{','').replace('}','').split("\t-")
            lst = [x for x in lst if len(x)>0]
            od = {}
            for i in lst:
                sloc = i.find(" ")
                od[i[:sloc]] = i[sloc:].strip().replace('"','')
            return od
def stratasys_out_proc(stra):
        if not(stra):
            return None
        stra=stra.replace(b'\n',b'').replace(b'\r',b'').split(b';')
        out_dict={}
        bracesplit = re.compile(r"(?P<category>machineStatus\([^\s]+\)) (?P<value>\{.*\})")
        for s in stra:
            p=bracesplit.search(s.decode("utf-8"))
            if(p == None):
                    p1 = s.decode("utf-8").partition(":");
                    if(p1[2]):
                        p1 = tuple(map(lambda each:each.strip(), p1))
                        out_dict[p1[0]]=p1[2]
            else:
                    out_dict[p.group('category')] = objproc(p.group('category'),p.group('value'))
        out_dict['machineStatus(queue)'] = list(filter(lambda x: len(x.keys()) != 0, out_dict['machineStatus(queue)']))
        return out_dict
def output_postproc(indata):
     name_map = {'paia' : 'mariner', 'lffs' : 'lffs', 'sst1230' : 'mariner', 'solo' : 'solo'}
     name=name_map[indata['machineStatus(general)']['modelerType']]
     nameKey="machineStatus("+name+")"
     indata['machineStatus(extended)'] = indata[nameKey]
     del indata[nameKey]
     if indata['machineStatus(general)']['modelerType'] == 'lffs':
        indata['machineStatus(extended)']['machineName'] = "Fortus"
     elif indata['machineStatus(general)']['modelerType'] == 'paia':
        indata['machineStatus(extended)']['machineName'] = "uPrint"
     elif indata['machineStatus(general)']['modelerType'] == 'mariner':
        indata['machineStatus(extended)']['machineName'] = "Dimension"
     elif indata['machineStatus(general)']['modelerType'] == 'solo':
        indata['machineStatus(extended)']['machineName'] = "Mojo"
     else:
        indata['machineStatus(extended)']['machineName'] = "Other"
     return indata

if( __name__ == "__main__"):
     print (output_postproc(stratasys_out_proc(printer_get_data(cf.printer_ip))))
