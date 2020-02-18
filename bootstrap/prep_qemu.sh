#!/bin/bash

set -e
set -x

mkdir -p /app

cat > /app/start_vm.sh <<EOF
#!/bin/bash

set -x

if [[ ! -e /app/image.raw ]]
then
  xz -d -T0 /app/image.raw.xz || (echo "Failed to unpack image" && exit 1)
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

exit_code=\$?

# Connect once to store the host key locally
if [[ \$exit_code -eq 0 ]]; then
    ssh -o StrictHostKeyChecking=accept-new localhost -p 5555 uname -a
    exit_code=\$?
fi

if [[ \$exit_code -ne 0 ]]; then
   echo "***********************************************************"
   echo "*                                                         *"
   echo "*       WARNING: failed to start or connect to VM         *"
   echo "*                                                         *"
   echo "***********************************************************"
fi

exit \$exit_code

EOF

chmod +x /app/start_vm.sh
