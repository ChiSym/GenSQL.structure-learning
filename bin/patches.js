#! /usr/bin/env node

const _ = require("lodash");
const cliProgress = require("cli-progress");
const fs = require("fs");
const rfc6902 = require("rfc6902");

const [, , file] = process.argv;

const raw = fs.readFileSync(file);
const models = JSON.parse(raw);

const pairs = _.zip(_.dropRight(models, 1), _.drop(models, 1));
const diffs = [];

const progress = new cliProgress.SingleBar(
  {},
  cliProgress.Presets.shades_classic
);
progress.start(pairs.length, 0);

pairs.forEach(([a, b]) => {
  diff = rfc6902.createPatch(a, b);
  diffs.push(diff);
  progress.increment();
});

progress.stop();

const out = {
  model: models[0],
  diffs: diffs,
  maxRows: _.last(models).X.length
};

const json = JSON.stringify(out);
process.stdout.write(json);
process.stdout.write("\n");
