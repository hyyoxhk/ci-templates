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
    globs = yaml.load(defaults_template.render({}),
                      Loader=yaml.Loader)['globals']

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

                # add missing keys from the globals
                for key, value in globs.items():
                    if key not in config:
                        config[key] = value

            # store the generated values in the base config dictionnary
            config_data.update(data)

    # load our distribution template
    template = env.get_template('template.tmpl')
    # and our ci template
    template_ci = env.get_template('template-ci.tmpl')

    out_folder = Path('templates')
    if not out_folder.exists():
        os.mkdir(out_folder)

    # define a generator for the list of scripts to be run in each distribution
    def get_script():
        n = 0
        while True:
            yield globs['scripts'][n]
            n += 1
            n %= len(globs['scripts'])

    scripts = get_script()

    # and render each distribution in the templates source directory
    for distrib, config in sorted(config_data.items()):
        dest = out_folder / f'{distrib}.yml'
        dest_ci = f'{distrib}-ci.yml'

        # use the next script for this config
        config['script'] = next(scripts)

        print(f'generating {dest}')
        with open(dest, 'w') as out_stream:
            template.stream(config).dump(out_stream)
        print(f'generating {dest_ci}')
        with open(dest_ci, 'w') as out_stream:
            template_ci.stream(config).dump(out_stream)

    # finally, regenerate the .gitlab-ci.yml
    template_general_ci = env.get_template('gitlab-ci.tmpl')

    distribs = [d for d in sorted(config_data.keys()) if d not in ('defaults', 'globals')]
    dest = f'.gitlab-ci.yml'

    config = {'distribs': distribs}
    config.update(globs)

    print(f'generating {dest}')
    with open(dest, 'w') as out_stream:
        template_general_ci.stream(config).dump(out_stream)
