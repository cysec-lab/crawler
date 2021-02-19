// dirの中のファイルたちをoutput_dirにobfscatorしたものを保存するコード
// NodeJS初めて使ったからエラー処理とかはなにも書いていない
// 多分ディレクトリ内にディレクトリとかあったらバグる
// $ node src/jjencoder.js

const dir = 'data/naist_data/normal'
const output_dir = 'data/created_obfscator_base64_compact'

var JavaScriptObfuscator = require('javascript-obfuscator');


const fs = require('fs');
const path = require('path');
var counter = 0;
fs.readdir(dir, function(err, files){
        if (err) throw err;
    files.forEach(function (file) {
        let text = fs.readFileSync(dir + '/' + file, 'utf-8');
        console.log(file);
        counter += 1;
        try {
            var obfuscationResult = JavaScriptObfuscator.obfuscate(text,
                {
                    compact: true,
                    controlFlowFlattening: true,
                    controlFlowFlatteningThreshold: 1,
                    numbersToExpressions: true,
                    simplify: true,
                    shuffleStringArray: true,
                    splitStrings: true,
                    stringArrayThreshold: 1,
                    stringArrayEncoding: [
                        'base64'
                    ]
                }
            );
            // console.log(obfuscationResult.getObfuscatedCode());
            fs.writeFileSync(output_dir + '/' + file, obfuscationResult.getObfuscatedCode());
        } catch (err) {
            console.error(err);
        }
    });
    console.log(counter + ' files obfed!');
});

