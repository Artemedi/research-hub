import gi,subprocess,json,threading,time,os,pathlib
from gi.repository import GLib
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
GLib.set_prgname('bk065-fixture');GLib.set_application_name('bk065-fixture')
count=[0];window=Gtk.Window(title='BK065 Synthetic Only');button=Gtk.Button(label='Fixture Button');button.connect('clicked',lambda *_:count.__setitem__(0,count[0]+1));window.add(button);window.show_all()
result={'source_sha':'b43ac4f6e892ef608f8851428613c4009f0e84c7','oracle':'GTK clicked callback in authored toy app','pid':os.getpid(),'cases':[]}
def cli(*args):
 p=subprocess.run(['/target/debug/agent-desktop','--session','bk065-lab',*args],capture_output=True,text=True,timeout=12)
 return p.returncode,json.loads(p.stdout)
def nodes(v):
 if isinstance(v,dict):
  yield v
  for child in v.values():yield from nodes(child)
 elif isinstance(v,list):
  for child in v:yield from nodes(child)
def probe():
 try:
  time.sleep(1)
  code,apps=cli('list-apps');result['apps']=apps
  candidates=[n for n in nodes(apps) if n.get('pid')==os.getpid() and isinstance(n.get('name'),str)]
  assert candidates,'own app not listed on private AT-SPI bus'
  name=candidates[0]['name'];code,snap=cli('snapshot','--app',name,'-i');result['snapshot']=snap
  target=next(n for n in nodes(snap) if n.get('name')=='Fixture Button' and n.get('ref_id'));ref=target['ref_id']
  code,action=cli('click',ref);time.sleep(.2);assert count[0]==1,('independent count',count[0],action)
  result['cases'].append({'case':'original click updates GTK oracle','passed':True,'count':count[0]})
  code,bare=cli('click','@e1');assert bare.get('error',{}).get('code')=='INVALID_ARGS' and count[0]==1
  result['cases'].append({'case':'bare ref refused without effect','passed':True})
  code,wrong=cli('click','@sdeadbeef:e1');assert wrong.get('error',{}).get('code')=='SNAPSHOT_NOT_FOUND' and count[0]==1
  result['cases'].append({'case':'unknown snapshot refused without effect','passed':True})
  GLib.idle_add(button.destroy);time.sleep(.3);code,stale=cli('click',ref);result['stale']=stale;assert stale.get('error',{}).get('code')=='STALE_REF' and count[0]==1
  result['cases'].append({'case':'destroyed widget refused without effect','passed':True})
  result['passed']=True
 except Exception as e:result['passed']=False;result['error']=repr(e)
 finally:
  pathlib.Path('/evidence/gui-probe.json').write_text(json.dumps(result,indent=2));GLib.idle_add(Gtk.main_quit)
threading.Thread(target=probe,daemon=True).start();GLib.timeout_add_seconds(50,lambda:(Gtk.main_quit(),False)[1]);Gtk.main()
