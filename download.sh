scp root@$(terraform output --json | jq -r '.public_ip.value'):/root/$1 .
