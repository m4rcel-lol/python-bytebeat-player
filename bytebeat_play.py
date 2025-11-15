from __future__ import annotations
import ast
import argparse
import math
import sys
import wave
import struct
import subprocess
import tempfile
import os
import platform
from typing import Callable, Iterator, Tuple, List, Union, TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
else:
    np = Any

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    SOUNDDEVICE_AVAILABLE = False

if platform.system().lower() == "windows":
    import winsound
    os.system("")


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    BLACK = "\033[30m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    @classmethod
    def gradient_bar(cls, progress: float, width: int = 40) -> str:
        filled = int(width * progress)
        empty = width - filled
        bar = f"{cls.CYAN}{'█' * filled}{cls.DIM}{'░' * empty}{cls.RESET}"
        return bar


class BytebeatValidator:
    
    ALLOWED_BINARY_OPS = {
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
        ast.Mod, ast.LShift, ast.RShift, ast.BitOr,
        ast.BitAnd, ast.BitXor, ast.Pow
    }
    
    ALLOWED_UNARY_OPS = {
        ast.UAdd, ast.USub, ast.Invert, ast.Not
    }
    
    @staticmethod
    def validate_ast_node(node: ast.AST) -> None:
        if isinstance(node, ast.Expression):
            BytebeatValidator.validate_ast_node(node.body)
            return
        
        if isinstance(node, ast.BinOp):
            if type(node.op) not in BytebeatValidator.ALLOWED_BINARY_OPS:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            BytebeatValidator.validate_ast_node(node.left)
            BytebeatValidator.validate_ast_node(node.right)
            return
        
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in BytebeatValidator.ALLOWED_UNARY_OPS:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            BytebeatValidator.validate_ast_node(node.operand)
            return
        
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
            return
        
        if isinstance(node, ast.Name):
            if node.id != 't':
                raise ValueError(f"Only variable 't' is allowed, found: {node.id}")
            return
        
        if isinstance(node, (ast.Call, ast.Attribute, ast.Compare, ast.BoolOp, ast.IfExp)):
            raise ValueError(f"Unsupported operation: {type(node).__name__}")
        
        if not isinstance(node, (ast.Load,)):
            raise ValueError(f"Unsupported node type: {type(node).__name__}")
    
    @staticmethod
    def compile_expression(expression: str) -> Callable[[int], int]:
        expression = expression.replace("/", "//")
        
        parsed = ast.parse(expression, mode='eval')
        BytebeatValidator.validate_ast_node(parsed)
        
        compiled_code = compile(parsed, '<bytebeat>', 'eval')
        
        def evaluate(t: int) -> int:
            local_vars = {'t': int(t)}
            try:
                result = eval(compiled_code, {"__builtins__": None, 'math': math}, local_vars)
                return int(result)
            except Exception:
                return 0
        
        return evaluate


class BytebeatGenerator:
    @staticmethod
    def generate_chunks(
        func: Callable[[int], int],
        duration: float = 10.0,
        sample_rate: int = 8000,
        time_offset: int = 0
    ) -> Iterator[Tuple[float, Union[Any, List[int]]]]:
        chunk_size = sample_rate // 4
        total_samples = int(duration * sample_rate)
        total_chunks = total_samples // chunk_size
        
        if NUMPY_AVAILABLE:
            for chunk_idx in range(total_chunks):
                base_time = time_offset + chunk_idx * chunk_size
                chunk = np.empty(chunk_size, dtype=np.int16)
                
                for sample_idx in range(chunk_size):
                    value = func(base_time + sample_idx)
                    chunk[sample_idx] = np.int16(((int(value) & 0xFF) - 128) * 256)
                
                progress = (chunk_idx + 1) / float(total_chunks)
                yield progress, chunk
        else:
            for chunk_idx in range(total_chunks):
                base_time = time_offset + chunk_idx * chunk_size
                chunk = [((int(func(base_time + j)) & 0xFF) - 128) * 256 for j in range(chunk_size)]
                
                progress = (chunk_idx + 1) / float(total_chunks)
                yield progress, chunk


