import sys
import os
import subprocess
import shlex

BUILTIN = ['echo', 'exit', 'type', 'pwd', 'cd']

def main():
    while True:
        rcvPATH = os.environ.get('PATH', '')
        dirs = rcvPATH.split(os.pathsep)
        
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        try:
            command = input()
        except EOFError:
            break

        parts = shlex.split(command)
        if not parts: continue

        stdoutFile = None
        stderrFile = None

        # Captura redirecionamento de saída
        for op in ['>', '1>']:
            if op in parts:
                idx = parts.index(op)
                stdoutFile = parts[idx + 1]
                parts = parts[:idx] + parts[idx+2:]
                break

        # Captura redirecionamento de erro
        if '2>' in parts:
            idx = parts.index('2>')
            stderrFile = parts[idx + 1]
            parts = parts[:idx] + parts[idx+2:]
        
        if not parts: continue
        cmdName = parts[0]
        args = parts[1:]

        def shellPrint(content, isError=False):
            targetPath = stderrFile if isError else stdoutFile
            if targetPath:
                pDir = os.path.dirname(targetPath)
                if pDir:
                    os.makedirs(pDir, exist_ok=True)
                with open(targetPath, 'w') as f:
                    f.write(content + '\n')
            else:
                if isError:
                    sys.stderr.write(content + '\n')
                    sys.stderr.flush()
                else:
                    print(content)

        if cmdName == 'echo':
            shellPrint(" ".join(args))
        elif cmdName == 'exit':
            if args and args[0] == '0':
                sys.exit(0)
            break
        elif cmdName == 'type':
            target = args[0]
            if target in BUILTIN:
                shellPrint(f"{target} is a shell builtin")
            else:
                found_path = next((os.path.join(d, target) for d in dirs if os.path.isfile(os.path.join(d, target)) and os.access(os.path.join(d, target), os.X_OK)), None)
                if found_path:
                    shellPrint(f"{target} is {found_path}")
                else:
                    shellPrint(f"{target}: not found")
        elif cmdName == 'pwd':
            shellPrint(os.getcwd())
        elif cmdName == 'cd':
            dest = os.path.expanduser('~') if not args or args[0] == '~' else args[0]
            try:
                os.chdir(dest)
            except FileNotFoundError:
                shellPrint(f"cd: {dest}: No such file or directory", isError=True)

        else: 
            foundPath = next((os.path.join(d, cmdName) for d in dirs if os.path.isfile(os.path.join(d, cmdName)) and os.access(os.path.join(d, cmdName), os.X_OK)), None)
            
            if foundPath:
                out_s = None
                err_s = None
                try:
                    # ORDEM CORRETA: 1.makedirs -> 2.open
                    if stdoutFile:
                        pDir = os.path.dirname(stdoutFile)
                        if pDir: os.makedirs(pDir, exist_ok=True)
                        out_s = open(stdoutFile, 'w')
                    
                    if stderrFile:
                        pDir = os.path.dirname(stderrFile)
                        if pDir: os.makedirs(pDir, exist_ok=True)
                        err_s = open(stderrFile, 'w')
                    
                    subprocess.run(
                        [cmdName] + args, 
                        executable=foundPath, 
                        stdout=out_s if out_s else sys.stdout,
                        stderr=err_s if err_s else sys.stderr
                    )
                finally:
                    if out_s: out_s.close()
                    if err_s: err_s.close()
            else:
                print(f"{cmdName}: command not found")

if __name__ == "__main__":
    main()