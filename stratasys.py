import re
import json
from struct import *
import socket
import time

PORT = 53742

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
        if(key == "machineStatus(queue)"):
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
        stra=stra.replace(b'\n',b'').split(b';')
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
        return out_dict                    


if( __name__ == "__main__"):
    print(stratasys_out_proc(printer_get_data()))
