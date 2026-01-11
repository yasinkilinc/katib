import os
import sys
import compileall

def check_syntax(directory):
    print(f"[*] Verifying syntax in: {directory}")
    # force=True makes it recompile even if timestamps match
    # legacy=True writes .pyc files to __pycache__ (standard behavior)
    # quiet=1 prints errors only
    success = compileall.compile_dir(directory, force=True, quiet=1)
    
    if success:
        print("[✓] Syntax OK.")
        return True
    else:
        print("[!] Syntax Errors Detected!")
        return False

if __name__ == "__main__":
    src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    if not check_syntax(src_dir):
        sys.exit(1)
    sys.exit(0)
