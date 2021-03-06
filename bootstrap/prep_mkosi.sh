#!/bin/bash

set -e
set -x

FEDORA_TARGET_RELEASE=31
CLOUD_IMAGE_URL="https://download.fedoraproject.org/pub/fedora/linux/releases/31/Cloud/x86_64/images/Fedora-Cloud-Base-31-1.9.x86_64.raw.xz"

pushd /app

curl -L $CLOUD_IMAGE_URL -o /app/image.raw.xz

# create a common ssh key that will be used to generate the final VM images
ssh-keygen -t rsa -f /root/.ssh/id_rsa -N ''

# to start the cloud-init ready image we need to provide it some input:
# https://blog.christophersmart.com/2016/06/17/booting-fedora-24-cloud-image-with-kvm/

cat > /app/meta-data << EOF
instance-id: Cloud00
local-hostname: cloud-00
EOF


cat > /app/user-data << EOF
#cloud-config
# Set the default user
system_info:
  default_user:
    name: cloud

# Unlock the default and root users
chpasswd:
  list: |
     cloud:password
     root:root
  expire: False

# Other settings
resize_rootfs: True
ssh_pwauth: True
disable_root: false
timezone: Australia/Sydney

# Add any ssh public keys
ssh_authorized_keys:
 - $(cat /root/.ssh/id_rsa.pub)

bootcmd:
 - [ sh, -c, echo "=========bootcmd=========" ]

runcmd:
 - [ sh, -c, echo "=========runcmd=========" ]

final_message: "SYSTEM READY TO LOG IN"
EOF

genisoimage -output /app/my-seed.iso \
            -volid cidata \
            -joliet \
            -rock /app/user-data /app/meta-data

# do some initial preparation in the target VM so it is mkosi capable
/app/start_vm.sh -cdrom /app/my-seed.iso

# install mkosi dependencies to build up our final VM image
ssh localhost -p 5555 dnf install -y mkosi systemd-container
# use the upstream mkosi code
ssh localhost -p 5555 git clone https://github.com/systemd/mkosi.git

# pacman needs 5.2.0 to work, fedora is still on 5.0.0
# https://bugzilla.redhat.com/show_bug.cgi?id=1582967
ssh localhost -p 5555 dnf install -y \
	https://kojipkgs.fedoraproject.org//work/tasks/9076/41689076/pacman-5.2.1-1.fc31.x86_64.rpm \
	https://kojipkgs.fedoraproject.org//work/tasks/9076/41689076/libalpm-5.2.1-1.fc31.x86_64.rpm \
	https://kojipkgs.fedoraproject.org//work/tasks/9076/41689076/pacman-filesystem-5.2.1-1.fc31.noarch.rpm

# stop the vm and compress the image file
ssh localhost -p 5555 halt -p || true

while pgrep qemu
do
	sleep 2
done

# manually compress the image with `-T0` to use multithreading
xz -T0 /app/image.raw

popd
