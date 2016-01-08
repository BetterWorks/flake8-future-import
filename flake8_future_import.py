#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Extension for flake8 to test for certain __future__ imports"""
from __future__ import print_function

import sys

try:
    import argparse
except ImportError as e:
    argparse = e

import ast

__version__ = '0.3.2'


class FutureImportVisitor(ast.NodeVisitor):

    def __init__(self):
        super(FutureImportVisitor, self).__init__()
        self.future_imports = []

        self._uses_code = False
        self._uses_print = False
        self._uses_division = False
        self._uses_import = False
        self._uses_str_literals = False

    def _is_print(self, node):
        # python 2
        if hasattr(ast, 'Print') and isinstance(node, ast.Print):
            return True

        # python 3
        if isinstance(node, ast.Call) and \
           isinstance(node.func, ast.Name) and \
           node.func.id == 'print':
            return True

        return False

    def visit_ImportFrom(self, node):
        if node.module == '__future__':
            self.future_imports += [node]
        else:
            self._uses_import = True

    def generic_visit(self, node):
        if not isinstance(node, ast.Module):
            self._uses_code = True

        if isinstance(node, ast.Str):
            self._uses_str_literals = True
        elif self._is_print(node):
            self._uses_print = True
        elif isinstance(node, ast.Div):
            self._uses_division = True
        elif isinstance(node, ast.Import):
            self._uses_import = True

        super(FutureImportVisitor, self).generic_visit(node)

    @property
    def uses_code(self):
        return self._uses_code or self.future_imports


class Flake8Argparse(object):

    @classmethod
    def add_options(cls, parser):
        class Wrapper(object):
            def add_argument(self, *args, **kwargs):
                # flake8 uses config_options to handle stuff like 'store_true'
                if kwargs['action'] == 'store_true':
                    for opt in args:
                        if opt.startswith('--'):
                            break
                    else:
                        opt = args[0]
                    parser.config_options.append(opt.lstrip('-'))
                parser.add_option(*args, **kwargs)

        cls.add_arguments(Wrapper())

    @classmethod
    def add_arguments(cls, parser):
        pass


class FutureImportChecker(Flake8Argparse):

    # Order important as it defines the error code
    AVAILABLE_IMPORTS = ('division', 'absolute_import', 'with_statement',
                         'print_function', 'unicode_literals', 'generator_stop')

    version = __version__
    name = 'flake8-future-import'
    require_code = True
    require_used = False

    def __init__(self, tree, filename):
        self.tree = tree

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--require-code', action='store_true',
                            help='Do only apply to files which not only have '
                                 'comments and (doc)strings')
        parser.add_argument('--require-used', action='store_true',
                            help='Only alert when relevant features are used')

    @classmethod
    def parse_options(cls, options):
        cls.require_code = options.require_code
        cls.require_used = options.require_used

    def _generate_error(self, future_import, lineno, present):
        code = 10 + self.AVAILABLE_IMPORTS.index(future_import)
        if present:
            msg = 'FI{0} __future__ import "{1}" present'
            code += 40
        else:
            msg = 'FI{0} __future__ import "{1}" missing'
        return lineno, 0, msg.format(code, future_import), type(self)

    def run(self):
        visitor = FutureImportVisitor()
        visitor.visit(self.tree)
        if self.require_code and not visitor.uses_code:
            return
        present = set()
        for import_node in visitor.future_imports:
            for alias in import_node.names:
                if alias.name not in self.AVAILABLE_IMPORTS:
                    # unknown code
                    continue
                yield self._generate_error(alias.name, import_node.lineno, True)
                present.add(alias.name)
        for name in self.AVAILABLE_IMPORTS:
            if name in present:
                continue

            if self.require_used:
                if name == 'print_function' and not visitor._uses_print:
                    continue

                if name == 'division' and not visitor._uses_division:
                    continue

                if name == 'absolute_import' and not visitor._uses_import:
                    continue

                if name == 'unicode_literals' and not visitor._uses_str_literals:
                    continue

            yield self._generate_error(name, 1, False)


def main(args):
    if isinstance(argparse, ImportError):
        print('argparse is required for the standalone version.')
        return
    parser = argparse.ArgumentParser()
    choices = set('FI' + str(10 + choice) for choice in
                  range(len(FutureImportChecker.AVAILABLE_IMPORTS)))
    choices |= set('FI' + str(50 + choice) for choice in
                   range(len(FutureImportChecker.AVAILABLE_IMPORTS)))
    parser.add_argument('--ignore', help='Ignore the given comma-separated '
                                         'codes')
    FutureImportChecker.add_arguments(parser)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args(args)
    FutureImportChecker.parse_options(args)
    if args.ignore:
        ignored = set(args.ignore.split(','))
        unrecognized = ignored - choices
        ignored &= choices
        if unrecognized:
            invalid = set()
            for invalid_code in unrecognized:
                no_valid = True
                if not invalid:
                    for valid_code in choices:
                        if valid_code.startswith(invalid_code):
                            ignored.add(valid_code)
                            no_valid = False
                if no_valid:
                    invalid.add(invalid_code)
            if invalid:
                raise ValueError('The code(s) is/are invalid: "{0}"'.format(
                    '", "'.join(invalid)))
    else:
        ignored = set()
    for filename in args.files:
        with open(filename, 'rb') as f:
            tree = compile(f.read(), filename, 'exec', ast.PyCF_ONLY_AST)
        for line, char, msg, checker in FutureImportChecker(tree,
                                                            filename).run():
            if msg[:4] not in ignored:
                print('{0}:{1}:{2}: {3}'.format(filename, line, char + 1, msg))


if __name__ == '__main__':
    main(sys.argv[1:])
