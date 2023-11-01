import argparse
import os
import sys

from .archive import print_auto_archive_settings, update_auto_archive
from .database import get_db_path
from .data_dir import get_data_dir
from .errors import ValidationError
from .link import link, unlink

def validate_trained(command_name):
    if not os.path.exists(get_db_path()):
        raise ValidationError(f'must run `auto-labeler train` before running `{command_name}` command')

def main():
    parser = argparse.ArgumentParser('auto-labeler')
    subparsers = parser.add_subparsers(dest='command')

    train_parser = subparsers.add_parser('train')
    train_parser.add_argument('label', nargs='+')

    archive_parser = subparsers.add_parser('auto-archive')
    archive_parser.add_argument('label', nargs='?')
    archive_parser.add_argument('delay', type=int, nargs='?')

    subparsers.add_parser('label')

    subparsers.add_parser('link')
    subparsers.add_parser('unlink')
    subparsers.add_parser('data-dir')

    args = parser.parse_args()

    try:
        if args.command == 'train':
            from .train import train_command

            train_command(args.label)
        elif args.command == 'auto-archive':
            validate_trained('auto-archive')

            if args.label is None:
                print_auto_archive_settings()
            else:
                if args.delay is None:
                    raise ValidationError('you must provide a value for auto-archive delay')
                elif args.delay < -1:
                    raise ValidationError('the delay must be greater than or equal to -1')
                update_auto_archive(args.label, args.delay)
        elif args.command == 'label':
            validate_trained('label')
            
            from .classify import label_and_archive_emails

            label_and_archive_emails()
        elif args.command == 'link':
            link()
        elif args.command == 'unlink':
            unlink()
        elif args.command == 'data-dir':
            print(get_data_dir())
        else:
            parser.print_help()
    except ValidationError as e:
        print(f'auto-labeler: error: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()