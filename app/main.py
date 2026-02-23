import cmd
import sys
import os
import subprocess

BUILTIN = ['echo', 'exit', 'type', 'pwd', 'cd']

def main():

    while True:
        # Get the PATH environment variable and split it into directories
        rcvPATH = os.environ.get('PATH', '')
        dirs = rcvPATH.split(os.pathsep)
        
        sys.stdout.write("$ ")
        
        # waiting for user's input
        command = input()
        parts = command.split()  
        cmdName = parts[0]
        args = parts[1:]
       
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
        elif cmdName == 'cd':
            if args:
                try:
                    os.chdir(args[0])
                except FileNotFoundError:
                    print(f"cd: {args[0]}: No such file or directory")
            else:
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
