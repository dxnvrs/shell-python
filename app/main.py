import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")

        # waiting for user's input
        command = input()
       
        if command[:3] == 'echo':
            print(command[5:])
         # if the user types "exit", break the loop and end the program
        elif command[:3] == 'exit':
            break
        else: 
            print(f"{command}: command not found")

        
if __name__ == "__main__":
    main()
