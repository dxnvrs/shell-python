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
            line = sys.stdin.readline()
            if not line: break
            command = line.strip()
        except EOFError:
            break

        if not command: continue
        parts = shlex.split(command)
        if not parts: continue

        stdoutFile = None
        stderrFile = None

        # 1. Extração rigorosa dos redirecionadores
        new_parts = []
        i = 0
        while i < len(parts):
            if parts[i] in ['>', '1>'] and i + 1 < len(parts):
                stdoutFile = parts[i+1]
                i += 2
            elif parts[i] == '2>' and i + 1 < len(parts):
                stderrFile = parts[i+1]
                i += 2
            else:
                new_parts.append(parts[i])
                i += 1
        
        parts = new_parts
        if not parts: continue
        cmdName = parts[0]
        args = parts[1:]

        # 2. Função de impressão que respeita os redirecionamentos
        def shellPrint(content, isError=False):
            target = stderrFile if isError else stdoutFile
            if target:
                pDir = os.path.dirname(os.path.abspath(target))
                if pDir: os.makedirs(pDir, exist_ok=True)
                with open(target, 'w') as f:
                    f.write(content + '\n')
            else:
                if isError:
                    sys.stderr.write(content + '\n')
                    sys.stderr.flush()
                else:
                    sys.stdout.write(content + '\n')
                    sys.stdout.flush()

        # --- Lógica de Comandos ---
        if cmdName == 'echo':
            shellPrint(" ".join(args))
        elif cmdName == 'exit':
            sys.exit(0)
        elif cmdName == 'pwd':
            shellPrint(os.getcwd())
        elif cmdName == 'cd':
            dest = os.path.expanduser('~') if not args or args[0] == '~' else args[0]
            try:
                os.chdir(dest)
            except FileNotFoundError:
                shellPrint(f"cd: {dest}: No such file or directory", isError=True)
        elif cmdName == 'type':
            target = args[0]
            if target in BUILTIN:
                shellPrint(f"{target} is a shell builtin")
            else:
                found = False
                for d in dirs:
                    p = os.path.join(d, target)
                    if os.path.isfile(p) and os.access(p, os.X_OK):
                        shellPrint(f"{target} is {p}")
                        found = True
                        break
                if not found: shellPrint(f"{target}: not found")
        
        # --- Programas Externos ---
        else:
            foundPath = None
            for d in dirs:
                p = os.path.join(d, cmdName)
                if os.path.isfile(p) and os.access(p, os.X_OK):
                    foundPath = p
                    break
            
            if foundPath:
                out_f = None
                err_f = None
                try:
                    if stdoutFile:
                        os.makedirs(os.path.dirname(os.path.abspath(stdoutFile)), exist_ok=True)
                        out_f = open(stdoutFile, 'w')
                    if stderrFile:
                        os.makedirs(os.path.dirname(os.path.abspath(stderrFile)), exist_ok=True)
                        err_f = open(stderrFile, 'w')

                    subprocess.run(
                        [cmdName] + args,
                        executable=foundPath,
                        stdout=out_f if out_f else sys.stdout,
                        stderr=err_f if err_f else sys.stderr
                    )
                finally:
                    if out_f: out_f.close()
                    if err_f: err_f.close()
            else:
                # Se o comando não existe, o erro deve ir para o stderrFile se ele existir!
                shellPrint(f"{cmdName}: command not found", isError=True)

if __name__ == "__main__":
    main()