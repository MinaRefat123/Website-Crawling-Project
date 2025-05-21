const gulp = require('gulp');
const shell = require('gulp-shell');
const clean = require('gulp-clean');

// Clean build directory
gulp.task('clean', () => {
  return gulp.src('dist', { read: false, allowEmpty: true })
    .pipe(clean());
});

// Lint Python code
gulp.task('lint', shell.task('pylint crawler.py'));

// Run tests
gulp.task('test', shell.task('pytest tests/'));

// Copy files to dist for deployment
gulp.task('build', () => {
  return gulp.src(['crawler.py', 'requirements.txt', 'package.json'])
    .pipe(gulp.dest('dist'));
});

// Default task: clean, lint, test, build
gulp.task('default', gulp.series('clean', 'lint', 'test', 'build'));