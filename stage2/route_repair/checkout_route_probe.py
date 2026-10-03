"""Bounded standard-library probe of a copied checkout application.

It checks controlled default/explicit launcher selection and HTTP handler
contracts. It neither starts the historical agent nor claims a historical server
was launched. Tests use local ephemeral HTTP listeners, never external services.
"""
import json
import subprocess
import sys

PROGRAM = r'''
import contextlib,http.client,importlib.util,json,os,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
root=Path.cwd()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,root/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
launcher=load("branch_launcher","run.py")
selections={}
for mode in ["UNSET","on","off"]:
 env=dict(os.environ)
 try:
  if mode=="UNSET":os.environ.pop("CHECKOUT_COMPAT",None)
  else:os.environ["CHECKOUT_COMPAT"]=mode
  hit=[];launcher.current_main=lambda:hit.append("current");launcher.legacy_main=lambda:hit.append("legacy")
  launcher.main();selections[mode]=hit
 finally:
  os.environ.clear();os.environ.update(env)
from checkout_app.server import Handler
from legacy_compat import LegacyHandler
contracts={}
for name,cls in [("current",Handler),("legacy",LegacyHandler)]:
 server=ThreadingHTTPServer(("127.0.0.1",0),cls)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 rows=[]
 try:
  for method in ["card","bank_transfer"]:
   client=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=3)
   payload={"cart":{"items":[{"price_cents":1250,"quantity":2}]},"method":method}
   client.request("POST","/api/checkout",body=json.dumps(payload),headers={"Content-Type":"application/json"})
   response=client.getresponse();body=response.read().decode();client.close()
   try:body=json.loads(body)
   except json.JSONDecodeError:pass
   rows.append({"method":method,"status":response.status,"body":body})
 finally:
  server.shutdown();server.server_close();thread.join(timeout=3)
 contracts[name]=rows
print(json.dumps({"controlled_launcher_selection":selections,"http_handler_contracts":contracts,
 "historical_server_execution_inferred":False,"browser_end_to_end_tested":False,"agent_provider_calls":0}))
'''


def probe(checkout):
    run = subprocess.run([sys.executable, '-c', PROGRAM], cwd=checkout, capture_output=True,
                         text=True, timeout=15, check=True)
    result = json.loads(run.stdout)
    result['handler_stderr'] = run.stderr
    # Port numbers and timestamps in HTTP logs are not scientific measurements.
    result['handler_stderr'] = 'HTTP handler access logs omitted; exact response bodies/statuses retained.'
    return result
