import sys
import os
import subprocess
import shlex
import readline

tab_count = 0
last_text = ""

def get_lcp(strs):
    if not strs:
        return ""
    
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix

def main():
    # List of built-in commands we support.
    BUILTINS = ['echo', 'exit', 'type', 'pwd', 'cd']

    def get_matches(text):
        execs = set(BUILTINS)
        pathEnv = os.environ.get("PATH", "").split(os.pathsep)

        for directory in pathEnv:
            if os.path.isdir(directory):
                try:
                    for filename in os.listdir(directory):
                        if filename.startswith(text):
                            full_path = os.path.join(directory, filename)
                            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                                execs.add(filename)
                except:
                    continue
        return sorted([c for c in execs if c.startswith(text)])
    
    def completer(text, state):
        global tab_count, last_text
        matches = get_matches(text)

        if not matches:
            return None
        
        if state == 0:
            if text == last_text:
                tab_count += 1
            else:
                tab_count = 1
                last_text = text
            
            if len(matches) == 1:
                return matches[0] + " "
                
            lcp = get_lcp(matches)
            if lcp != text:
                return lcp

            if tab_count == 1:
                sys.stdout.write("\x07")
                sys.stdout.flush()
                return None
            elif tab_count >= 2:
                print()
                print("  ".join(matches))
                sys.stdout.write(f"$ {readline.get_line_buffer()}")
                sys.stdout.flush()

                tab_count = 0
                return None
        return None

    readline.set_completer(completer)
    readline.parse_and_bind('set show-all-if-ambiguous off')

    if "libedit" in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        line = input()
        if not line:
            break
        
        command_line = line.strip()
        
        if not command_line:
            continue

        try:
            tab_count = 0
            last_text = ""
            parts = shlex.split(command_line)
        except ValueError:
            continue

        stdout_file = None
        stderr_file = None
        stdout_mode = 'w'
        stderr_mode = "w"
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
                    stderr_mode = 'w'
                    idx += 2
                else:
                    idx += 1
            elif parts[idx] == '2>>':
                if idx + 1 < len(parts):
                    stderr_file = parts[idx + 1]
                    stderr_mode = 'a'
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
                with open(stderr_file, stderr_mode) as f:
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
                        err_f = open(stderr_file, stderr_mode)

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