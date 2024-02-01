# inferenceql.structure-learning

## Setup

``` shell
gcloud auth login
```

``` shell
docker login
```

``` shell
gsutil -m cp -r "gs://civitech-ai-explore/voterfile" data
```

## Cloud

Follow the workflow below to instantiate and interact with a remote AWS machine capable of running structure learning. Note that you must still get structure learning onto the target machine, and you must log into Docker so the Loom Docker image can be retrieved.

Instantiate remote machine:

``` shell
terraform init
```

``` shell
terraform apply
```

SSH into to remote machine:

``` shell
./connect.sh
```

Send files to remote machine:

``` shell
./upload.sh <PATH>
```

Send files to remote machine:

``` shell
./download.sh <PATH>
```

Destroy remote machine:

``` shell
terraform destroy
```
