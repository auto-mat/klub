import os
import pathlib
import shutil
import subprocess

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Build js ContentTools library' # noqa

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--npm', 
            dest='npm', 
            default='/usr/bin/npm',
            help='Npm js package manager path',
        )

    def handle(self, *args, **options):
        self.npm_path = options.get('npm')
        _finders = finders.AppDirectoriesFinder()

        self.npm_path = pathlib.Path(self.npm_path)
        if not self.npm_path.exists():
            raise CommandError("Npm path '{}' doesn't exist.".format(self.npm_path))

        # Aklub app assets dirs
        self.js_src_dir = _finders.find_in_app(
            app='aklub',
            path='aklub/js',
        )
        self.styles_src_dir = _finders.find_in_app(
            app='aklub',
            path='aklub/css',
        )
        self.fonts_src_dir = _finders.find_in_app(
            app='aklub',
            path='aklub/fonts',
        )

        self.cttools_coffee_src_scripts_dir = (
            pathlib.Path(self.js_src_dir) / 'contenttools' / 'src' / 'scripts'
        )
        self.cttools_src_styles_dir = (
            pathlib.Path(self.styles_src_dir) / 'contenttools' / 'src' / 'styles' / 'ui'
        )
        self.cttools_src_fonts_dir = (
            pathlib.Path(self.fonts_src_dir) / 'contenttools'
        )
        self.cttools_src_sandbox_styles_dir = (
            pathlib.Path(self.styles_src_dir) / 'contenttools' / 'src' / 'sandbox' / 'styles'
        )

        # Target dirs
        self.cttools_target_dir = (
            pathlib.Path(settings.BASE_DIR) / 'bower_components' / 'ContentTools'
        )

        self.cttools_target_scripts_dir = self.cttools_target_dir / 'src' / 'scripts'
        self.cttools_target_styles_dir = self.cttools_target_dir / 'src' / 'styles' / 'ui'
        self.cttools_target_fonts_dir = self.cttools_target_dir / 'build' / 'images'
        self.cttools_target_sandbox_dir = self.cttools_target_dir / 'src' / 'sandbox'

        self.__copy_coffee_scripts()
        self.__copy_sass_styles()
        self.__copy_fonts()
        self.__copy_gruntfile()

        os.chdir(self.cttools_target_dir)

        # Install npm packages
        self.__install(
            [self.npm_path, 'install'],
            self.npm_path,
            )
        # Install grunt-cli
        self.__install(
            [self.npm_path, 'install', 'grunt-cli'],
            self.npm_path,
            'install grunt-cli',
            )
        # Build ContentTools
        program = self.cttools_target_dir / 'node_modules' / 'grunt-cli' / 'bin' / 'grunt'
        self.__install(
            [program, 'build'],
            program,
            'build',
            )
        # Build ContentTools sandbox
        self.__install(
            [program, 'sandbox'],
            program,
            'sandbox',
            )

        shutil.rmtree('node_modules/')

    def __copy_coffee_scripts(self):
        # Copy coffee scripts
        scripts = self.cttools_coffee_src_scripts_dir.glob('*.coffee')
        for script_file in scripts:
            shutil.copy(script_file, self.cttools_target_scripts_dir / script_file.name)

    def __copy_sass_styles(self):
        # Copy sass styles
        styles = self.cttools_src_styles_dir.glob('*.scss')
        for style_file in styles:
            shutil.copy(style_file, self.cttools_target_styles_dir / style_file.name)

        _ui_scss_file = self.cttools_target_styles_dir / '_ui.scss'
        with open(_ui_scss_file, 'a+') as f:
            f.seek(0)
            content = f.read()
            if '@import "custom-toolbox";' not in content:
                f.write('\n@import "custom-toolbox";')

        _src_sandbox_scss_file = self.cttools_src_sandbox_styles_dir / 'sandbox.scss'
        _target_sandbox_scss_file = self.cttools_target_sandbox_dir / 'sandbox.scss'
        with open(_src_sandbox_scss_file, 'r') as f_read, open(_target_sandbox_scss_file, 'r+') as f_write:
            text = f_read.readlines()
            append_text = []
            for line in text:
                if '$max-width:' in line:
                    replace_text = line
                else:
                    append_text.append(line)
            content = f_write.read().replace('$max-width: 920px;', replace_text)
            content += ''.join(append_text)
            f_write.seek(0)
            f_write.write(content)

    def __copy_fonts(self):
        # Copy font icons
        font_icon_file = self.cttools_src_fonts_dir / 'icons.woff'
        shutil.copy(font_icon_file, self.cttools_target_fonts_dir / font_icon_file.name)

    def __copy_gruntfile(self):
        # Copy Gruntfile
        grunt_file = pathlib.Path(self.js_src_dir) / 'contenttools' / 'Gruntfile.coffee'
        shutil.copy(grunt_file, self.cttools_target_dir / grunt_file.name)

    def __install(self, command, program, package='install'):
        def raise_command_error(stream):
            raise CommandError(
                f'Error executing command {program} '
                f'{package}\n{stream}'
            )

        # Install package
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            if stderr:
                raise_command_error(stderr.decode('utf-8'))
            if stdout:
                raise_command_error(stdout.decode('utf-8'))
