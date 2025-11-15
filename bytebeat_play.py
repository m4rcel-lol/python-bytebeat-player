#!/usr/bin/env python3
from __future__ import annotations
import ast,argparse,math,sys,wave,struct,subprocess,tempfile,os,platform
from typing import Callable,Iterator,Tuple,List,Union,TYPE_CHECKING,Any
if TYPE_CHECKING:
 import numpy as np
else:
 np=Any
try:
 import numpy as np;_n=True
except ImportError:
 np=None;_n=False
try:
 import sounddevice as sd;_s=True
except ImportError:
 sd=None;_s=False
if platform.system().lower()=="windows":
 import winsound;os.system("")
_r,_b,_d,_k,_R,_g,_y,_c,_m,_w,_bk,_br,_bg,_by,_bb,_bm,_bc,_bw="\033[0m","\033[1m","\033[2m","\033[30m","\033[91m","\033[92m","\033[93m","\033[96m","\033[95m","\033[97m","\033[40m","\033[41m","\033[42m","\033[43m","\033[44m","\033[45m","\033[46m","\033[47m"
class _C:
 R,B,D,K,RED,G,Y,C,M,W=_r,_b,_d,_k,_R,_g,_y,_c,_m,_w
 @classmethod
 def _gb(cls,p:float,w:int=40)->str:
  f,e=int(w*p),w-int(w*p);return f"{cls.C}{'█'*f}{cls.D}{'░'*e}{cls.R}"
class _V:
 _ao={ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.LShift,ast.RShift,ast.BitOr,ast.BitAnd,ast.BitXor,ast.Pow}
 _uo={ast.UAdd,ast.USub,ast.Invert,ast.Not}
 @staticmethod
 def _v(n:ast.AST)->None:
  if isinstance(n,ast.Expression):_V._v(n.body);return
  if isinstance(n,ast.BinOp):
   if type(n.op)not in _V._ao:raise ValueError(f"Unsupported binary operator: {type(n.op).__name__}")
   _V._v(n.left);_V._v(n.right);return
  if isinstance(n,ast.UnaryOp):
   if type(n.op)not in _V._uo:raise ValueError(f"Unsupported unary operator: {type(n.op).__name__}")
   _V._v(n.operand);return
  if isinstance(n,ast.Constant):
   if not isinstance(n.value,(int,float)):raise ValueError(f"Unsupported constant type: {type(n.value).__name__}")
   return
  if isinstance(n,ast.Name):
   if n.id!='t':raise ValueError(f"Only variable 't' is allowed, found: {n.id}")
   return
  if isinstance(n,(ast.Call,ast.Attribute,ast.Compare,ast.BoolOp,ast.IfExp)):raise ValueError(f"Unsupported operation: {type(n).__name__}")
  if not isinstance(n,(ast.Load,)):raise ValueError(f"Unsupported node type: {type(n).__name__}")
 @staticmethod
 def _ce(e:str)->Callable[[int],int]:
  e=e.replace("/","//");p=ast.parse(e,mode='eval');_V._v(p);cc=compile(p,'<bytebeat>','eval')
  def _ev(t:int)->int:
   lv={'t':int(t)}
   try:r=eval(cc,{"__builtins__":None,'math':math},lv);return int(r)
   except Exception:return 0
  return _ev
class _G:
 @staticmethod
 def _gc(f:Callable[[int],int],d:float=10.0,sr:int=8000,to:int=0)->Iterator[Tuple[float,Union[Any,List[int]]]]:
  cs,ts,tc=sr//4,int(d*sr),int(d*sr)//(sr//4)
  if _n:
   for i in range(tc):
    bt=to+i*cs;ch=np.empty(cs,dtype=np.int16)
    for j in range(cs):v=f(bt+j);ch[j]=np.int16(((int(v)&0xFF)-128)*256)
    yield(i+1)/float(tc),ch
  else:
   for i in range(tc):
    bt=to+i*cs;ch=[((int(f(bt+j))&0xFF)-128)*256 for j in range(cs)]
    yield(i+1)/float(tc),ch
