# inferenceql.structure-learning

To get started with structure learning, please see the guide, either [elsewhere in this repo](https://github.com/InferenceQL/inferenceql.structure-learning/blob/main/docs/modules/ROOT/pages/structure-learning.adoc) or [hosted on fly.dev](https://inferenceql-documentation.fly.dev/structure-learning/structure-learning.html).

## Cloud

``` shell
NIXPKGS_ALLOW_UNFREE=1 nix shell --impure nixpkgs#terraform
```

### Connecting

``` shell
terraform init
terraform apply
ssh root@<IP address>
```

### Choosing a different AMI

``` shell
aws ec2 describe-images \
    --region us-east-1 \
    --filters Name=owner-id,Values=080433136561 \
  | jq '.Images | map(select(.Architecture == "x86_64")) | sort_by(.CreationDate) | reverse | map({ ImageId, Architecture, Description }) | .[:5]'
```
