#!/bin/bash
# npx google-closure-compiler --js=normal/acceliaimg.durasite.net-images-youtube.js --js_output_file=test.js

TARGET_DIR='data/normal'
OUTPUT_DIR='data/created_closure_compiler'

for file in `\find $TARGET_DIR -maxdepth 1 -type f`; do
    echo $(basename $file)
    npx google-closure-compiler --js=$file --js_output_file=$OUTPUT_DIR/$(basename $file)
    # echo $OUTPUT_DIR/$(basename $file)
done
