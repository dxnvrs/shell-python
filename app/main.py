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
        
        stdoutFile = None
        stderrFile = None

        outputFile = None

        if '>' in parts or '1>' in parts:
            op = '>' if '>' in parts else '1>'
            idx = parts.index(op)
            stdoutFile = parts[idx + 1]
            parts = parts[:idx] + parts[idx+2:]

        if '2>' in parts:
            idx = parts.index('2>')
            stderrFile = parts[idx + 1]
            parts = parts[:idx] + parts[idx+2:]

        if not parts: continue
        
        cmdName = parts[0]
        args = parts[1:]

        def shellPrint(content):
            if outputFile:
                with open(outputFile, 'w') as f:
                    f.write(content + '\n')
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
            foundPath = None
            # Search for the command in the directories specified in PATH
            for directory in dirs:
                full_path = os.path.join(directory, cmdName)
                if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                    foundPath = full_path 
                    break
            if foundPath:

                outStream = None
                errStream = None
                try:
                    if stdoutFile:
                        os.makedirs(os.path.dirname(os.path.abspath(stdoutFile)), exist_ok=True)  # Ensure the directory exists
                        outStream = open(stdoutFile, 'w')
                    
                    if stderrFile:
                        os.makedirs(os.path.dirname(os.path.abspath(stderrFile)), exist_ok=True)  # Ensure the directory exists
                        errStream = open(stderrFile, 'w')
                
                    subprocess.run(
                        [cmdName] + args, 
                        executable=foundPath, 
                        stdout=outStream if outStream else None,
                        stderr=errStream if errStream else None
                        )
                except Exception as e:
                    print(f"Error executing command: {e}")
                finally:
                    if outStream:
                        outStream.close()
                    if errStream:
                        errStream.close()
            else:
                print(f"{cmdName}: command not found")
       
if __name__ == "__main__":
    main()
