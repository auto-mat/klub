import os
import pathlib
import subprocess
import shutil

from django.contrib.staticfiles import finders
from django.core.management import BaseCommand, CommandError

from django.conf import settings


class Command(BaseCommand):
    help = 'Build js ContentTools library' # noqa

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--npm', dest='npm', default='/usr/bin/npm',
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

        # Target dirs
        self.cttools_target_dir = (
            pathlib.Path(settings.BASE_DIR) / 'bower_components' / 'ContentTools'
        )

        self.cttools_target_scripts_dir = self.cttools_target_dir / 'src' / 'scripts'
        self.cttools_target_styles_dir = self.cttools_target_dir / 'src' / 'styles' / 'ui'
        self.cttools_target_fonts_dir = self.cttools_target_dir / 'build' / 'images'

        self.__copy_coffee_scripts()
        self.__copy_sass_styles()
        self.__copy_fonts()
        self.__copy_gruntfile()

        os.chdir(self.cttools_target_dir)

        self.__install_npm_packages()
        self.__install_grunt_cli()
        self.__run_grunt_build_cmd()

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

    def __copy_fonts(self):
        # Copy font icons
        font_icon_file = self.cttools_src_fonts_dir / 'icons.woff'
        shutil.copy(font_icon_file, self.cttools_target_fonts_dir / font_icon_file.name)

    def __copy_gruntfile(self):
        # Copy Gruntfile
        grunt_file = pathlib.Path(self.js_src_dir) / 'contenttools' / 'Gruntfile.coffee'
        shutil.copy(grunt_file, self.cttools_target_dir / grunt_file.name)

    def __install_npm_packages(self):
        # Install npm packages
        p = subprocess.Popen(
            [self.npm_path, 'install'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            self.stdout.write('Error executing command {} install'.format(self.npm_path))
            if stderr:
                raise CommandError(
                    'Error executing command {} install\n{}'.format(
                        self.npm_path,
                        stderr.decode('utf-8'),
                    ),
                )
            if stdout:
                raise CommandError(
                    'Error executing command {} install\n{}'.format(
                        self.npm_path,
                        stdout.decode('utf-8'),
                    ),
                )

    def __install_grunt_cli(self):
        # Install grunt-cli package

        p = subprocess.Popen(
            [self.npm_path, 'install', 'grunt-cli'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            if stderr:
                raise CommandError(
                    'Error executing command {} install grunt-cli\n{}'.format(
                        self.npm_path,
                        stderr.decode('utf-8'),
                    ),
                )
            if stdout:
                raise CommandError(
                    'Error executing command {} install grunt-cli\n{}'.format(
                        self.npm_path,
                        stdout.decode('utf-8'),
                    ),
                )

    def __run_grunt_build_cmd(self):
        # Run grunt build
        command = self.cttools_target_dir / 'node_modules' / 'grunt-cli' / 'bin' / 'grunt'
        p = subprocess.Popen(
            [command, 'build'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            if stderr:
                raise CommandError(
                    'Error executing command {} build\n{}'.format(
                        command,
                        stderr.decode('utf-8'),
                    ),
                )
            if stdout:
                raise CommandError(
                    'Error executing command {} build\n{}'.format(
                        command,
                        stdout.decode('utf-8'),
                    ),
                )
