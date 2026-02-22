import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")

        # waiting for user's input
        command = input()
       
        if command[:4] == 'echo':
            print(command[5:])
         # if the user types "exit", break the loop and end the program
        elif command[:4] == 'exit':
            break
        elif command[:4] == 'type':
            if command[5:9] == "echo" or command[5:9] == "exit" or command[5:9] == "type":
                print(f"{command[5:9]} is a shell builtin")
            else:
                print(f"{command[5:]}: not found")
        else: 
            print(f"{command}: command not found")

        
if __name__ == "__main__":
    main()
