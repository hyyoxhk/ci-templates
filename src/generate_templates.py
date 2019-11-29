#!/bin/env python3
# vim: set expandtab shiftwidth=4 tabstop=4 textwidth=0:

import jinja2
import os
import yaml

from pathlib import Path

if __name__ == '__main__':
    config_data = {}

    env = jinja2.Environment(loader=jinja2.FileSystemLoader('./src'),
                             trim_blocks=True,
                             lstrip_blocks=True)

    # load the various definitions in the provided YAML files
    src_folder = Path('src')

    defaults_template = env.get_template('defaults.yml')

    for distrib in [x for x in src_folder.iterdir()
                    if (x.name.endswith('.yml')
                        and x.name not in 'defaults.yml')]:
        with open(distrib) as fd:
            data = yaml.load(fd, Loader=yaml.Loader)

            # for each root element in each yaml file
            for config in data.values():

                # add the uppercase version of each key
                for key, value in [(k, v) for (k, v) in config.items()
                                   if isinstance(v, str)]:
                    config[key.upper()] = value.upper()

                # special case I could not figure out with defaults.yml
                if 'VERSION' in config:
                    del(config['VERSION'])

                # render the defaults template with the current root element
                defaults = yaml.load(defaults_template.render(config),
                                     Loader=yaml.Loader)['defaults']

                # add missing keys from the generated defaults
                for key, value in defaults.items():
                    if key not in config:
                        config[key] = value

            # store the geenrated values in the base config dictionnary
            config_data.update(data)

    # load our distribution template
    template = env.get_template('template.tmpl')

    out_folder = Path('templates')
    if not out_folder.exists():
        os.mkdir(out_folder)

    # and render each distribution in the templates source directory
    for distrib, config in config_data.items():
        dest = out_folder / f'{distrib}.yml'
        print(f'generating {dest}')
        with open(dest, 'w') as out_stream:
            template.stream(config).dump(out_stream)
