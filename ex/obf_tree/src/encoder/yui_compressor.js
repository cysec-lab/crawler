const dir = 'data/normal'
const output_dir = 'data/created_yui_compress'


const fs = require('fs');

const data = 'data/normal/assets.calendly.com-assets-external-widget.js'

fs.readdir(dir, function(err, files){
    if (err) throw err;
    files.forEach(function (file) {
        console.log(dir + '/' + file);
        compressor.compress(data, {
            //Compressor Options:
            charset: 'utf8',
            type: 'js',
            nomunge: true,
            'line-break': 80
        }, function(err, data, extra) {
            console.log(data);
            //err   If compressor encounters an error, it's stderr will be here
            //data  The compressed string, you write it out where you want it
            //extra The stderr (warnings are printed here in case you want to echo them
        });
    });
});
