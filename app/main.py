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
        cmdName = parts[0]
        args = parts[1:]

        if '>' in args or '1>' in args:
            # Handle output redirection
            output_file = None
            if '>' in args:
                output_file = args[args.index('>') + 1]
            elif '1>' in args:
                output_file = args[args.index('1>') + 1]
            
            # Remove redirection arguments from args list
            filtered_args = []
            skip_next = False
            for arg in args:
                if skip_next:
                    skip_next = False
                    continue
                if arg == '>' or arg == '1>':
                    skip_next = True
                    continue
                filtered_args.append(arg)

            with open(output_file, 'w') as f:
                subprocess.run([cmdName] + filtered_args, stdout=f, stderr=f)
       
        if cmdName == 'echo':
            print(" ".join(args))
         # if the user types "exit", break the loop and end the program
        elif cmdName == 'exit':
            if args and args[0] == '0':
                sys.exit(0)
            break
        # if the user types "type <command>", check if the command is a shell builtin or an executable in the PATH
        elif cmdName == 'type':
            target = args[0]
            if target in BUILTIN:
                print(f"{target} is a shell builtin")
            else:
                found = False
                for directory in dirs:
                    full_path = os.path.join(directory, target)
                    if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                        print(f"{target} is {full_path}")
                        found = True
                        break
                if not found:
                    print(f"{target}: not found")
        # if the user types "pwd", print the current working directory
        elif cmdName == 'pwd':
            print(os.getcwd())
        # if the user types "cd <directory>", change the current working directory to the specified directory. If no directory is specified, change to the user's home directory. If the specified directory does not exist, print an error message
        elif cmdName == 'cd':
            if args and args[0] != '~':
                try:
                    os.chdir(args[0])
                except FileNotFoundError:
                    print(f"cd: {args[0]}: No such file or directory")
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
                subprocess.run([cmdName] + args, executable=foundPath)
            else:
                print(f"{cmdName}: command not found")

        
if __name__ == "__main__":
    main()
