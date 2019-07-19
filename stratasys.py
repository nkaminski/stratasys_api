import sys
import re
from struct import *
import socket
import config as cf

def make_request(sock, req):
    """ Makes a request to the printer by packing
    the request string into a 64 byte fixed length packet.
    """
    req_struct = pack('64s', req)
    sock.sendall(req_struct)

def recv_data(sock,size):
    """ Receives `size` bytes from the printer and returns
    the first null-terminated/C-style string in the returned payload.
    """ 
    data = b''
    needed=size
    while(needed>0):
        data += sock.recv(needed)
        needed=size-len(data)
    return data[:data.find(b'\x00')]

def printer_get_data(h,p=53742):
    """ Makes a rquest for the `status.sts` file over the
    Stratasys line protocol and returns the contents as a byte string.
    
    Returns None if the printer cannot be contacted."""
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

def expand_stanza(key, value):
    """ Expands a machineStatus stanza to a dictionary
    or list of dictionaries representing the stanza """
    if(key == "machineStatus(queue)"):
        # Queue stanza, parse to list of queue entry dictionaries
        qentries = value[1:-1].split('}\t')
        ol=[]
        for qentry in qentries:
            if not len(qentry):
                continue
            lst = qentry.replace('{','').replace('}','').split("\t-")
            lst = map(lambda each:each.strip("\t"), lst)
            lst = [x for x in lst if len(x)>0]
            od = {}
            for item in lst:
                itemkey, _, itemvalue = item.partition(" ")
                od[itemkey] = itemvalue.strip().replace('"','')
            ol.append(od)
        return ol
    else:
        # Non-queue stanza, parse to dictionary
        lst = value.replace('{','').replace('}','').split("\t-")
        lst = [x for x in lst if len(x)>0]
        od = {}
        for item in lst:
            itemkey, _, itemvalue = item.partition(" ")
            od[itemkey] = itemvalue.strip().replace('"','')
        return od

def stratasys_out_proc(status_sts):
    """ Parses the string output of the `ststus.sts` endpoint of the
    Stratasys line protocol into a composite of Python data structures.
    """
    # Initialization and input validation
    out_dict={}
    bracesplit = re.compile(r"(?P<category>machineStatus\([^\s]+\)) (?P<value>\{.*\})")
    if not(status_sts):
        return None
    # Split semicolon delimited stanzas
    stanzas = status_sts.replace(b'\n',b'').replace(b'\r',b'').split(b';')
    
    # Process each indented stanza
    for stanza in stanzas:
        machinestatus = bracesplit.search(stanza.decode("utf-8"))
        if machinestatus:
            # Handle a machinestatus stanza
            out_dict[machinestatus.group('category')] = \
	    		expand_stanza(machinestatus.group('category'),machinestatus.group('value'))
        else:
            # Handle metadata line/stanza
            key, _, value = stanza.decode("utf-8").partition(":");
            if len(value):
                out_dict[key] = value

    # Filter out any empty queue objects
    out_dict['machineStatus(queue)'] = list(filter(lambda x: len(x.keys()) != 0, out_dict['machineStatus(queue)']))
    return out_dict

def output_postproc(indata):
    """ Post-processes the output, adding the machineType attribute
    to the machine-specific stanza and naming the result consistently
    `machineStatus(extended)`
    """
    # Mapping modelerType to name of extended stanza
    name_map = {'paia' : 'mariner', 'lffs' : 'lffs', 'sst1230' : 'mariner', 'solo' : 'solo', 'dorado1': 'dorado1'}
    name=name_map[indata['machineStatus(general)']['modelerType']]
    nameKey="machineStatus("+name+")"
    indata['machineStatus(extended)'] = indata[nameKey]
    del indata[nameKey]
    # Mapping modelerType to friendly name/model of the machine.
    if indata['machineStatus(general)']['modelerType'] == 'lffs':
       indata['machineStatus(extended)']['machineName'] = "Fortus"
    elif indata['machineStatus(general)']['modelerType'] == 'paia':
       indata['machineStatus(extended)']['machineName'] = "uPrint"
    elif indata['machineStatus(general)']['modelerType'] == 'mariner':
       indata['machineStatus(extended)']['machineName'] = "Dimension"
    elif indata['machineStatus(general)']['modelerType'] == 'solo':
       indata['machineStatus(extended)']['machineName'] = "Mojo"
    elif indata['machineStatus(general)']['modelerType'] == 'dorado1':
       indata['machineStatus(extended)']['machineName'] = "F170"
    else:
       indata['machineStatus(extended)']['machineName'] = "Other"
    return indata

if( __name__ == "__main__"):
    if len(sys.argv) == 2:
        print("Reading printer data from file specified on command line")
        with open(sys.argv[1], 'rb') as fp:
            printer_data = fp.read()
    else:
        print("Reading printer data via network from {}".format(cf.printer_ip))
        printer_data = printer_get_data(cf.printer_ip)
    
    print(output_postproc(stratasys_out_proc(printer_data)))
