# inferenceql.structure-learning

## Setup

``` shell
gcloud auth login
```

``` shell
docker login
```

``` shell
mkdir -p data/raw
gsutil -m cp \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000000.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000001.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000002.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000003.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000004.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000005.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000006.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000007.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000008.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000009.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000010.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000011.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000012.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000013.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000014.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000015.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000016.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000017.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000018.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000019.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000020.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000021.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000022.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000023.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000024.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000025.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000026.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000027.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000028.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000029.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000030.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000031.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000032.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000033.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000034.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000035.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000036.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000037.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000038.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000039.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000040.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000041.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000042.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000043.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000044.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000045.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000046.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000047.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000048.csv" \
  "gs://civitech-ai-explore/voterfile/voterfile_000000000049.csv" \
  data/raw
```
