import re
import json
import time
import stratasys as st
from pprint import pprint
import flask as fk
from flask import jsonify,Response

app = fk.Flask(__name__)
printer_host = '192.168.0.3'

def return_unavail():
    rd = { 'status' : "offline"}
    resp = jsonify(rd)
    resp.status_code=503
    return resp
def refreshCond():
    global od, lastref
    if(lastref < time.monotonic()):
        od=st.output_postproc(st.stratasys_out_proc(st.printer_get_data(printer_host)))
        print("Perfomed Refresh")
        lastref = (time.monotonic() + 10.0)
        
#dict_keys(['machineStatus(cassette)', 'machineStatus(queue)', 'machineStatus(previousJob)', 'machineStatus(general)', 'Transferred', 'machineStatus(mariner)', 'machineStatus(currentJob)'])
@app.route("/v1/uprint/queue")
def queue():
    global od
    refreshCond()
    if not od:
        return return_unavail()
    rs = json.dumps(od['machineStatus(queue)'])
    return Response(rs, status=200, mimetype = 'application/json')
@app.route("/v1/uprint/status")
def stat():
    global od
    refreshCond()
    if not od:
        return return_unavail()
    return jsonify(sanitize(od['machineStatus(general)']))
@app.route("/v1/uprint/job")
def job():
    global od
    refreshCond()
    if not od:
        return return_unavail()
    return jsonify(sanitize(od['machineStatus(currentJob)']))
@app.route("/v1/uprint/extstatus")
def es():
    global od
    refreshCond()
    if not od:
        return return_unavail()
    return jsonify(sanitize(od['machineStatus(extended)']))
@app.route("/v1/uprint/material")
def cass():
    global od
    refreshCond()
    if not od:
        return return_unavail()
    return jsonify(sanitize(od['machineStatus(cassette)']))
@app.route("/")
def root():
    return app.send_static_file('index.html')

def sanitize(ind):
    r = re.compile("version|serial|mfglot|mfgdate|usagedate")
    return {k: v for k, v in ind.items() if r.search(k.lower()) == None}

if( __name__ == "__main__"):
    lastref = 0
    app.run(host='0.0.0.0',port=8080,debug=False)

