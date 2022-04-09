var gulp = require('gulp');
var rsync = require('gulp-rsync');

var filesToMove = [
        './proto.py',
        './lib/*'
    ];

function deploy(done) {
  gulp.src(filesToMove)
    .pipe(rsync({
      root: '',
      hostname: 'root@199.192.21.240',
      destination: '/opt/tools_b-master',
    }))
   done();};


// The default task (called when you run `gulp` from cli) 
gulp.task('default', deploy);