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

Follow the workflow below to instantiate and interact with a remote AWS machine capable of running structure learning.

Create cloud infrastructure:

``` shell
terraform init
```

``` shell
terraform apply
```

SSH into to the instance:

``` shell
./connect.sh
```

(on instance) Log into GitHub:

``` shell
gh auth login
```

(on instance) Clone this branch:

``` shell
git clone -b <BRANCH> https://github.com/InferenceQL/inferenceql.structure-learning.git
```

Send files to remote instance:

``` shell
./upload.sh <PATH>
```

Send files to remote instance:

``` shell
./download.sh <PATH>
```

Destroy all cloud infrastructure:

``` shell
terraform destroy
```
