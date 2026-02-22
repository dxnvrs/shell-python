import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        #pass

        # waiting for user's input
        command = input()
        print(f"{command}: command not found")

if __name__ == "__main__":
    main()
