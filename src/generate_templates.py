#!/bin/env python3
# vim: set expandtab shiftwidth=4 tabstop=4 textwidth=0:

import jinja2
import os
import yaml

from pathlib import Path

if __name__ == '__main__':
    config_data = {}

    # load the various definitions in the provided YAML files
    src_folder = Path('src')
    for distrib in [x for x in src_folder.iterdir()
                    if x.name.endswith('.yml')]:
        with open(distrib) as fd:
            data = yaml.load(fd, Loader=yaml.Loader)

            # add some generated variables to keep the template simple
            for config in data.values():
                config['DISTRIBUTION'] = config['distribution'].upper()
                if 'image' in config:
                    config['docker_repo'] = config['image'].split('/')[0]
                else:
                    config['docker_repo'] = config['distribution']
                if 'version' in config:
                    config['VERSION'] = config['version']
                    if 'image' not in config:
                        config['image'] = f'{config["distribution"]}:{config["version"]}'
                else:
                    config['VERSION'] = f'${config["DISTRIBUTION"]}_VERSION'
                if 'image' not in config:
                    config['image'] = '$DISTRO:$DISTRO_VERSION'
                config['PACKAGES'] = f'{config["DISTRIBUTION"]}_{config["package_type"]}'.upper()
                if 'aarch64' not in config:
                    config['aarch64'] = True
            config_data.update(data)

    env = jinja2.Environment(loader = jinja2.FileSystemLoader('./src'),
                             trim_blocks=True,
                             lstrip_blocks=True)

    template = env.get_template('template.tmpl')

    out_folder = Path('templates')
    if not out_folder.exists():
        os.mkdir(out_folder)

    for distrib, config in config_data.items():
        dest = out_folder / f'{distrib}.yml'
        print(f'generating {dest}')
        with open(dest, 'w') as out_stream:
            template.stream(config).dump(out_stream)
