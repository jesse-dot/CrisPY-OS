#!/bin/sh
# This script bundles the Alpine kernel and CrisPY OS into a bootable ISO

set -e # Exit on error

echo "--- Starting CrisPY OS ISO Build Process ---"

# Define the Alpine version and architecture
ALPINE_REPO="https://dl-cdn.alpinelinux.org/alpine/v3.19/main"
ARCH=$(uname -m)

# 1. Clean up and setup workspace
rm -rf staging
mkdir -p staging/boot/grub
mkdir -p staging/pyos

# 2. Copy the Python Kernel (main.py)
if [ -f "main.py" ]; then
    cp main.py staging/pyos/
    echo "Successfully copied main.py to staging."
else
    echo "ERROR: main.py not found in current directory!"
    exit 1
fi

# 3. Create GRUB configuration
cat <<EOF > staging/boot/grub/grub.cfg
set default=0
set timeout=2

menuentry "CrisPY OS v0.1" {
    linux /boot/vmlinuz-virt quiet console=tty0
    initrd /boot/initramfs-virt
}
EOF

# 4. Fetch the Alpine Linux kernel and initfs
# We explicitly provide the repository and architecture to avoid 'package not found' errors
echo "Downloading Alpine boot components for $ARCH..."
mkdir -p /tmp/alpine-root/etc/apk
cp -r /etc/apk/keys /tmp/alpine-root/etc/apk/

apk add --initdb \
    --root /tmp/alpine-root \
    --repository "$ALPINE_REPO" \
    --arch "$ARCH" \
    --allow-untrusted \
    alpine-base linux-virt python3

# Copy the actual kernel and initramfs to our ISO staging area
cp /tmp/alpine-root/boot/vmlinuz-virt staging/boot/
cp /tmp/alpine-root/boot/initramfs-virt staging/boot/

# 5. Build the ISO
echo "Creating ISO image..."
xorriso -as mkisofs \
  -joliet -rock \
  -volid "CRISPY_OS" \
  -o pyos.iso \
  -b boot/grub/grub.cfg \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  staging/

echo "--- Build Complete: pyos.iso is ready ---"
