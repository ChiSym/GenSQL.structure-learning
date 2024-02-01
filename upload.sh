scp $1 root@$(terraform output --json | jq -r '.public_ip.value'):/root
