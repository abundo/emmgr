#!/urs/bin/env python3

from flask import render_template, request, redirect
from emmgr.app import app

import re
import json
import shlex
from orderedattrdict import AttrDict

import emmgr.lib.config as config
import emmgr.lib.log as log
import emmgr.lib.util as util

import emmgr.lib.element as element


@app.route('/elements/running_configuration')
def running_configuration():
    messages = []
    config = None
    param = util.get_param(request, ["action",
                                    "hostname",
                                    "save_config",
                                    ])
    if param.hostname:
        try:
            e = element.Element(hostname=param.hostname)
            config = e.get_running_config()
            config = "\n".join(config)
            
        except element.ElementException as err:
            messages.append(err)
    return render_template('elements/running_configuration.html',
                           messages=messages,
                           param=param,
                           paramJson=json.dumps(param),
                           config=config,
                           )
    


@app.route('/elements/software_management')
def software_management():
    import lib.jobs as jobs
    import lib.jobs_def as jobs_def
    
    messages = []
    ement = None
    job = None
    
    param = util.get_param(request, ["action",
                                    "hostname",
                                    "mgr",
                                    "firmware",
                                    ])

    # todo, handle default
    if param.mgr == "":  
        param.mgr = config.em.default_firmware_server
    if param.firmware == "":
        param.firmware = config.em.asr920.default_firmware
    
    # print("query", query)
    if param.hostname:
        
        try:
            e = element.Element(hostname=param.hostname)
            config = e.get_running_config()
            config = "\n".join(config)
            
            if param.action == "sw_upgrade":
                description = "Upgrade firmware in element %s to %s" % \
                    (param.hostname, param.firmware)
                     
                job = jobs.Job(description=description, submitter="")
                job.add( jobs_def.Job_em_sw_upgrade(hostname=ement.ipaddr_mgmt, 
                                                    mgr=param.mgr,
                                                    filename=param.firmware,
                                                    setboot=True )
                                    )
                jobs_id = jobs.jobMgr.add(job)
                messages.append(description)
                messages.append("Job id: %s" % job.id)
            
        except element.ElementException as err:
            messages.append(err)
                
    return render_template('elements/software_management.html',
                           messages=messages,
                           param=param,
                           paramJson=json.dumps(param), 
                           ement=ement, job=job)