class _P:
 @staticmethod
 def _pr(f:Callable[[int],int],d:float,sr:int,to:int)->None:
  if not _s or not _n:print(f"{_C.Y}⚠ sounddevice/numpy not installed — using WAV fallback{_C.R}");_P._pf(f,d,sr,to);return
  print(f"\n{_C.B}{_C.G}▶ Playing live audio... {_C.D}(Press Ctrl+C to stop){_C.R}");st=sd.OutputStream(samplerate=sr,channels=1,dtype='float32');st.start()
  try:
   for p,ch in _G._gc(f,d,sr,to):
    bar=_C._gb(p);pc=int(p*100);print(f"\r{_C.C}Progress: {_C.R}[ {bar} {_C.C}] {pc}%{_C.R}",end="",flush=True)
    st.write(ch.astype('float32')/32768.0)
  except KeyboardInterrupt:print(f"\n\n{_C.Y}⏹ Playback interrupted by user{_C.R}")
  finally:st.stop();st.close();print(f"\n{_C.G}✓ Playback complete{_C.R}\n")
 @staticmethod
 def _pf(f:Callable[[int],int],d:float,sr:int,to:int)->None:
  print(f"\n{_C.C}Rendering audio...{_C.R}");a=[]
  try:
   for p,ch in _G._gc(f,d,sr,to):
    a.extend(ch);bar=_C._gb(p);pc=int(p*100);print(f"\r{_C.C}Rendering: {_C.R}[ {bar} {_C.C}] {pc}%{_C.R}",end="",flush=True)
  except KeyboardInterrupt:print(f"\n\n{_C.Y}⏹ Rendering interrupted{_C.R}")
  print(f"\n{_C.G}✓ Rendering complete{_C.R}");_P._pw(a,sr)
 @staticmethod
 def _pw(s:Union[Any,List[int]],sr:int)->None:
  with tempfile.NamedTemporaryFile(suffix='.wav',delete=False)as tf:tfn=tf.name
  fr=b''.join(struct.pack('<h',x)for x in s)if isinstance(s,list)else s.tobytes()
  with wave.open(tfn,'wb')as wf:wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr);wf.writeframes(fr)
  print(f"{_C.C}Playing WAV file...{_C.R}");pl=False;sn=platform.system().lower()
  if sn=="windows":
   try:winsound.PlaySound(tfn,winsound.SND_FILENAME);pl=True
   except Exception:pass
  elif sn=="darwin":
   try:subprocess.run(['afplay',tfn],check=True);pl=True
   except Exception:pass
  else:
   try:subprocess.run(['aplay',tfn],check=True);pl=True
   except Exception:
    try:subprocess.run(['ffplay','-nodisp','-autoexit','-hide_banner','-loglevel','panic',tfn],check=True);pl=True
    except Exception:pass
  if not pl:print(f"{_C.Y}⚠ Could not auto-play. WAV file saved to: {tfn}{_C.R}")
  else:print(f"{_C.G}✓ Playback complete{_C.R}\n")
def _pb()->None:
 print(f"""
{_C.M}██████╗ ██╗   ██╗████████╗███████╗██████╗ ███████╗ █████╗ ████████╗
██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔════╝██╔══██╗██╔════╝██╔══██╗╚══██╔══╝
██████╔╝ ╚████╔╝    ██║   █████╗  ██████╔╝█████╗  ███████║   ██║   
██╔══██╗  ╚██╔╝     ██║   ██╔══╝  ██╔══██╗██╔══╝  ██╔══██║   ██║   
██████╔╝   ██║      ██║   ███████╗██████╔╝███████╗██║  ██║   ██║   
╚═════╝    ╚═╝      ╚═╝   ╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   
{_C.Y}                   ╔═╗╦  ╔═╗╦ ╦╔═╗╦═╗
                   ╠═╝║  ╠═╣╚╦╝║╣ ╠╦╝
                   ╩  ╩═╝╩ ╩ ╩ ╚═╝╩╚═{_C.R}
""")
def _pi(e:str,sr:int,d:float,to:int)->None:
 print(f"\n{_C.B}{_C.Y}Configuration:{_C.R}");print(f"  {_C.B}Expression:{_C.R}   {_C.G}{e}{_C.R}");print(f"  {_C.B}Sample Rate:{_C.R}  {_C.M}{sr}{_C.R} Hz");print(f"  {_C.B}Duration:{_C.R}     {_C.M}{d:.1f}{_C.R} seconds");print(f"  {_C.B}Time Offset:{_C.R}  {_C.M}{to}{_C.R}")
 snp=f"{_C.G}✓{_C.R}"if _n else f"{_C.RED}✗{_C.R}";ssd=f"{_C.G}✓{_C.R}"if _s else f"{_C.RED}✗{_C.R}"
 print(f"  {_C.B}Status:{_C.R}       NumPy {snp} | Sounddevice {ssd}")
