import sys
import os
import subprocess
import shlex
import readline

tab_count = 0
last_text = ""

# List of built-in commands we support.
BUILTINS = ['echo', 'exit', 'type', 'pwd', 'cd']
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
        output = " ".join(args).replace("\\n", "\n")
        sys.stdout.write(output + "\n")
    elif cmd == 'exit':
        sys.exit(0)
    elif cmd == 'pwd':
        sys.stdout.write(os.getcwd() + "\n")
    elif cmd == 'cd':
        path = args[0] if args else os.path.expanduser("~")
        try:
            os.chdir(path)
        except FileNotFoundError:
            sys.stderr.write(f"cd: {path}: No such file or directory\n")
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
                    sys.stdin = os.fdopen(stdin, 'r') if isinstance(stdin, int) else stdin
                if stdout is not None:
                    sys.stdout = os.fdopen(stdout, 'w') if isinstance(stdout, int) else stdout
                run_builtin(cmd_name, args[1:])
            finally:
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

        # Pipeline logic
        if '|' in command_line:
            cmd_parts = command_line.split("|")
            cmds = [shlex.split(c.strip()) for c in cmd_parts]

            if len(cmds) == 2:
                r_fd, w_fd = os.pipe()

                cmd1_args = cmds[0]
                cmd2_args = cmds[1]

                args1, out_f1, out_m1, err_f1, err_m1 = parse_redirections(cmd1_args)

                err_h1 = None
                if err_f1:
                    os.makedirs(os.path.dirname(os.path.abspath(err_f1)), exist_ok=True)
                    err_h1 = open(err_f1, err_m1)

                p1 = execute_command(args1, stdout=w_fd, stderr=err_h1)
                os.close(w_fd)

                args2, out_f2, out_m2, err_f2, err_m2 = parse_redirections(cmd2_args)

                final_out = None
                if out_f2:
                    os.makedirs(os.path.dirname(os.path.abspath(out_f2)), exist_ok=True)
                    final_out = open(out_f2, out_m2)

                final_err = None
                if err_f2:
                    os.makedirs(os.path.dirname(os.path.abspath(err_f2)), exist_ok=True)
                    final_err = open(err_f2, err_m2)

                p2 = execute_command(args2, stdin=r_fd, stdout=final_out, stderr=final_err)
                os.close(r_fd)

                if p1: p1.wait()
                if p2: p2.wait()

                if err_h1: err_h1.close()
                if final_out: final_out.close()
                if final_err: final_err.close()
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