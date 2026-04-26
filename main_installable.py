import os
import sys
import time
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

def cmd_install(args):
    """Executes a REAL installation to a block device (e.g., /dev/sda)."""
    print("=========================================")
    print("      CrisPY OS BARE-METAL INSTALLER     ")
    print("=========================================")
    
    if not args:
        print("Usage: install <target_drive>")
        print("Example: install /dev/sda (Linux VM) or /dev/vda")
        return

    target = args[0]
    
    # 1. EXTREME Warning and Confirmation
    print(f"\n[!!!] DANGER: THIS WILL ERASE EVERYTHING ON '{target}' [!!!]")
    print("Only do this in a Virtual Machine! If you run this on your host PC, it will wipe your drive.")
    confirm = input("Type 'ERASE' to continue, or anything else to cancel: ")
    
    if confirm != "ERASE":
        print("Installation canceled for your safety.")
        return

    print("\nStarting bare-metal installation process...")
    
    # Figure out the partition name (e.g., /dev/sda -> /dev/sda1)
    part_dev = f"{target}1" if not target[-1].isdigit() else f"{target}p1"
    
    try:
        # 2. Partition the Drive
        print(f"-> Creating new partition table on {target} (fdisk)...")
        # Sends commands to fdisk: o (new DOS disklabel), n (new partition), p (primary), 1 (partition 1), enter (default first sector), enter (default last sector), w (write)
        fdisk_cmds = b"o\nn\np\n1\n\n\nw\n"
        subprocess.run(['fdisk', target], input=fdisk_cmds, capture_output=True, check=True)
        time.sleep(1)
        
        # 3. Format the Partition
        print(f"-> Formatting {part_dev} as ext4...")
        subprocess.run(['mkfs.ext4', '-F', part_dev], capture_output=True, check=True)
        
        # 4. Mount the New Drive
        print(f"-> Mounting {part_dev} to /mnt...")
        os.makedirs('/mnt', exist_ok=True)
        subprocess.run(['mount', part_dev, '/mnt'], check=True)
        
        # 5. Copy the Live File System
        print("-> Copying core system files (this may take a moment)...")
        # cp -ax copies the root file system but ignores virtual hardware folders like /proc and /dev
        subprocess.run(['cp', '-ax', '/', '/mnt'], check=True)
        
        # 6. Install Bootloader
        print("-> Installing GRUB bootloader...")
        subprocess.run(['grub-install', '--boot-directory=/mnt/boot', target], capture_output=True, check=True)
        
        print("\n=========================================")
        print("       INSTALLATION COMPLETE!            ")
        print("=========================================")
        print(f"CrisPY OS has successfully installed to {target}.")
        print("You can now power off, remove the ISO/USB, and boot directly from the hard drive!")
        
    except FileNotFoundError as e:
        print(f"\n[!] Missing Dependency: The command '{e.filename}' was not found.")
        print("Ensure fdisk, mkfs.ext4, and grub are included in your Buildroot environment.")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Installation failed during system command.")
        print(f"Command executed: {' '.join(e.cmd)}")
        if e.stderr:
            print(f"Error output: {e.stderr.decode('utf-8', errors='ignore').strip()}")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
    finally:
        # 7. Always unmount cleanly, even if the install failed halfway through
        subprocess.run(['umount', '/mnt'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

def cmd_help(args):
    """Displays system help."""
    print("CrisPY OS Prototype v0.3")
    print("-" * 20)
    print("Available commands:")
    print("  ls [dir]    - List directory contents")
    print("  cd <dir>    - Change current directory")
    print("  pwd         - Print working directory")
    print("  cat <file>  - Read a text file")
    print("  touch <file>- Create an empty file")
    print("  mkdir <dir> - Create a new directory")
    print("  rm <file>   - Delete a file")
    print("  clear       - Clear the screen")
    print("  install     - Install OS to a drive/folder")
    print("  help        - Show this help message")
    print("  halt        - Shut down the system")

# --- Kernel / Main Loop ---

def main():
    # Clear the screen on boot (handles both Windows and Linux/Mac hosts during testing)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("Welcome to CrisPY OS Prototype v0.3")
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
        'clear': cmd_clear,
        'install': cmd_install,
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
