import json
import os
import pathlib
import re
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
            raise CommandError(f"Npm path '{self.npm_path}' doesn't exist.")

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
            pathlib.Path(self.js_src_dir) / 'contenttools' / 'src' /
            'scripts'
        )
        self.cttools_src_styles_dir = (
            pathlib.Path(self.styles_src_dir) / 'contenttools' / 'src' /
            'styles' / 'ui'
        )
        self.cttools_src_fonts_dir = (
            pathlib.Path(self.fonts_src_dir) / 'contenttools'
        )
        self.cttools_src_sandbox_styles_dir = (
            pathlib.Path(self.styles_src_dir) / 'contenttools' / 'src' /
            'sandbox' / 'styles'
        )
        self.cttools_src_trans_dir = (
            pathlib.Path(self.js_src_dir) / 'contenttools' / 'src' /
            'translations'
        )

        # Target dirs
        self.cttools_target_dir = (
            pathlib.Path(settings.BASE_DIR) / 'bower_components' /
            'ContentTools'
        )

        self.cttools_target_scripts_dir = (
            self.cttools_target_dir / 'src' / 'scripts'
        )
        self.cttools_target_styles_dir = (
            self.cttools_target_dir / 'src' / 'styles' / 'ui'
        )
        self.cttools_target_fonts_dir = (
            self.cttools_target_dir / 'build' / 'images'
        )
        self.cttools_target_sandbox_dir = (
            self.cttools_target_dir / 'src' / 'sandbox'
        )
        self.cttools_target_sandbox__build_dir = (
            self.cttools_target_dir / 'sandbox'
        )
        self.cttools_target_trans_dir = (
            self.cttools_target_dir / 'translations'
        )

        self.__copy_coffee_scripts()
        self.__copy_sass_styles()
        self.__copy_fonts()
        self.__copy_gruntfile()
        self.__copy_localizations()

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
        grunt = (
            self.cttools_target_dir / 'node_modules' / 'grunt-cli' /
            'bin' / 'grunt'
        )
        self.__install(
            [grunt, 'build'],
            grunt,
            'build',
            )
        # Build ContentTools sandbox
        self.__install(
            [grunt, 'sandbox'],
            grunt,
            'sandbox',
            )

        shutil.rmtree('node_modules/')

    def __copy_coffee_scripts(self):
        # Copy coffee scripts
        scripts = self.cttools_coffee_src_scripts_dir.glob('*.coffee')
        for script_file in scripts:
            shutil.copy(
                script_file,
                self.cttools_target_scripts_dir / script_file.name,
            )

    def __copy_sass_styles(self):
        # Copy sass styles
        styles = self.cttools_src_styles_dir.glob('*.scss')
        for style_file in styles:
            shutil.copy(
                style_file,
                self.cttools_target_styles_dir / style_file.name,
            )

        _ui_scss_file = self.cttools_target_styles_dir / '_ui.scss'
        with open(_ui_scss_file, 'a+') as f:
            f.seek(0)
            content = f.read()
            if '@import "custom-toolbox";' not in content:
                f.write('\n@import "custom-toolbox";')

        # Copy sandbox append file
        sandbox_append_scss_file = (
            self.cttools_src_sandbox_styles_dir / 'sandbox-append.scss'
        )
        shutil.copy(sandbox_append_scss_file, self.cttools_target_sandbox_dir)

        # Apply sandbox replace file
        _src_sandbox_scss_file = (
            self.cttools_src_sandbox_styles_dir / 'sandbox-replace.scss'
        )
        _target_sandbox_scss_file = (
            self.cttools_target_sandbox_dir / 'sandbox.scss'
        )

        with open(_src_sandbox_scss_file, 'r') as f_read, \
                open(_target_sandbox_scss_file, 'r+') as f_write:

            new_content = None
            source_content = f_read.readlines()

            max_width_base_text = '$max-width: 920px;'

            for line in source_content:
                if '$max-width:' in line:
                    max_width_replace_text = line

            target_content = f_write.read()

            if max_width_base_text in target_content:
                new_content = target_content.replace(
                    max_width_base_text,
                    max_width_replace_text,
                )

            if not new_content:
                new_content = target_content

            new_content = self.__replace_css_import(new_content)

            if new_content:
                f_write.seek(0)
                f_write.truncate(0)
                f_write.write(new_content)

    def __replace_css_import(self, content):
        """Replace default css import path with correct path"""

        css_imports = re.findall('@import.*.;', content)

        for css_import in css_imports:
            css_import_split = css_import.split(' ')

            try:
                css_import_path = pathlib.PurePath(
                    css_import_split[1][:-1].replace('"', ''),
                )
            except IndexError:
                continue

            css_import_path_parts = list(css_import_path.parts)
            if css_import_path_parts.count('..') < 2:
                continue

            css_import_path_parts.pop(0)

            css_import_new_path = pathlib.PurePath(*css_import_path_parts)
            new_css_import_text = (
                f"{css_import_split[0]} \"{css_import_new_path.as_posix()}\";"
            )
            content = content.replace(css_import, new_css_import_text)

        return content

    def __copy_fonts(self):
        """Copy font icons"""

        font_icon_file = self.cttools_src_fonts_dir / 'icons.woff'
        shutil.copy(
            font_icon_file,
            self.cttools_target_fonts_dir / font_icon_file.name,
        )

    def __copy_gruntfile(self):
        """Copy Gruntfile"""

        grunt_file = (
            pathlib.Path(self.js_src_dir) / 'contenttools' / 'Gruntfile.coffee'
        )
        shutil.copy(grunt_file, self.cttools_target_dir / grunt_file.name)

    def __copy_localizations(self):
        """Copy localization json files"""

        trans_src_files = self.cttools_src_trans_dir.glob('*.json')

        for trans_src_file in trans_src_files:

            trans_target_file = (self.cttools_target_trans_dir /
                                 trans_src_file.name)

            with open(trans_src_file, 'r') as src_read_trans_f, \
                    open(trans_target_file, 'r+', encoding='utf-8') as \
                    target_write_trans_f:

                src_trans = json.load(src_read_trans_f)
                target_trans = json.load(target_write_trans_f)
                target_trans_keys = target_trans.keys()
                update_trans = {}

                for trans_string in src_trans.keys():
                    if trans_string not in target_trans_keys:
                        update_trans[trans_string] = src_trans[trans_string]

                if update_trans:
                    target_trans.update(update_trans)

                    target_write_trans_f.seek(0)
                    target_write_trans_f.truncate(0)
                    json.dump(
                        target_trans, target_write_trans_f,
                        indent=4, ensure_ascii=False, sort_keys=True,
                    )

    def __install(self, command, program, package='install'):
        """Install/build package"""

        def raise_command_error(stream):
            raise CommandError(
                f"Error executing command {program} "
                f"{package}\n{stream}"
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
