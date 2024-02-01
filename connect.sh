ssh root@$(terraform output --json | jq -r '.public_ip.value')