def _ph():
 print(f"""
{_C.M}{_C.B}BYTEBEAT PLAYER{_C.R} - 8-bit audio from math

{_C.B}{_C.Y}USAGE:{_C.R}
  python bytebeat_play.py {_C.G}<file>{_C.R} [{_C.C}options{_C.R}]

{_C.B}{_C.Y}ARGUMENTS:{_C.R}
  {_C.G}<file>{_C.R}          Path to bytebeat expression file

{_C.B}{_C.Y}OPTIONS:{_C.R}
  {_C.C}--duration{_C.R} {_C.D}<float>{_C.R}  Duration in seconds (default: 60.0)
  {_C.C}--sr{_C.R}       {_C.D}<int>{_C.R}    Sample rate in Hz (default: 8000)
  {_C.C}--tstart{_C.R}   {_C.D}<int>{_C.R}    Time offset (default: 0)
  {_C.C}-h, --help{_C.R}           Show this help message

{_C.B}{_C.Y}EXAMPLES:{_C.R}
  python bytebeat_play.py {_C.G}song.byteb{_C.R}
  python bytebeat_play.py {_C.G}song.byteb{_C.R} {_C.C}--duration 30{_C.R}
  python bytebeat_play.py {_C.G}song.byteb{_C.R} {_C.C}--sr 16000{_C.R}

{_C.B}{_C.Y}EXPRESSION EXAMPLE:{_C.R}
  {_C.M}t*(t>>8|t>>9)&46&t>>8{_C.R}
""")
def main()->None:
 pr=argparse.ArgumentParser(description="Bytebeat Player",formatter_class=argparse.RawDescriptionHelpFormatter,add_help=False)
 pr.add_argument('-h','--help',action='store_true',help='Show help message');pr.add_argument('file',nargs='?',help='Path to bytebeat expression file');pr.add_argument('--duration',type=float,default=60.0,help='Duration in seconds');pr.add_argument('--sr',type=int,default=8000,help='Sample rate in Hz');pr.add_argument('--tstart',type=int,default=0,help='Starting time offset')
 a=pr.parse_args()
 if a.help or not a.file:_ph();sys.exit(0)
 _pb()
 try:
  with open(a.file,'r')as fi:ex=fi.read().strip()
 except FileNotFoundError:print(f"{_C.RED}{_C.B}✗ Error:{_C.R} File not found: {a.file}");sys.exit(1)
 except Exception as e:print(f"{_C.RED}{_C.B}✗ Error reading file:{_C.R} {e}");sys.exit(1)
 if not ex:print(f"{_C.RED}{_C.B}✗ Error:{_C.R} Expression file is empty");sys.exit(1)
 try:bf=_V._ce(ex)
 except ValueError as e:print(f"{_C.RED}{_C.B}✗ Invalid expression:{_C.R} {e}");sys.exit(1)
 except SyntaxError as e:print(f"{_C.RED}{_C.B}✗ Syntax error:{_C.R} {e}");sys.exit(1)
 except Exception as e:print(f"{_C.RED}{_C.B}✗ Error compiling expression:{_C.R} {e}");sys.exit(1)
 _pi(ex,a.sr,a.duration,a.tstart)
 try:_P._pr(bf,a.duration,a.sr,a.tstart)
 except Exception as e:print(f"\n{_C.RED}{_C.B}✗ Playback error:{_C.R} {e}");sys.exit(1)
if __name__=='__main__':main()
