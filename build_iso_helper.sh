#!/bin/sh
# This script bundles the Alpine kernel and CrisPY OS into a bootable ISO

set -e # Exit on error

echo "--- Starting CrisPY OS ISO Build Process ---"

# Define the Alpine version and architecture
ALPINE_REPO="https://dl-cdn.alpinelinux.org/alpine/v3.19/main"
ALPINE_COMMUNITY="https://dl-cdn.alpinelinux.org/alpine/v3.19/community"
ARCH=$(uname -m)

# 1. Clean up and setup workspace
rm -rf staging rootfs
mkdir -p staging/boot/grub
mkdir -p rootfs/bin rootfs/etc rootfs/lib rootfs/proc rootfs/sys rootfs/dev rootfs/tmp rootfs/usr/bin

# 2. Fetch the Alpine Linux base and Python to create a ROOTFS
echo "Downloading Alpine components for rootfs..."
mkdir -p rootfs/etc/apk/keys
cp /etc/apk/keys/*.pub rootfs/etc/apk/keys/ || echo "Warning: Using host keys"

apk add --initdb \
    --root $(pwd)/rootfs \
    --repository "$ALPINE_REPO" \
    --repository "$ALPINE_COMMUNITY" \
    --arch "$ARCH" \
    --allow-untrusted \
    --no-scripts \
    alpine-base python3

# 3. Copy CrisPY OS code into the rootfs
if [ -f "main.py" ]; then
    cp main.py rootfs/usr/bin/main.py
else
    echo "ERROR: main.py not found!"
    exit 1
fi

# 4. Create the INIT script
cat <<EOF > rootfs/init
#!/bin/sh
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

echo "---------------------------------------"
echo "  Welcome to CrisPY OS Bootloader...   "
echo "---------------------------------------"
python3 /usr/bin/main.py

echo "CrisPY OS has exited. Shutting down..."
poweroff -f
EOF

chmod +x rootfs/init

# 5. Pack the rootfs into a compressed cpio archive (initramfs)
echo "Packing rootfs into initramfs..."
cd rootfs
find . | cpio -o -H newc | gzip > ../staging/boot/initramfs-crispy
cd ..

# 6. Fetch Kernel and Bootloader files
echo "Fetching kernel and bootloader components..."
mkdir -p /tmp/kernel-fetch
apk add --initdb \
    --root /tmp/kernel-fetch \
    --repository "$ALPINE_REPO" \
    --arch "$ARCH" \
    --allow-untrusted \
    --no-scripts \
    linux-virt grub-bios

cp /tmp/kernel-fetch/boot/vmlinuz-virt staging/boot/

# 7. Create GRUB configuration
cat <<EOF > staging/boot/grub/grub.cfg
set default=0
set timeout=1
set gfxpayload=text

menuentry "CrisPY OS v0.1" {
    linux /boot/vmlinuz-virt quiet panic=1
    initrd /boot/initramfs-crispy
}
EOF

# 8. Build the ISO with explicit Boot Flags for BIOS compatibility
# We use -as mkisofs with specific El Torito flags which VMware requires
echo "Creating ISO image with El Torito boot records..."
xorriso -as mkisofs \
  -R -J \
  -V "CRISPY_OS" \
  -o pyos.iso \
  -b boot/grub/grub.cfg \
  -no-emul-boot \
  -boot-load-size 4 \
  -boot-info-table \
  -isolevel 3 \
  staging/

echo "--- Build Complete: pyos.iso is ready ---"
