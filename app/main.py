import sys
import os
import subprocess
import shlex

BUILTIN = ['echo', 'exit', 'type', 'pwd', 'cd']

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        line = sys.stdin.readline()
        if not line: break
        command_line = line.strip()
        if not command_line: continue

        # shlex split ajuda com aspas, mas vamos limpar os operadores manualmente depois
        parts = shlex.split(command_line)
        
        stdout_file = None
        stderr_file = None
        clean_parts = []
        
        i = 0
        while i < len(parts):
            # Trata > e 1>
            if parts[i] in ['>', '1>']:
                if i + 1 < len(parts):
                    stdout_file = parts[i+1]
                    i += 2
                    continue
            # Trata 2>
            elif parts[i] == '2>':
                if i + 1 < len(parts):
                    stderr_file = parts[i+1]
                    i += 2
                    continue
            # Caso o operador esteja colado: '2>/tmp/file' (shlex às vezes mantém junto)
            elif parts[i].startswith('2>') and len(parts[i]) > 2:
                stderr_file = parts[i][2:]
                i += 1
                continue
            elif (parts[i].startswith('>') or parts[i].startswith('1>')) and len(parts[i]) > 1:
                # Ajuste para >/tmp/file ou 1>/tmp/file
                stdout_file = parts[i].split('>', 1)[1]
                i += 1
                continue
            
            clean_parts.append(parts[i])
            i += 1

        if not clean_parts: continue
        cmd_name = clean_parts[0]
        args = clean_parts[1:]

        # --- Helper para garantir que o arquivo e diretório existam ---
        def get_file_handle(path):
            if not path: return None
            # Força o caminho absoluto para evitar erros de diretório
            abs_path = os.path.abspath(path)
            parent = os.path.dirname(abs_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            return open(abs_path, 'w')

        # --- Lógica de Execução ---
        if cmd_name == 'echo':
            output = " ".join(args) + "\n"
            if stdout_file:
                with get_file_handle(stdout_file) as f: f.write(output)
            else:
                sys.stdout.write(output)
        
        elif cmd_name == 'exit':
            sys.exit(0)
            
        elif cmd_name == 'pwd':
            output = os.getcwd() + "\n"
            if stdout_file:
                with get_file_handle(stdout_file) as f: f.write(output)
            else:
                sys.stdout.write(output)

        elif cmd_name == 'cd':
            dest = os.path.expanduser('~') if not args or args[0] == '~' else args[0]
            try:
                os.chdir(dest)
            except FileNotFoundError:
                err_msg = f"cd: {dest}: No such file or directory\n"
                if stderr_file:
                    with get_file_handle(stderr_file) as f: f.write(err_msg)
                else:
                    sys.stderr.write(err_msg)

        elif cmd_name == 'type':
            target = args[0]
            msg = ""
            if target in BUILTIN:
                msg = f"{target} is a shell builtin\n"
            else:
                path_env = os.environ.get("PATH", "").split(os.pathsep)
                found = None
                for d in path_env:
                    p = os.path.join(d, target)
                    if os.path.isfile(p) and os.access(p, os.X_OK):
                        found = p
                        break
                msg = f"{target} is {found}\n" if found else f"{target}: not found\n"
            
            if stdout_file:
                with get_file_handle(stdout_file) as f: f.write(msg)
            else:
                sys.stdout.write(msg)

        else:
            # Comandos Externos
            path_env = os.environ.get("PATH", "").split(os.pathsep)
            found_path = None
            for d in path_env:
                p = os.path.join(d, cmd_name)
                if os.path.isfile(p) and os.access(p, os.X_OK):
                    found_path = p
                    break
            
            if found_path:
                out_h = get_file_handle(stdout_file)
                err_h = get_file_handle(stderr_file)
                try:
                    subprocess.run(
                        [cmd_name] + args,
                        executable=found_path,
                        stdout=out_h if out_h else sys.stdout,
                        stderr=err_h if err_h else sys.stderr
                    )
                finally:
                    if out_h: out_h.close()
                    if err_h: err_h.close()
            else:
                err_msg = f"{cmd_name}: command not found\n"
                if stderr_file:
                    with get_file_handle(stderr_file) as f: f.write(err_msg)
                else:
                    sys.stderr.write(err_msg)

if __name__ == "__main__":
    main()