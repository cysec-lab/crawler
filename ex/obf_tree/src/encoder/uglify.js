const dir = 'data/normal';
const output_dir = 'data/created_ugilfy';

var UglifyJS = require("uglify-js");

const fs = require('fs');
const path = require('path');
const { Console } = require("console");
var counter = 0;

fs.readdir(dir, function(err, files){
        if (err) throw err;
    files.forEach(function (file) {
        console.log(file);
        try {
            let text = fs.readFileSync(dir + '/' + file, 'utf-8');
            var result = UglifyJS.minify(text);
            // console.log(result.code);
            fs.writeFileSync(output_dir + '/' + file, result.code);
            counter += 1;
        } catch (err) {
            console.error(err);
        }
    });
    console.log(counter + ' files uglifyed!');
});