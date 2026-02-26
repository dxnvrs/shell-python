import sys
import os
import subprocess
import shlex
import readline

tab_count = 0
last_text = ""
command_history = []

# List of built-in commands we support.
BUILTINS = ['echo', 'exit', 'type', 'pwd', 'cd', 'history']
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

def find_in_path(cmd):
    pathEnv = os.environ.get("PATH", "").split(os.pathsep)
    for d in pathEnv:
        p = os.path.join(d, cmd)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None

def run_builtin(cmd, args):
    if cmd == 'echo':
        output = " ".join(args)
        sys.stdout.write(output + "\n")
    elif cmd == 'exit':
        sys.exit(0)
    elif cmd == 'pwd':
        sys.stdout.write(os.getcwd() + "\n")
    elif cmd == 'cd':
        path = os.path.expanduser('~') if not args or args[0] == '~' else os.path.expanduser(args[0])
        try:
            os.chdir(path)
        except FileNotFoundError:
            sys.stderr.write(f"cd: {path}: No such file or directory\n")
    elif cmd == 'history':
        if args and args[0].isdigit():
            n = int(args[0])
            display_list = command_history[-n:] if n>0 else []
            start_index = len(command_history) - len(display_list) + 1
        else:
            display_list = command_history
            start_index = 1
        for i, entry in enumerate(display_list, start_index):
            sys.stdout.write(f"{i:5} {entry}\n")
    elif cmd == 'type':
        target = args[0]
        if target in BUILTINS:
            sys.stdout.write(f"{target} is a shell builtin\n")
        else:
            path = find_in_path(target)
            if path:
                sys.stdout.write(f"{target} is {path}\n")
            else:
                sys.stdout.write(f"{target}: not found\n")
    sys.stdout.flush()

def execute_command(args, stdin=None, stdout=None, stderr=None):
        cmd_name = args[0]

        if cmd_name in BUILTINS:
            old_stdin, old_stdout = sys.stdin, sys.stdout
            try:
                if stdin is not None:
                    sys.stdin = os.fdopen(os.dup(stdin), 'r') if isinstance(stdin, int) else stdin
                if stdout is not None:
                    sys.stdout = os.fdopen(os.dup(stdout), 'w') if isinstance(stdout, int) else stdout
                run_builtin(cmd_name, args[1:])
            finally:
                if sys.stdin != old_stdin: sys.stdin.close()
                if sys.stdout != old_stdout: sys.stdout.close()
                sys.stdin, sys.stdout = old_stdin, old_stdout
            return None
        else:

            path = find_in_path(cmd_name)
            if path:
                return subprocess.Popen(
                    args,
                    executable=path,
                    stdin=stdin if stdin is not None else sys.stdin,
                    stdout=stdout if stdout is not None else sys.stdout,
                    stderr=stderr if stderr is not None else sys.stderr
                )
            else:
                sys.stderr.write(f"{cmd_name}: command not found\n")
                sys.stderr.flush()
                return None
def parse_redirections(args):
    final_args = []
    stdout_file = None
    stdout_mode = 'w'
    stderr_file = None
    stderr_mode = 'w'

    idx = 0
    while idx < len(args):
        if args[idx] in ['>', '1>']:
            stdout_file, stdout_mode, idx = args[idx+1], 'w', idx + 2
        elif args[idx] in ['>>', '1>>']:
            stdout_file, stdout_mode, idx = args[idx+1], 'a', idx + 2
        elif args[idx] == '2>':
            stderr_file, stderr_mode, idx = args[idx+1], 'w', idx + 2
        elif args[idx] == '2>>':
            stderr_file, stderr_mode, idx = args[idx+1], 'a', idx + 2
        else:
            final_args.append(args[idx])
            idx += 1
    return final_args, stdout_file, stdout_mode, stderr_file, stderr_mode

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
def main():

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

        command_history.append(command_line)
        readline.add_history(command_line)

        # multi-stage pipeline logic
        if '|' in command_line:
            cmd_parts = command_line.split("|")
            cmds = [shlex.split(c.strip()) for c in cmd_parts]

            processes = []
            prev_read_fd = None

            for i, cmd_args in enumerate(cmds):
                is_first = (i == 0)
                is_last = (i == len(cmds) - 1)

                current_stdin = prev_read_fd if not is_first else None

                current_stdout = None
                if not is_last:
                    r_fd, w_fd = os.pipe()
                    current_stdout = w_fd
                    prev_read_fd = r_fd
                else:
                    cmd_args, out_f, out_m, err_f, err_m = parse_redirections(cmd_args)
                    if out_f:
                        os.makedirs(os.path.dirname(os.path.abspath(out_f)), exist_ok=True)
                        current_stdout = open(out_f, out_m)
                p = execute_command(cmd_args, stdin=current_stdin, stdout=current_stdout)

                if not is_last and isinstance(current_stdout, int):
                    os.close(current_stdout)
                if current_stdin is not None:
                    os.close(current_stdin)

                if p:
                    processes.append((p, current_stdout if not isinstance(current_stdout, int) else None))
                else:
                    if is_last and current_stdout and not isinstance(current_stdout, int):
                        current_stdout.close()

            for proc, file_handle in processes:
                proc.wait()
                if file_handle:
                    file_handle.close()
            
            tab_count = 0
            last_text = ""
            continue

        try:
            parts = shlex.split(command_line)
        except ValueError: continue

        args, out_f, out_m, err_f, err_m = parse_redirections(parts)

        out_h = None
        if out_f:
            os.makedirs(os.path.dirname(os.path.abspath(out_f)), exist_ok=True)
            out_h = open(out_f, out_m)

        err_h = None
        if err_f:
            os.makedirs(os.path.dirname(os.path.abspath(err_f)), exist_ok=True)
            err_h = open(err_f, err_m)

        p = execute_command(args, stdout=out_h, stderr=err_h)

        if p:
            p.wait()

        if out_h: out_h.close()
        if err_h: err_h.close()


if __name__ == "__main__":
    main()