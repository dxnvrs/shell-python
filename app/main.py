import cmd
import sys
import os
import subprocess

def main():
    # Get the PATH environment variable and split it into directories
    rcvPATH = os.environ.get('PATH', '')
    dirs = rcvPATH.split(os.pathsep)

    while True:
        
        
        sys.stdout.write("$ ")
        BUILTIN = ['echo', 'exit', 'type']
        
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
            if cmdName in BUILTIN:
                print(f"{cmdName} is a shell builtin")
            else:
                found = False
                for directory in dirs:
                    full_path = os.path.join(directory, cmdName)
                    if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                        print(f"{cmdName} is {full_path}")
                        found = True
                        break
                if not found:
                    print(f"{cmdName}: not found")
        # if the command is not a builtin or an executable in the PATH, print an error message
        else: 
            foundPath = None
            for directory in dirs:
                full_path = os.path.join(directory, cmdName)
                if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                    foundPath = full_path 
                    break
            if foundPath:
                subprocess.run([foundPath] + args)
            else:
                print(f"{cmdName}: command not found")

        
if __name__ == "__main__":
    main()
