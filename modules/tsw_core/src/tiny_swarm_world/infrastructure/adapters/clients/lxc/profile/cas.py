"""Literal bounded local HTTP CAS; no repository import in the child process."""
PROFILE_CAS = r'''
import hashlib,http.client,json,os,re,socket,stat,struct,sys
from uuid import UUID
ERROR='PROFILE_CAS_UNKNOWN'
http.client._MAXLINE=4096
http.client._MAXHEADERS=32
def unique(pairs):
 result={}
 for key,value in pairs:
  if key in result: raise ValueError()
  result[key]=value
 return result
class Local(http.client.HTTPConnection):
 def connect(self):
  path=ENDPOINTS[ENDPOINT_KIND]
  parent=path.rsplit('/',1)[0]
  while True:
   info=os.lstat(parent)
   if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022: raise ValueError()
   if parent=='/': break
   parent=parent.rsplit('/',1)[0] or '/'
  info=os.lstat(path)
  if not stat.S_ISSOCK(info.st_mode) or info.st_uid!=0: raise ValueError()
  self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
  self.sock.settimeout(10)
  self.sock.connect(path)
  _,uid,_=struct.unpack('3i',self.sock.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
  if uid!=0: raise ValueError()
def request(method,path,body=None,headers=None):
 client=Local('localhost',timeout=10)
 try:
  client.request(method,path,body=body,headers=headers or {})
  response=client.getresponse()
  if response.getheader('Content-Type') not in ('application/json','application/json; charset=utf-8'): raise ValueError()
  length=response.getheader('Content-Length')
  transfer=response.getheader('Transfer-Encoding')
  if (length is not None and (not length.isascii() or not length.isdigit() or int(length)>1048576)
      or transfer not in (None,'chunked') or length is not None and transfer is not None): raise ValueError()
  raw=response.read(1048577)
  if length is not None and len(raw)!=int(length): raise ValueError()
  if len(raw)>1048576 or response.status!=200: raise ValueError()
  row=json.loads(raw,object_pairs_hook=unique)
  if (not isinstance(row,dict) or set(row)!={'type','status','status_code','operation','error_code','error','metadata'}
      or row['type']!='sync' or row['status']!='Success' or type(row['status_code']) is not int or row['status_code']!=200
      or row['operation']!='' or type(row['error_code']) is not int or row['error_code']!=0 or row['error']!=''): raise ValueError()
  return row['metadata'],response.getheader('ETag')
 finally: client.close()
def profile(row,path):
 if (not isinstance(row,dict) or set(row)!={'name','project','description','config','devices','used_by'}
     or row['name']!=path.split('/')[3].split('?')[0] or row['project']!='default'
     or row['description']!='Tiny Swarm World installation profile'
     or row['used_by'] not in (['/1.0/instances/swarm-manager'],['/1.0/instances/swarm-manager?project=default'])): raise ValueError()
 config=row['config']
 if (not isinstance(config,dict) or set(config)!={'user.tiny_swarm_world.installation_id','user.tiny_swarm_world.operation_id'}
     or type(config['user.tiny_swarm_world.installation_id']) is not str
     or str(UUID(config['user.tiny_swarm_world.installation_id']))!=config['user.tiny_swarm_world.installation_id']
     or type(config['user.tiny_swarm_world.operation_id']) is not str
     or re.fullmatch('[0-9a-f]{32}',config['user.tiny_swarm_world.operation_id']) is None): raise ValueError()
 if row['name']!='tsw-manager-'+hashlib.sha256(config['user.tiny_swarm_world.installation_id'].encode('ascii')).hexdigest()[:24]: raise ValueError()
 devices(row['devices'])
def devices(rows):
 if not isinstance(rows,dict) or len(rows)>64: raise ValueError()
 for key,row in rows.items():
  if type(key) is not str or re.fullmatch(r'tsw-proxy-[1-9][0-9]{0,4}',key) is None: raise ValueError()
  port=int(key.rsplit('-',1)[1])
  if (port>65535 or not isinstance(row,dict) or set(row)!={'type','bind','listen','connect','nat','proxy_protocol'}
      or row['type']!='proxy' or row['bind']!='host' or row['nat']!='false' or row['proxy_protocol']!='false'
      or row['listen'] not in ('tcp:0.0.0.0:'+str(port),'tcp:127.0.0.1:'+str(port))
      or row['connect']!='tcp:127.0.0.1:'+str(port)): raise ValueError()
try:
 if len(sys.argv)!=2 or len(sys.argv[1].encode())>1048576: raise ValueError()
 arg=json.loads(sys.argv[1],object_pairs_hook=unique)
 if not isinstance(arg,dict) or set(arg)!={'endpoint_kind','path','before','target'}: raise ValueError()
 ENDPOINTS={'incus_run':'/run/incus/unix.socket','incus_var_lib':'/var/lib/incus/unix.socket'}
 ENDPOINT_KIND=arg['endpoint_kind']
 if type(ENDPOINT_KIND) is not str or ENDPOINT_KIND not in ENDPOINTS: raise ValueError()
 path=arg['path']
 if type(path) is not str or re.fullmatch(r'/1\.0/profiles/tsw-manager-[0-9a-f]{24}\?project=default',path) is None: raise ValueError()
 profile(arg['before'],path)
 observed,etag=request('GET',path)
 if observed!=arg['before'] or type(etag) is not str or re.fullmatch(r'"[0-9a-f]{64}"',etag) is None: raise ValueError()
 target=arg['target']
 if (not isinstance(target,dict) or set(target)!={'description','config','devices'}
     or target['description']!=arg['before']['description'] or target['config']!=arg['before']['config']): raise ValueError()
 devices(target['devices'])
 metadata,_=request('PUT',path,json.dumps(target,separators=(',',':')),{'Content-Type':'application/json','If-Match':etag})
 if metadata is not None and metadata!={}: raise ValueError()
 print('PROFILE_CAS_APPLIED')
except BaseException:
 print(ERROR)
 sys.exit(2)
'''
