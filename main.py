import os
import sys

# --- System Commands ---

def cmd_pwd(args):
    """Prints the current working directory."""
    print(os.getcwd())

def cmd_ls(args):
    """Lists files and directories."""
    target_dir = args[0] if args else '.'
    
    try:
        files = os.listdir(target_dir)
        if not files:
            print("<empty directory>")
        else:
            for item in sorted(files):
                if os.path.isdir(os.path.join(target_dir, item)):
                    print(f"[{item}/]")
                else:
                    print(item)
    except FileNotFoundError:
        print(f"ls: cannot access '{target_dir}': No such file or directory")
    except NotADirectoryError:
        print(f"ls: cannot access '{target_dir}': Not a directory")
    except PermissionError:
        print(f"ls: cannot open directory '{target_dir}': Permission denied")

def cmd_cd(args):
    """Changes the current working directory."""
    if not args:
        print("cd: missing argument")
        return
    
    target_dir = args[0]
    try:
        os.chdir(target_dir)
    except FileNotFoundError:
        print(f"cd: {target_dir}: No such file or directory")
    except Exception as e:
        print(f"cd: error: {e}")

def cmd_cat(args):
    """Reads the content of a file."""
    if not args:
        print("cat: missing filename")
        return
    try:
        with open(args[0], 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"cat: {args[0]}: {e}")

def cmd_help(args):
    """Displays system help."""
    print("CrisPY OS Prototype v0.1")
    print("-" * 25)
    print("Available commands:")
    print("  ls [dir]  - List directory contents")
    print("  cd <dir>  - Change current directory")
    print("  pwd       - Print working directory")
    print("  cat <file>- View file contents")
    print("  help      - Show this help message")
    print("  halt      - Shut down the system")

# --- Kernel / Main Loop ---

def main():
    # Clear screen for that clean boot feel
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("Welcome to CrisPY OS Prototype v0.1")
    print("System initialized. Type 'help' for commands.\n")

    commands = {
        'pwd': cmd_pwd,
        'ls': cmd_ls,
        'cd': cmd_cd,
        'cat': cmd_cat,
        'help': cmd_help
    }

    while True:
        try:
            cwd = os.getcwd()
            prompt = f"root@crispy:{cwd}# "
            
            cmd_input = input(prompt).strip()

            if not cmd_input:
                continue

            parts = cmd_input.split()
            command = parts[0]
            args = parts[1:]

            if command == 'halt' or command == 'exit':
                print("Halting system... Goodbye!")
                # In a real ISO, the 'poweroff' in the profile will take over here
                break

            if command in commands:
                commands[command](args)
            else:
                print(f"crispy: {command}: command not found")

        except KeyboardInterrupt:
            print("\nType 'halt' to exit.")
        except Exception as e:
            print(f"\n[KERNEL PANIC] Unhandled system exception: {e}")

if __name__ == "__main__":
    main()
