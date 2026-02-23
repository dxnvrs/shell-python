import cmd
import sys
import os
import subprocess
import shlex

BUILTIN = ['echo', 'exit', 'type', 'pwd', 'cd']

def main():

    while True:
        # get the PATH environment variable and split it into directories
        rcvPATH = os.environ.get('PATH', '')
        dirs = rcvPATH.split(os.pathsep)
        
        sys.stdout.write("$ ")
        
        # waiting for user's input
        command = input()
        # split the command into the command name and its arguments using shlex.split to handle quoted strings properly
        parts = shlex.split(command)  
        if not parts: continue

        stdoutFile = None
        stderrFile = None

        outputFile = None

        for op in ['>', '1>']:
            if op in parts:
                idx = parts.index(op)
                stdoutFile = parts[idx + 1]
                parts = parts[:idx] + parts[idx+2:]
                break

        if '2>' in parts:
            idx = parts.index('2>')
            stderrFile = parts[idx + 1]
            parts = parts[:idx] + parts[idx+2:]
        
        cmdName = parts[0]
        args = parts[1:]

        def shellPrint(content, isError=False):
            targetPath = stderrFile if isError else stdoutFile
            if targetPath:
                pDir = os.path.dirname(targetPath)
                if pDir:
                    os.makedirs(pDir, exist_ok=True)  # Ensure the directory exists
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
         # if the user types "exit", break the loop and end the program
        elif cmdName == 'exit':
            if args and args[0] == '0':
                sys.exit(0)
            break
        # if the user types "type <command>", check if the command is a shell builtin or an executable in the PATH
        elif cmdName == 'type':
            target = args[0]
            if target in BUILTIN:
                shellPrint(f"{target} is a shell builtin")
            else:
                found = False
                for directory in dirs:
                    full_path = os.path.join(directory, target)
                    if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                        shellPrint(f"{target} is {full_path}")
                        found = True
                        break
                if not found:
                    shellPrint(f"{target}: not found")
        # if the user types "pwd", print the current working directory
        elif cmdName == 'pwd':
            shellPrint(os.getcwd())
        # if the user types "cd <directory>", change the current working directory to the specified directory. If no directory is specified, change to the user's home directory. If the specified directory does not exist, print an error message
        elif cmdName == 'cd':
            if args and args[0] != '~':
                try:
                    os.chdir(args[0])
                except FileNotFoundError:
                    shellPrint(f"cd: {args[0]}: No such file or directory")
            else:
                # If no directory is specified or the argument is '~', change to the user's home directory
                os.chdir(os.path.expanduser('~'))

        # if the command is not a builtin or an executable in the PATH, print an error message
        else: 
            # Programas Externos
            foundPath = next((os.path.join(d, cmdName) for d in dirs if os.path.isfile(os.path.join(d, cmdName)) and os.access(os.path.join(d, cmdName), os.X_OK)), None)
            
            if foundPath:
                out_s = open(stdoutFile, 'w') if stdoutFile else None
                err_s = open(stderrFile, 'w') if stderrFile else None
                
                if out_s and os.path.dirname(stdoutFile): os.makedirs(os.path.dirname(stdoutFile), exist_ok=True)
                if err_s and os.path.dirname(stderrFile): os.makedirs(os.path.dirname(stderrFile), exist_ok=True)
                
                try:
                    subprocess.run([cmdName] + args, executable=foundPath, stdout=out_s if out_s else sys.stdout, stderr=err_s if err_s else sys.stderr)
                finally:
                    if out_s: out_s.close()
                    if err_s: err_s.close()
            else:
                print(f"{cmdName}: command not found")
       
if __name__ == "__main__":
    main()
