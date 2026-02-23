import sys
import os
import subprocess
import shlex

def main():
    # List of built-in commands we support.
    BUILTINS = ['echo', 'exit', 'type', 'pwd', 'cd']

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        line = sys.stdin.readline()
        if not line:
            break
        
        command_line = line.strip()
        if not command_line:
            continue

        try:
            parts = shlex.split(command_line)
        except ValueError:
            continue # Erro de aspas mal formadas

        stdout_file = None
        stderr_file = None
        stdout_mode = 'w'
        final_args = []
        
        # Extração de redirecionadores (trata >, 1>, 2>)
        idx = 0
        while idx < len(parts):
            if parts[idx] in ['>>', '1>>']:
                if idx + 1 < len(parts):
                    stdout_file = parts[idx + 1]
                    stdout_mode = 'a'
                    idx += 2
                else:
                    idx += 1
            elif parts[idx] in ['>', '1>']:
                if idx + 1 < len(parts):
                    stdout_file = parts[idx + 1]
                    stdout_mode = 'w'
                    idx += 2
                else:
                    idx += 1
            elif parts[idx] == '2>':
                if idx + 1 < len(parts):
                    stderr_file = parts[idx + 1]
                    idx += 2
                else:
                    idx += 1
            elif parts[idx] == '2>>':
                if idx + 1 < len(parts):
                    stderr_file = parts[idx + 1]
                    idx += 2
                else:
                    idx += 1
            else:
                final_args.append(parts[idx])
                idx += 1

        if not final_args:
            continue

        cmd, args = final_args[0], final_args[1:] 

        def execute_output(content_stdout=None, content_stderr=None):
            if stdout_file:
                parent = os.path.dirname(os.path.abspath(stdout_file))
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(stdout_file, stdout_mode) as f:
                    if content_stdout is not None:
                        f.write(content_stdout)
            elif content_stdout is not None:
                sys.stdout.write(content_stdout)
                sys.stdout.flush()
            
            if stderr_file:
                parent = os.path.dirname(os.path.abspath(stderr_file))
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(stderr_file, 'w') as f:
                    if content_stderr is not None:
                        f.write(content_stderr)
            elif content_stderr is not None:
                sys.stderr.write(content_stderr)
                sys.stderr.flush()

        # --- Lógica de Comandos ---
        if cmd == 'echo':
            execute_output(" ".join(args) + "\n")

        elif cmd == 'pwd':
            execute_output(os.getcwd() + "\n")

        elif cmd == 'exit':
            sys.exit(0)

        elif cmd == 'cd':
            path = os.path.expanduser('~') if not args or args[0] == '~' else args[0]
            try:
                os.chdir(path)
            except FileNotFoundError:
                execute_output(content_stderr=f"cd: {path}: No such file or directory\n")

        elif cmd == 'type':
            target = args[0]
            if target in BUILTINS:
                execute_output(content_stdout=f"{target} is a shell builtin\n")
            else:
                path_env = os.environ.get("PATH", "").split(os.pathsep)
                found = None
                for d in path_env:
                    p = os.path.join(d, target)
                    if os.path.isfile(p) and os.access(p, os.X_OK):
                        found = p
                        break
                if found:
                    execute_output(content_stdout=f"{target} is {found}\n")
                else:
                    execute_output(content_stdout=f"{target}: not found\n")

        else:
            # Comandos Externos
            path_env = os.environ.get("PATH", "").split(os.pathsep)
            found_path = None
            for d in path_env:
                p = os.path.join(d, cmd)
                if os.path.isfile(p) and os.access(p, os.X_OK):
                    found_path = p
                    break
            
            if found_path:
                out_f = None
                err_f = None
                try:
                    if stdout_file:
                        os.makedirs(os.path.dirname(os.path.abspath(stdout_file)), exist_ok=True)
                        out_f = open(stdout_file, stdout_mode)
                    if stderr_file:
                        os.makedirs(os.path.dirname(os.path.abspath(stderr_file)), exist_ok=True)
                        err_f = open(stderr_file, 'w')

                    # Passamos o nome do comando como argv[0] para satisfazer o tester
                    subprocess.run(
                        [cmd] + args,
                        executable=found_path,
                        stdout=out_f if out_f else sys.stdout,
                        stderr=err_f if err_f else sys.stderr
                    )
                finally:
                    if out_f: out_f.close()
                    if err_f: err_f.close()
            else:
                execute_output(content_stderr=f"{cmd}: command not found\n")

if __name__ == "__main__":
    main()