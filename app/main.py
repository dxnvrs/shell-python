import sys
import os


def main():
    rcvPATH = os.environ.get('PATH', '')
    dirs = rcvPATH.split(os.pathsep)

    # TODO: Uncomment the code below to pass the first stage
    while True:
        
        
        sys.stdout.write("$ ")
        BUILTIN = ['echo', 'exit', 'type']
        
        # waiting for user's input
        command = input()
       
        if command[:4] == 'echo':
            print(command[5:])
         # if the user types "exit", break the loop and end the program
        elif command[:4] == 'exit':
            break
        elif command[:4] == 'type':
            cmdName = command[5:]
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
        else: 
            print(f"{command}: command not found")

        
if __name__ == "__main__":
    main()