class AudioPlayer:
    @staticmethod
    def play_realtime(
        func: Callable[[int], int],
        duration: float,
        sample_rate: int,
        time_offset: int
    ) -> None:
        if not SOUNDDEVICE_AVAILABLE or not NUMPY_AVAILABLE:
            print(f"{Colors.YELLOW}⚠ sounddevice/numpy not installed — using WAV fallback{Colors.RESET}")
            AudioPlayer.play_wav_fallback(func, duration, sample_rate, time_offset)
            return
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}▶ Playing live audio... {Colors.DIM}(Press Ctrl+C to stop){Colors.RESET}")
        
        stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32')
        stream.start()
        
        try:
            for progress, chunk in BytebeatGenerator.generate_chunks(func, duration, sample_rate, time_offset):
                bar = Colors.gradient_bar(progress)
                percentage = int(progress * 100)
                print(f"\r{Colors.CYAN}Progress: {Colors.RESET}[ {bar} {Colors.CYAN}] {percentage}%{Colors.RESET}", end="", flush=True)
                
                stream.write(chunk.astype('float32') / 32768.0)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⏹ Playback interrupted by user{Colors.RESET}")
        
        finally:
            stream.stop()
            stream.close()
            print(f"\n{Colors.GREEN}✓ Playback complete{Colors.RESET}\n")
    
    @staticmethod
    def play_wav_fallback(
        func: Callable[[int], int],
        duration: float,
        sample_rate: int,
        time_offset: int
    ) -> None:
        print(f"\n{Colors.CYAN}Rendering audio...{Colors.RESET}")
        all_samples = []
        
        try:
            for progress, chunk in BytebeatGenerator.generate_chunks(func, duration, sample_rate, time_offset):
                all_samples.extend(chunk)
                bar = Colors.gradient_bar(progress)
                percentage = int(progress * 100)
                print(f"\r{Colors.CYAN}Rendering: {Colors.RESET}[ {bar} {Colors.CYAN}] {percentage}%{Colors.RESET}", end="", flush=True)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⏹ Rendering interrupted{Colors.RESET}")
        
        print(f"\n{Colors.GREEN}✓ Rendering complete{Colors.RESET}")
        AudioPlayer._play_wav_file(all_samples, sample_rate)
    
    @staticmethod
    def _play_wav_file(samples: Union[Any, List[int]], sample_rate: int) -> None:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        if isinstance(samples, list):
            frames = b''.join(struct.pack('<h', sample) for sample in samples)
        else:
            frames = samples.tobytes()
        
        with wave.open(temp_filename, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(frames)
        
        print(f"{Colors.CYAN}Playing WAV file...{Colors.RESET}")
        
        played = False
        system_name = platform.system().lower()
        
        if system_name == "windows":
            try:
                winsound.PlaySound(temp_filename, winsound.SND_FILENAME)
                played = True
            except Exception:
                pass
        
        elif system_name == "darwin":
            try:
                subprocess.run(['afplay', temp_filename], check=True)
                played = True
            except Exception:
                pass
        
        else:
            try:
                subprocess.run(['aplay', temp_filename], check=True)
                played = True
            except Exception:
                try:
                    subprocess.run(['ffplay', '-nodisp', '-autoexit', '-hide_banner', '-loglevel', 'panic', temp_filename], check=True)
                    played = True
                except Exception:
                    pass
        
        if not played:
            print(f"{Colors.YELLOW}⚠ Could not auto-play. WAV file saved to: {temp_filename}{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}✓ Playback complete{Colors.RESET}\n")


def print_banner() -> None:
    print(f"""
{Colors.MAGENTA}██████╗ ██╗   ██╗████████╗███████╗██████╗ ███████╗ █████╗ ████████╗
██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔════╝██╔══██╗██╔════╝██╔══██╗╚══██╔══╝
██████╔╝ ╚████╔╝    ██║   █████╗  ██████╔╝█████╗  ███████║   ██║   
██╔══██╗  ╚██╔╝     ██║   ██╔══╝  ██╔══██╗██╔══╝  ██╔══██║   ██║   
██████╔╝   ██║      ██║   ███████╗██████╔╝███████╗██║  ██║   ██║   
╚═════╝    ╚═╝      ╚═╝   ╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   
{Colors.YELLOW}                   ╔═╗╦  ╔═╗╦ ╦╔═╗╦═╗
                   ╠═╝║  ╠═╣╚╦╝║╣ ╠╦╝
                   ╩  ╩═╝╩ ╩ ╩ ╚═╝╩╚═{Colors.RESET}
""")


def print_info(expression: str, sample_rate: int, duration: float, time_offset: int) -> None:
    print(f"\n{Colors.BOLD}{Colors.YELLOW}Configuration:{Colors.RESET}")
    print(f"  {Colors.BOLD}Expression:{Colors.RESET}   {Colors.GREEN}{expression}{Colors.RESET}")
    print(f"  {Colors.BOLD}Sample Rate:{Colors.RESET}  {Colors.MAGENTA}{sample_rate}{Colors.RESET} Hz")
    print(f"  {Colors.BOLD}Duration:{Colors.RESET}     {Colors.MAGENTA}{duration:.1f}{Colors.RESET} seconds")
    print(f"  {Colors.BOLD}Time Offset:{Colors.RESET}  {Colors.MAGENTA}{time_offset}{Colors.RESET}")

    status_np = f"{Colors.GREEN}✓{Colors.RESET}" if NUMPY_AVAILABLE else f"{Colors.RED}✗{Colors.RESET}"
    status_sd = f"{Colors.GREEN}✓{Colors.RESET}" if SOUNDDEVICE_AVAILABLE else f"{Colors.RED}✗{Colors.RESET}"

    print(f"  {Colors.BOLD}Status:{Colors.RESET} NumPy {status_np} Sounddevice {status_sd}")


def print_styled_help():
    print(f"""
{Colors.MAGENTA}{Colors.BOLD}BYTEBEAT PLAYER{Colors.RESET} - 8-bit audio from math

{Colors.BOLD}{Colors.YELLOW}USAGE:{Colors.RESET}
  python bytebeat_play.py {Colors.GREEN}<file>{Colors.RESET} [{Colors.CYAN}options{Colors.RESET}]

{Colors.BOLD}{Colors.YELLOW}ARGUMENTS:{Colors.RESET}
  {Colors.GREEN}<file>{Colors.RESET} Path to bytebeat expression file

{Colors.BOLD}{Colors.YELLOW}OPTIONS:{Colors.RESET}
  {Colors.CYAN}--duration{Colors.RESET} {Colors.DIM}<float>{Colors.RESET}  Duration in seconds (default: 60.0)
  {Colors.CYAN}--sr{Colors.RESET}       {Colors.DIM}<int>{Colors.RESET}    Sample rate in Hz (default: 8000)
  {Colors.CYAN}--tstart{Colors.RESET}   {Colors.DIM}<int>{Colors.RESET}    Time offset (default: 0)
  {Colors.CYAN}-h, --help{Colors.RESET} Show this help message

{Colors.BOLD}{Colors.YELLOW}EXAMPLES:{Colors.RESET}
  python bytebeat_play.py {Colors.GREEN}song.byteb{Colors.RESET}
  python bytebeat_play.py {Colors.GREEN}song.byteb{Colors.RESET} {Colors.CYAN}--duration 30{Colors.RESET}
  python bytebeat_play.py {Colors.GREEN}song.byteb{Colors.RESET} {Colors.CYAN}--sr 16000{Colors.RESET}

{Colors.BOLD}{Colors.YELLOW}EXPRESSION EXAMPLE:{Colors.RESET}
  {Colors.MAGENTA}t*(t>>8|t>>9)&46&t>>8{Colors.RESET}
""")



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bytebeat Player",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')
    parser.add_argument('file', nargs='?', help='Path to bytebeat expression file')
    parser.add_argument('--duration', type=float, default=60.0, help='Duration in seconds')
    parser.add_argument('--sr', type=int, default=8000, help='Sample rate in Hz')
    parser.add_argument('--tstart', type=int, default=0, help='Starting time offset')
    
    args = parser.parse_args()
    
    if args.help or not args.file:
        print_styled_help()
        sys.exit(0)
    
    print_banner()
    
    try:
        with open(args.file, 'r') as file:
            expression = file.read().strip()
    except FileNotFoundError:
        print(f"{Colors.RED}{Colors.BOLD}✗ Error:{Colors.RESET} File not found: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}{Colors.BOLD}✗ Error reading file:{Colors.RESET} {e}")
        sys.exit(1)
    
    if not expression:
        print(f"{Colors.RED}{Colors.BOLD}✗ Error:{Colors.RESET} Expression file is empty")
        sys.exit(1)
    
    try:
        bytebeat_func = BytebeatValidator.compile_expression(expression)
    except ValueError as e:
        print(f"{Colors.RED}{Colors.BOLD}✗ Invalid expression:{Colors.RESET} {e}")
        sys.exit(1)
    except SyntaxError as e:
        print(f"{Colors.RED}{Colors.BOLD}✗ Syntax error:{Colors.RESET} {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}{Colors.BOLD}✗ Error compiling expression:{Colors.RESET} {e}")
        sys.exit(1)
    
    print_info(expression, args.sr, args.duration, args.tstart)
    
    try:
        AudioPlayer.play_realtime(bytebeat_func, args.duration, args.sr, args.tstart)
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Playback error:{Colors.RESET} {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
