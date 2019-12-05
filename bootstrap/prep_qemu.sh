#!/bin/bash

set -e
set -x

mkdir -p /app

cat > /app/start_vm.sh <<EOF
#!/bin/bash

set -x
set -e

if [[ ! -e /app/image.raw ]]
then
  xz -d -T0 /app/image.raw.xz
fi

qemu-system-x86_64 -machine accel=kvm \\
                   -smp 2 -m 1024 \\
                   -drive format=raw,file=/app/image.raw \\
                   -device virtio-net-pci,netdev=net0 \\
                   -netdev user,id=net0,hostfwd=tcp::5555-:22 \\
                   -display none \\
                   -daemonize \\
                   "\$@" \\
                   -serial file:\$CI_BUILDS_DIR/\$CI_PROJECT_PATH/console.out

# store the host key locally
ssh -o StrictHostKeyChecking=accept-new localhost -p 5555 uname -a

EOF

chmod +x /app/start_vm.sh
