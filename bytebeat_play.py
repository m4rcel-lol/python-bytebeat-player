from __future__ import annotations
import ast, argparse, math, sys, wave, struct, subprocess, tempfile, os, platform
try:
    import numpy as _np
except ImportError:
    _np = None
try:
    import sounddevice as _sd
except ImportError:
    _sd = None
if platform.system().lower()=="windows":
    import winsound as _ws
    os.system("")
_Z = {ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.LShift,ast.RShift,ast.BitOr,ast.BitAnd,ast.BitXor,ast.Pow}
_Y = {ast.UAdd,ast.USub,ast.Invert,ast.Not}
_C = {"r":"\033[0m","g":"\033[92m","c":"\033[96m","y":"\033[93m","R":"\033[91m","B":"\033[1m"}
def _a(n):
    if isinstance(n,ast.Expression): _a(n.body); return
    if isinstance(n,ast.BinOp):
        if type(n.op) not in _Z: raise ValueError(type(n.op).__name__)
        _a(n.left); _a(n.right); return
    if isinstance(n,ast.UnaryOp):
        if type(n.op) not in _Y: raise ValueError(type(n.op).__name__)
        _a(n.operand); return
    if isinstance(n,ast.Constant):
        if not isinstance(n.value,(int,float)): raise ValueError("c")
        return
    if isinstance(n,ast.Name):
        if n.id!='t': raise ValueError(n.id)
        return
    if isinstance(n,(ast.Call,ast.Attribute,ast.Compare,ast.BoolOp,ast.IfExp)): raise ValueError(type(n).__name__)
    if not isinstance(n,(ast.Load,)): raise ValueError(type(n).__name__)
def _b(s):
    s=s.replace("/","//"); p=ast.parse(s,mode='eval'); _a(p); co=compile(p,'<b>','eval')
    def _e(t):
        L={'t':int(t)}
        try:
            r=eval(co,{"__builtins__":None,'math':math},L); return int(r)
        except Exception:
            return 0
    return _e
def _g(f,d=10.0,sr=8000,t0=0):
    cs=sr//4; n=int(d*sr); tc=n//cs
    if _np is not None:
        for i in range(tc):
            b=t0+i*cs; a=_np.empty(cs,dtype=_np.int16)
            for j in range(cs):
                v=f(b+j); a[j]=_np.int16(((int(v)&0xFF)-128)*256)
            yield i/float(tc),a
    else:
        for i in range(tc):
            b=t0+i*cs
            ch=[((int(f(b+j))&0xFF)-128)*256 for j in range(cs)]
            yield i/float(tc),ch
def _p(f,d,sr,t0):
    if _sd is None or _np is None:
        print(f"{_C['y']}sounddevice not installed — using WAV fallback.{_C['r']}")
        allv=[]
        try:
            for pr,ch in _g(f,d,sr,t0):
                allv.extend(ch)
                bar="█"*int(40*pr)+"-"*int(40*(1-pr))
                print(f"\r{_C['c']}[ {bar} ] {int(pr*100)}%{_C['r']}",end="",flush=True)
        except KeyboardInterrupt:
            print(f"\n{_C['R']}Stopped by user!{_C['r']}")
        print()
        _w(allv,sr); return
    print(f"{_C['B']}{_C['g']}▶ Playing live... Press Ctrl+C to stop.{_C['r']}")
    st=_sd.OutputStream(samplerate=sr,channels=1,dtype='float32'); st.start()
    try:
        for pr,ch in _g(f,d,sr,t0):
            bar="█"*int(40*pr)+"-"*int(40*(1-pr))
            print(f"\r{_C['c']}[ {bar} ] {int(pr*100)}%{_C['r']}",end="",flush=True)
            st.write(ch.astype('float32')/32768.0)
    except KeyboardInterrupt:
        print(f"\n{_C['R']}⏹ Interrupted by user!{_C['r']}")
    finally:
        st.stop(); st.close(); print(f"{_C['g']}Done.{_C['r']}")
def _w(samps,sr):
    with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as t: fn=t.name
    frames = samps.tobytes() if not isinstance(samps,list) else b''.join(struct.pack('<h',x) for x in samps)
    with wave.open(fn,'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(frames)
    played=False; sysn=platform.system().lower()
    if sysn=="windows":
        try: _ws.PlaySound(fn,_ws.SND_FILENAME); played=True
        except Exception: pass
    elif sysn=="darwin":
        try: subprocess.run(['afplay',fn],check=True); played=True
        except Exception: pass
    else:
        try: subprocess.run(['aplay',fn],check=True); played=True
        except Exception:
            try: subprocess.run(['ffplay','-nodisp','-autoexit','-hide_banner','-loglevel','panic',fn],check=True); played=True
            except Exception: pass
    if not played: print(f"{_C['y']}Couldn't auto-play. WAV written to: {fn}{_C['r']}")
def _m():
    p=argparse.ArgumentParser(description=""); p.add_argument('file'); p.add_argument('--duration',type=float,default=60.0); p.add_argument('--sr',type=int,default=8000); p.add_argument('--tstart',type=int,default=0)
    a=p.parse_args()
    try:
        with open(a.file,'r') as f: expr=f.read().strip()
    except Exception as e:
        print(f"{_C['R']}Could not read file:{_C['r']}",e); sys.exit(1)
    try:
        ev=_b(expr)
    except Exception as e:
        print(f"{_C['R']}Error parsing expression:{_C['r']}",e); sys.exit(1)
    print(f"{_C['B']}{_C['g']}Bytebeat Player Ready!{_C['r']}")
    print(f"{_C['c']}Expression:{_C['r']} {expr}")
    print(f"{_C['c']}Sample Rate:{_C['r']} {a.sr} Hz")
    print(f"{_C['c']}Duration:{_C['r']} {a.duration:.1f} s\n")
    _p(ev,a.duration,a.sr,a.tstart)
if __name__=='__main__': _m()
