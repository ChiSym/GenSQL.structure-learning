#! /usr/bin/env node

/*
 * This script reads in a JSON file with a single string.
 * It then compresses the string using lz-string, and then
 * writes out that compressed string to stdout.
 */

var lzString = require('lz-string');
var fs = require('fs');

if (process.argv.length < 3) {
  console.error('Usage: lz-string <input_file>');
  process.exit(1);
}

let raw_data = fs.readFileSync(process.argv[2]);
let transit_string = JSON.parse(raw_data);
console.log(JSON.stringify(lzString.compress(transit_string)));
