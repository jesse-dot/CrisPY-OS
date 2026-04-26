#!/bin/sh
# This script bundles the Alpine kernel and CrisPY OS into a bootable ISO

set -e # Exit on error

echo "--- Starting CrisPY OS ISO Build Process ---"

# Define the Alpine version and architecture
ALPINE_REPO="https://dl-cdn.alpinelinux.org/alpine/v3.19/main"
ARCH=$(uname -m)

# 1. Clean up and setup workspace
rm -rf staging rootfs
mkdir -p staging/boot/grub
mkdir -p rootfs/bin rootfs/etc rootfs/lib rootfs/proc rootfs/sys rootfs/dev rootfs/tmp rootfs/usr/bin

# 2. Fetch the Alpine Linux base and Python to create a ROOTFS
echo "Downloading Alpine components for rootfs..."
mkdir -p /tmp/alpine-root/etc/apk
cp -r /etc/apk/keys /tmp/alpine-root/etc/apk/

apk add --initdb \
    --root $(pwd)/rootfs \
    --repository "$ALPINE_REPO" \
    --arch "$ARCH" \
    --allow-untrusted \
    alpine-base python3

# 3. Copy CrisPY OS code into the rootfs
cp main.py rootfs/usr/bin/main.py

# 4. Create the INIT script (Crucial step to fix the black screen)
# This is the first process the Linux kernel runs.
cat <<EOF > rootfs/init
#!/bin/sh
# Mount essential filesystems
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

echo "Welcome to CrisPY OS Bootloader..."
# Run the Python OS
python3 /usr/bin/main.py

# If the OS exits, poweroff
echo "CrisPY OS has exited. Shutting down..."
poweroff -f
EOF

chmod +x rootfs/init

# 5. Pack the rootfs into a compressed cpio archive (initramfs)
echo "Packing rootfs into initramfs..."
cd rootfs
find . | cpio -o -H newc | gzip > ../staging/boot/initramfs-crispy
cd ..

# 6. Fetch the Kernel
# We just need the kernel file now, as we made our own initrd
apk add --initdb --root /tmp/kernel-fetch --repository "$ALPINE_REPO" --arch "$ARCH" --allow-untrusted linux-virt
cp /tmp/kernel-fetch/boot/vmlinuz-virt staging/boot/

# 7. Create GRUB configuration
cat <<EOF > staging/boot/grub/grub.cfg
set default=0
set timeout=1

menuentry "CrisPY OS v0.1" {
    linux /boot/vmlinuz-virt quiet panic=1
    initrd /boot/initramfs-crispy
}
EOF

# 8. Build the ISO
echo "Creating ISO image..."
xorriso -as mkisofs \
  -joliet -rock \
  -volid "CRISPY_OS" \
  -o pyos.iso \
  -b boot/grub/grub.cfg \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  staging/

echo "--- Build Complete: pyos.iso is ready ---"
