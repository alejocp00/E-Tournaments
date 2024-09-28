import sys
from chord import ChordNode

def main(m:int):
    c = ChordNode(m)
    c.run()
    commands = {
        "join": c.join,
        "lookup": c.lookup,
        "predecessor":c.find_predecessor,
        "successor":c.find_succesor,
        "exit": c.exit,
        "ft":c.get_finger_table,
        "ns":c.get_node_set,
        "ip":c.get_ip_table
    }
    while True:
        try:
            usr_input = input().split()
            if len(usr_input) == 0:
                continue
            arg_0 = usr_input[0]
            try:
                command = commands[arg_0]
            except KeyError:
                print("Unrecognized command")
                continue

            try:
                args = []
                if arg_0 == "join" and len(usr_input) > 1:
                    args.append(usr_input[1])
                elif len(usr_input) > 1:
                    args.append(int(usr_input[1]))
            except IndexError:
                print("Bad Arguments")
                continue
            
            print(command(*args))
            if arg_0 == "exit":
                break
        
        except KeyboardInterrupt:
            print("Exit")
            c.joined = False
            c.online = False
            exit(1)




if __name__ == "__main__":
    arg = sys.argv
    if len(arg) == 1:
        m = 5
    else:
        m = int(arg[1])
    main(m)