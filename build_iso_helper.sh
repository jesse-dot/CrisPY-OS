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
mkdir -p staging/boot/isolinux
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

# 6. Fetch Kernel and ISOLINUX bootloader files
echo "Fetching kernel and syslinux components..."
mkdir -p /tmp/kernel-fetch
apk add --initdb \
    --root /tmp/kernel-fetch \
    --repository "$ALPINE_REPO" \
    --arch "$ARCH" \
    --allow-untrusted \
    --no-scripts \
    linux-virt syslinux

# Copy Kernel
cp /tmp/kernel-fetch/boot/vmlinuz-virt staging/boot/vmlinuz

# Copy ISOLINUX components for BIOS booting
cp /tmp/kernel-fetch/usr/share/syslinux/isolinux.bin staging/boot/isolinux/
cp /tmp/kernel-fetch/usr/share/syslinux/ldlinux.c32 staging/boot/isolinux/

# 7. Create ISOLINUX configuration (Replaces GRUB for better compatibility)
cat <<EOF > staging/boot/isolinux/isolinux.cfg
DEFAULT crispy
LABEL crispy
  SAY Booting CrisPY OS...
  KERNEL /boot/vmlinuz
  APPEND initrd=/boot/initramfs-crispy quiet panic=1
EOF

# 8. Build the ISO with compatible El Torito flags
# Removed -isolevel and used -b with the isolinux binary
echo "Creating ISO image with ISOLINUX..."
xorriso -as mkisofs \
  -o pyos.iso \
  -b boot/isolinux/isolinux.bin \
  -c boot/isolinux/boot.cat \
  -no-emul-boot \
  -boot-load-size 4 \
  -boot-info-table \
  -R -J -V "CRISPY_OS" \
  staging/

echo "--- Build Complete: pyos.iso is ready ---"
