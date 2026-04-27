import os
import sys
import shutil
import subprocess

# --- System Commands ---

def cmd_pwd(args):
    """Prints the current working directory."""
    print(os.getcwd())

def cmd_ls(args):
    """Lists files and directories."""
    # If the user provides an argument (e.g., ls /var), use it. Otherwise, use current directory ('.')
    target_dir = args[0] if args else '.'
    
    try:
        files = os.listdir(target_dir)
        if not files:
            print("<empty directory>")
        else:
            # Sort files alphabetically
            for item in sorted(files):
                # Check if the item is a directory so we can format it differently
                if os.path.isdir(os.path.join(target_dir, item)):
                    print(f"[{item}/]") # Brackets and trailing slash for directories
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
        print("cd: missing argument (where do you want to go?)")
        return
    
    target_dir = args[0]
    try:
        os.chdir(target_dir)
    except FileNotFoundError:
        print(f"cd: {target_dir}: No such file or directory")
    except NotADirectoryError:
        print(f"cd: {target_dir}: Not a directory")
    except PermissionError:
        print(f"cd: {target_dir}: Permission denied")

def cmd_cat(args):
    """Reads and prints the contents of a file."""
    if not args:
        print("cat: missing filename")
        return
    
    filename = args[0]
    try:
        with open(filename, 'r') as f:
            content = f.read()
            print(content, end="")
            # Ensure we end on a new line if the file doesn't have one
            if not content.endswith('\n'):
                print()
    except FileNotFoundError:
        print(f"cat: {filename}: No such file or directory")
    except IsADirectoryError:
        print(f"cat: {filename}: Is a directory")
    except PermissionError:
        print(f"cat: {filename}: Permission denied")
    except UnicodeDecodeError:
        print(f"cat: {filename}: Cannot read binary file")

def cmd_touch(args):
    """Creates an empty file or updates its timestamp."""
    if not args:
        print("touch: missing filename")
        return
    
    filename = args[0]
    try:
        # 'a' opens for appending without truncating, creating it if it doesn't exist
        with open(filename, 'a'):
            os.utime(filename, None)
    except Exception as e:
        print(f"touch: {filename}: {e}")

def cmd_mkdir(args):
    """Creates a new directory."""
    if not args:
        print("mkdir: missing directory name")
        return
    
    dirname = args[0]
    try:
        os.mkdir(dirname)
    except FileExistsError:
        print(f"mkdir: cannot create directory '{dirname}': File exists")
    except Exception as e:
        print(f"mkdir: cannot create directory '{dirname}': {e}")

def cmd_rm(args):
    """Removes a file."""
    if not args:
        print("rm: missing filename")
        return
    
    filename = args[0]
    try:
        os.remove(filename)
    except FileNotFoundError:
        print(f"rm: cannot remove '{filename}': No such file or directory")
    except IsADirectoryError:
        print(f"rm: cannot remove '{filename}': Is a directory. Use rmdir.")
    except Exception as e:
        print(f"rm: cannot remove '{filename}': {e}")

def cmd_clear(args):
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def cmd_nano(args):
    """Opens a file in nano."""
    if not args:
        print("nano: missing filename")
        return

    if shutil.which('nano') is None:
        print("nano: command not found")
        return

    try:
        subprocess.run(['nano', args[0]])
    except Exception as e:
        print(f"nano: {args[0]}: {e}")

def cmd_help(args):
    """Displays system help."""
    print("CrisPY OS Prototype v0.2")
    print("-" * 20)
    print("Available commands:")
    print("  ls [dir]    - List directory contents")
    print("  cd <dir>    - Change current directory")
    print("  pwd         - Print working directory")
    print("  cat <file>  - Read a text file")
    print("  touch <file>- Create an empty file")
    print("  mkdir <dir> - Create a new directory")
    print("  rm <file>   - Delete a file")
    print("  nano <file> - Edit a file with nano")
    print("  clear       - Clear the screen")
    print("  help        - Show this help message")
    print("  halt        - Shut down the system")

# --- Kernel / Main Loop ---

def main():
    # Clear the screen on boot (handles both Windows and Linux/Mac hosts during testing)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("Welcome to CrisPY OS Prototype v0.2")
    print("System initialized. Type 'help' for commands.\n")

    # Map typed strings to our Python functions
    commands = {
        'pwd': cmd_pwd,
        'ls': cmd_ls,
        'cd': cmd_cd,
        'cat': cmd_cat,
        'touch': cmd_touch,
        'mkdir': cmd_mkdir,
        'rm': cmd_rm,
        'nano': cmd_nano,
        'clear': cmd_clear,
        'help': cmd_help
    }

    # The Master REPL (Read-Eval-Print Loop)
    while True:
        try:
            # We dynamically update the prompt to show the current directory!
            cwd = os.getcwd()
            prompt = f"root@crispy:{cwd}# "
            
            # READ
            cmd_input = input(prompt).strip()

            if not cmd_input:
                continue

            # EVALUATE
            parts = cmd_input.split()
            command = parts[0]
            args = parts[1:]

            # Built-in halt mechanism
            if command == 'halt' or command == 'exit':
                print("Halting system... Goodbye!")
                break

            # Execute command if it exists
            if command in commands:
                commands[command](args)
            else:
                print(f"crispy: {command}: command not found")

        # The Kernel Panic Traps
        except KeyboardInterrupt:
            # Catches Ctrl+C so the OS doesn't crash
            print("\nType 'halt' to exit.")
        except Exception as e:
            # Catches catastrophic bugs
            print(f"\n[KERNEL PANIC] Unhandled system exception: {e}")
            print("In a real OS, the system would freeze here.")

if __name__ == "__main__":
    main()
