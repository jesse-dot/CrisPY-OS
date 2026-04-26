#!/bin/sh
# This script bundles the Alpine kernel and CrisPY OS into two bootable ISOs:
# 1. A Live-only version (main.py)
# 2. An Installable version (main_installable.py + system tools)

set -e # Exit on error

ALPINE_REPO="https://dl-cdn.alpinelinux.org/alpine/v3.19/main"
ALPINE_COMMUNITY="https://dl-cdn.alpinelinux.org/alpine/v3.19/community"
ARCH=$(uname -m)

# Function to build an ISO
# Args: $1=ISO_NAME, $2=SCRIPT_NAME, $3=INCLUDE_TOOLS (true/false)
build_variant() {
    ISO_NAME=$1
    SCRIPT_NAME=$2
    INCLUDE_TOOLS=$3
    
    echo "--- Building Variant: $ISO_NAME ($SCRIPT_NAME) ---"
    
    # Setup fresh workspace for this variant
    VARIANT_DIR="work_$ISO_NAME"
    rm -rf "$VARIANT_DIR" rootfs_tmp
    mkdir -p "$VARIANT_DIR/staging/boot/isolinux"
    mkdir -p rootfs_tmp/bin rootfs_tmp/etc rootfs_tmp/lib rootfs_tmp/proc rootfs_tmp/sys rootfs_tmp/dev rootfs_tmp/tmp rootfs_tmp/usr/bin

    # 1. Prepare RootFS
    echo "Creating RootFS..."
    mkdir -p rootfs_tmp/etc/apk/keys
    cp /etc/apk/keys/*.pub rootfs_tmp/etc/apk/keys/ || true

    # Define packages based on variant
    PACKAGES="alpine-base python3 busybox"
    if [ "$INCLUDE_TOOLS" = "true" ]; then
        PACKAGES="$PACKAGES util-linux e2fsprogs grub-bios"
    fi

    apk add --initdb \
        --root $(pwd)/rootfs_tmp \
        --repository "$ALPINE_REPO" \
        --repository "$ALPINE_COMMUNITY" \
        --arch "$ARCH" \
        --allow-untrusted \
        --no-scripts \
        $PACKAGES

    # 2. Copy the specific Python script
    if [ -f "$SCRIPT_NAME" ]; then
        cp "$SCRIPT_NAME" rootfs_tmp/usr/bin/kernel.py
    else
        echo "Warning: $SCRIPT_NAME not found, falling back to main.py"
        cp main.py rootfs_tmp/usr/bin/kernel.py
    fi

    # 3. Create the INIT script
    cat <<EOF > rootfs_tmp/init
#!/bin/bin/busybox sh
/bin/busybox --install -s
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

echo "---------------------------------------"
echo "  Booting $ISO_NAME                   "
echo "---------------------------------------"
python3 /usr/bin/kernel.py
poweroff -f
EOF
    chmod +x rootfs_tmp/init

    # 4. Pack Initramfs
    echo "Packing Initramfs..."
    cd rootfs_tmp
    find . | cpio -o -H newc | gzip > "../$VARIANT_DIR/staging/boot/initrd"
    cd ..

    # 5. Setup Bootloader and Kernel
    mkdir -p kernel_tmp
    apk add --initdb --root $(pwd)/kernel_tmp --repository "$ALPINE_REPO" --arch "$ARCH" --allow-untrusted --no-scripts linux-virt syslinux
    
    cp kernel_tmp/boot/vmlinuz-virt "$VARIANT_DIR/staging/boot/vmlinuz"
    cp kernel_tmp/usr/share/syslinux/isolinux.bin "$VARIANT_DIR/staging/boot/isolinux/"
    cp kernel_tmp/usr/share/syslinux/ldlinux.c32 "$VARIANT_DIR/staging/boot/isolinux/"

    # FIXED: Added missing closing quote to the heredoc path
    cat <<EOF > "$VARIANT_DIR/staging/boot/isolinux/isolinux.cfg"
DEFAULT crispy
LABEL crispy
  SAY Booting $ISO_NAME...
  KERNEL /boot/vmlinuz
  APPEND initrd=/boot/initrd quiet panic=1
EOF

    # 6. Final ISO Creation
    xorriso -as mkisofs \
      -o "$ISO_NAME.iso" \
      -b boot/isolinux/isolinux.bin \
      -c boot/isolinux/boot.cat \
      -no-emul-boot -boot-load-size 4 -boot-info-table \
      -R -J -V "${ISO_NAME}" \
      "$VARIANT_DIR/staging/"

    # Cleanup variant
    rm -rf "$VARIANT_DIR" rootfs_tmp kernel_tmp
    echo "--- Finished $ISO_NAME.iso ---"
}

# Run builds
build_variant "crispy-live" "main.py" "false"
build_variant "crispy-installer" "main_installable.py" "true"

echo "Build Process Complete. Two ISOs generated."
