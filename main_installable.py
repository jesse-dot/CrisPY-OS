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
    """Executes a REAL installation to a block device."""
    print("=========================================")
    print("      CrisPY OS BARE-METAL INSTALLER     ")
    print("=========================================")
    
    print("\nScanning for available hardware drives...")
    available_drives = []
    
    # 0. Force-mount special Linux filesystems just in case the boot script forgot!
    try:
        os.makedirs('/proc', exist_ok=True)
        os.makedirs('/sys', exist_ok=True)
        os.makedirs('/dev', exist_ok=True)
        subprocess.run(['mount', '-t', 'proc', 'none', '/proc'], stderr=subprocess.DEVNULL)
        subprocess.run(['mount', '-t', 'sysfs', 'none', '/sys'], stderr=subprocess.DEVNULL)
        subprocess.run(['mount', '-t', 'devtmpfs', 'none', '/dev'], stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Safely try to read the Linux block devices
    try:
        # Method 1: Read from /proc/partitions (Very reliable if /proc is mounted)
        if os.path.exists('/proc/partitions'):
            with open('/proc/partitions', 'r') as f:
                lines = f.readlines()[2:] # Skip the header lines
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        dev_name = parts[3]
                        if not dev_name.startswith('loop') and not dev_name.startswith('ram') and not dev_name.startswith('sr'):
                            # Skip partitions (like sda1), keep base drives (like sda, vda, nvme0n1)
                            if not dev_name[-1].isdigit() or ('nvme' in dev_name and 'p' not in dev_name):
                                available_drives.append(f"/dev/{dev_name}")

        # Method 2: Read from /sys/block (Fallback)
        if not available_drives and os.path.exists('/sys/block') and len(os.listdir('/sys/block')) > 0:
            for dev in os.listdir('/sys/block'):
                # Ignore loopback, RAM drives, and CD-ROMs (sr)
                if not dev.startswith('loop') and not dev.startswith('ram') and not dev.startswith('sr'):
                    available_drives.append(f"/dev/{dev}")
                    
        # Method 3: Fallback if /sys is not mounted. Check /dev directly!
        if not available_drives and os.path.exists('/dev'):
            for dev in os.listdir('/dev'):
                # Look for common VM/PC drive prefixes and ensure it's a main drive (not a partition like sda1)
                if (dev.startswith('sd') or dev.startswith('vd') or dev.startswith('hd')) and len(dev) == 3:
                    available_drives.append(f"/dev/{dev}")
                elif dev.startswith('nvme') and 'n' in dev and 'p' not in dev:
                    available_drives.append(f"/dev/{dev}")
                    
        # Remove duplicates and sort nicely
        available_drives = list(set(available_drives))
        available_drives.sort()
        
        if available_drives:
            print("Found the following drives:")
            for i, drive in enumerate(available_drives):
                print(f"  [{i + 1}] {drive}")
        else:
            print("No physical drives detected.")
            print("\n[!] Troubleshooting Tips:")
            print("1. Did you attach a Virtual Hard Disk to the VM in VirtualBox/VMware?")
            print("2. In VirtualBox, try changing the Storage Controller from SATA to IDE.")
            print("3. Your Buildroot Linux Kernel might be missing the VirtIO/SATA driver for your VM.")
            
    except Exception as e:
        print(f"Could not automatically detect drives: {e}")

    print("\nPlease enter the target drive path.")
    if available_drives:
        print("You can type the path (e.g., /dev/sda) OR the number from the list above.")
        
    target_input = input("\nTarget Drive: ").strip()
    
    if not target_input:
        print("Installation canceled.")
        return
        
    # Check if the user typed a number from the list
    if target_input.isdigit() and available_drives:
        idx = int(target_input) - 1
        if 0 <= idx < len(available_drives):
            target = available_drives[idx]
        else:
            print("Invalid number selection. Installation canceled.")
            return
    else:
        # Otherwise, assume they typed the direct path (e.g., /dev/sda)
        target = target_input
    
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
        # 1.5 Wipe old filesystems/signatures so fdisk doesn't get stuck asking "Remove signature?"
        print(f"-> Wiping old partition tables on {target}...")
        subprocess.run(['dd', 'if=/dev/zero', f'of={target}', 'bs=1M', 'count=10'], stderr=subprocess.DEVNULL)
        time.sleep(1)

        # 2. Partition the Drive
        print(f"-> Creating new partition table on {target} (fdisk)...")
        # Sends commands to fdisk: o (new DOS disklabel), n (new partition), p (primary), 1 (partition 1), enter (default first sector), enter (default last sector), w (write)
        fdisk_cmds = b"o\nn\np\n1\n\n\nw\n"
        subprocess.run(['fdisk', target], input=fdisk_cmds, capture_output=True, check=True)
        time.sleep(2)
        
        # Force the Linux device manager to refresh /dev with the newly created partition node
        subprocess.run(['mdev', '-s'], stderr=subprocess.DEVNULL)
        
        # Double check that the partition actually showed up before trying to format
        if not os.path.exists(part_dev):
            raise Exception(f"The partition {part_dev} was not created. fdisk may have failed silently.")
        
        # 3. Format the Partition
        print(f"-> Formatting {part_dev} as ext4...")
        subprocess.run(['mkfs.ext4', '-F', part_dev], capture_output=True, check=True)
        
        # 4. Mount the New Drive
        print(f"-> Mounting {part_dev} to /mnt...")
        os.makedirs('/mnt', exist_ok=True)
        subprocess.run(['mount', part_dev, '/mnt'], check=True)
        
        # 5. Copy the Live File System
        print("-> Copying core system files (this may take a moment)...")
        # BusyBox 'cp' doesn't support '-x', so we manually skip virtual hardware folders
        skip_folders = ['dev', 'proc', 'sys', 'mnt', 'run', 'tmp']
        for item in os.listdir('/'):
            if item not in skip_folders:
                src = os.path.join('/', item)
                subprocess.run(['cp', '-a', src, '/mnt/'], check=True)
        
        # Create empty mount points for the virtual filesystems on the new drive
        for folder in skip_folders:
            os.makedirs(f'/mnt/{folder}', exist_ok=True)
        
        # 6. Install Bootloader
        print("-> Installing GRUB bootloader...")
        subprocess.run(['grub-install', '--boot-directory=/mnt/boot', target], capture_output=True, check=True)
        
        # 7. Generate GRUB Configuration
        print("-> Creating GRUB configuration file...")
        os.makedirs('/mnt/boot/grub', exist_ok=True)
        
        # Auto-detect the kernel name (usually bzImage or vmlinuz)
        kernel_name = "bzImage" # Default guess
        if os.path.exists('/mnt/boot'):
            for f in os.listdir('/mnt/boot'):
                if 'bzImage' in f or 'vmlinuz' in f:
                    kernel_name = f
                    break
        
        # Use Python's sys module to find the exact path to the interpreter
        python_path = sys.executable or "/usr/bin/python3"
        
        grub_cfg = f"""set timeout=5
set default=0

menuentry "CrisPY OS" {{
    linux /boot/{kernel_name} root={part_dev} rw rootwait init={python_path} /os_main.py
}}

        with open('/mnt/boot/grub/grub.cfg', 'w') as f:
            f.write(grub_cfg)
        
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
    print("  install     - Install OS to a drive")
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
