module.exports = (grunt) ->

    require('es6-promise').polyfill()

    # Project configuration
    grunt.initConfig({

        pkg: grunt.file.readJSON('package.json')

        coffee:
            options:
                join: true

            build:
                #options:
                #    sourceMap: true
                files:
                    'src/tmp/template_widget.js': [
                         'src/script/mixins.coffee',
                        'src/script/app_init.coffee',
                        'src/script/popover_dialog.coffee',
                        'src/script/get_template_name_dialog.coffee',
                        'src/script/edit_template_dialog.coffee',
                        'src/script/html_template_widget.coffee',
                        'src/script/process_template.coffee'

                    ]

        uglify:
            options:
                banner: '/*! <%= pkg.name %> v<%= pkg.version %> by <%= pkg.author.name %> <<%= pkg.author.email %>> */\n'
                mangle: true
                # sourceMap: true
                # sourceMapIn: './src/tmp/template_widget.js.map'

            build:
                src: 'src/tmp/template_widget.js'
                dest: '../template_widget.min.js'

        clean:
            build: ['src/tmp']

        jasmine:
            build:
                src: ['build/content-tools.js']
                options:
                    specs: 'spec/content-tools-spec.js'
                    helpers: 'spec/spec-helper.js'

        watch:
            build:
                files: [
                    'src/scripts/**/*.coffee',
                    ]
                tasks: ['build']

            spec:
                files: ['src/spec/**/*.coffee']
                tasks: ['spec']
    })

    # Plug-ins
    grunt.loadNpmTasks 'grunt-contrib-clean'
    grunt.loadNpmTasks 'grunt-contrib-coffee'
    grunt.loadNpmTasks 'grunt-contrib-jasmine'
    grunt.loadNpmTasks 'grunt-contrib-uglify'
    grunt.loadNpmTasks 'grunt-contrib-watch'

    # Tasks
    grunt.registerTask 'build', [
        'coffee:build'
        'uglify:build'
        'clean:build'
    ]

    grunt.registerTask 'spec', [
        'coffee:spec'
    ]

    grunt.registerTask 'watch-build', ['watch:build']
    grunt.registerTask 'watch-spec', ['watch:spec']
