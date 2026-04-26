#!/bin/sh
# This script bundles the Alpine kernel and CrisPY OS into two bootable ISOs.
# Fixed: Syslinux path detection and variable expansion.

set -e # Exit on error

ALPINE_REPO="https://dl-cdn.alpinelinux.org/alpine/v3.19/main"
ALPINE_COMMUNITY="https://dl-cdn.alpinelinux.org/alpine/v3.19/community"
ARCH=$(uname -m)

build_variant() {
    ISO_NAME=$1
    SCRIPT_NAME=$2
    INCLUDE_TOOLS=$3
    
    echo "--- Building Variant: $ISO_NAME ($SCRIPT_NAME) ---"
    
    VARIANT_DIR="work_$ISO_NAME"
    rm -rf "$VARIANT_DIR" rootfs_tmp kernel_tmp
    mkdir -p "$VARIANT_DIR/staging/boot/isolinux"
    mkdir -p rootfs_tmp/bin rootfs_tmp/etc rootfs_tmp/lib rootfs_tmp/proc rootfs_tmp/sys rootfs_tmp/dev rootfs_tmp/tmp rootfs_tmp/usr/bin rootfs_tmp/usr/sbin rootfs_tmp/sbin rootfs_tmp/root

    # 1. Prepare RootFS
    echo "Creating RootFS and installing packages..."
    mkdir -p rootfs_tmp/etc/apk/keys
    cp /etc/apk/keys/*.pub rootfs_tmp/etc/apk/keys/ || true

    PACKAGES="alpine-base python3 busybox kmod linux-virt"
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

    # 2. Kernel Module Setup
    KVER=$(ls rootfs_tmp/lib/modules | head -n 1)
    echo "Detected kernel version: $KVER"
    chroot rootfs_tmp /sbin/depmod -a "$KVER" || true

    # 3. Copy and CLEAN the specific Python script
    if [ -f "$SCRIPT_NAME" ]; then
        echo "Cleaning and copying $SCRIPT_NAME..."
        sed 's/\xc2\xa0/ /g' "$SCRIPT_NAME" > rootfs_tmp/usr/bin/kernel.py
    else
        echo "Warning: $SCRIPT_NAME not found, using main.py"
        sed 's/\xc2\xa0/ /g' main.py > rootfs_tmp/usr/bin/kernel.py
    fi

    # 4. Create the INIT script
    cat <<EOF > rootfs_tmp/init
#!/bin/sh
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
/bin/busybox --install -s

mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs dev /dev

# Setup mdev for device node creation
echo /sbin/mdev > /proc/sys/kernel/hotplug
mdev -s

# Load modules
modprobe virtio_pci virtio_blk nvme ahci sd_mod ata_piix 2>/dev/null || true
mdev -s

export TERM=linux
export HOME=/root
cd /root

# Run Python OS
if [ -f /usr/bin/python3 ]; then
    /usr/bin/python3 /usr/bin/kernel.py
else
    echo "FATAL: python3 not found"
    /bin/sh
fi

poweroff -f
EOF
    chmod +x rootfs_tmp/init

    # 5. Pack Initramfs
    echo "Packing Initramfs..."
    (cd rootfs_tmp && find . | cpio -o -H newc | gzip) > "$VARIANT_DIR/staging/boot/initrd"

    # 6. Setup Bootloader and Kernel
    echo "Fetching Kernel and Syslinux..."
    mkdir -p kernel_tmp
    apk add --initdb --root $(pwd)/kernel_tmp --repository "$ALPINE_REPO" --arch "$ARCH" --allow-untrusted --no-scripts linux-virt syslinux
    
    cp kernel_tmp/boot/vmlinuz-virt "$VARIANT_DIR/staging/boot/vmlinuz"
    
    # Locate syslinux files dynamically
    SYSLINUX_SRC=$(find kernel_tmp/usr -name "isolinux.bin" | xargs dirname | head -n 1)
    
    if [ -z "$SYSLINUX_SRC" ]; then
        echo "ERROR: Could not find isolinux.bin in kernel_tmp"
        exit 1
    fi
    
    echo "Found Syslinux files at: $SYSLINUX_SRC"
    cp "$SYSLINUX_SRC/isolinux.bin" "$VARIANT_DIR/staging/boot/isolinux/"
    cp "$SYSLINUX_SRC/ldlinux.c32" "$VARIANT_DIR/staging/boot/isolinux/"
    # Try to copy optional but helpful modules
    cp "$SYSLINUX_SRC/libutil.c32" "$VARIANT_DIR/staging/boot/isolinux/" 2>/dev/null || true
    cp "$SYSLINUX_SRC/libcom32.c32" "$VARIANT_DIR/staging/boot/isolinux/" 2>/dev/null || true

    cat <<EOF > "$VARIANT_DIR/staging/boot/isolinux/isolinux.cfg"
DEFAULT crispy
LABEL crispy
  KERNEL /boot/vmlinuz
  APPEND initrd=/boot/initrd quiet nomodeset panic=1
EOF

    # 7. Final ISO Creation
    xorriso -as mkisofs \
      -o "$ISO_NAME.iso" \
      -b boot/isolinux/isolinux.bin \
      -c boot/isolinux/boot.cat \
      -no-emul-boot -boot-load-size 4 -boot-info-table \
      -R -J -V "CRISPY_OS" \
      "$VARIANT_DIR/staging/"

    # Make the ISO hybrid
    if command -v isohybrid >/dev/null; then
        isohybrid "$ISO_NAME.iso"
    fi

    rm -rf "$VARIANT_DIR" rootfs_tmp kernel_tmp
    echo "--- Generated $ISO_NAME.iso ---"
}

build_variant "crispy-live" "main.py" "false"
build_variant "crispy-installer" "main_installable.py" "true"
