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
            if command[5:] in BUILTIN:
                print(f"{command[5:]} is a shell builtin")
            else:
                if os.path.exists(command[5:]):
                    print(f"{command[5:]} is {rcvPATH}")
                else:
                    print(f"{command[5:]}: not found")
        else: 
            print(f"{command}: command not found")

        
if __name__ == "__main__":
    main()
