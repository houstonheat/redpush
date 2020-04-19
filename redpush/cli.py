"""
    Tool to manage the queries, graphs and dashboards in a redash server from yaml definitions.
    Treating all of them as code, so you can version control them as you should :-)
"""
import os
import click
import requests
from slugify import slugify
import csv
from ruamel import yaml
import difflib
import sys
from ruamel.yaml.compat import StringIO
from operator import itemgetter
from redpush import redash

def save_yaml(queries, filename):
    """
        Save the queries into yaml
    """
    stream = open(filename, 'w')
    yaml.scalarstring.walk_tree(queries)
    yaml.dump(queries, stream,Dumper=yaml.RoundTripDumper)
    stream.close()

def read_yaml(filename):
    """
        Load the queries from a yaml file
    """
    file = open(filename, 'r')
    contents = yaml.load(file, yaml.RoundTripLoader)
    file.close()
    return contents

def sort_queries(queries):
    """
        Sort the list of queries so we can compare them easily afterwards
    """
    # First short queries per id
    queries = sorted(queries, key=itemgetter('redpush_id'))
    # then each query, sort the properties alphabetically 
    sorted_keys = [] 
    for item in queries:
        my_sorted_dict = {}   
        for k in sorted(item):
            my_sorted_dict[k] = item[k]
        sorted_keys.append(my_sorted_dict)
    return sorted_keys

@click.group()
def cli():
    pass

@cli.command()
@click.option('--redash-url',envvar='REDASH_URL')
@click.option('--api-key',envvar='REDASH_KEY', help="API Key")
@click.option('-o', '--out-file', help="File to store the queries", type=str)
@click.option('--split-file', is_flag=True, help="Split dump to separate Yaml files")
@click.option('-p', '--out-path', help="Folder to store Yaml files", type=str)
@click.option('--include-dashboards', is_flag=True, help="Dump include Dashboard")
def dump(redash_url, api_key, out_file, split_file, out_path, include_dashboards):
    if split_file:
        if out_path is None:
            click.echo('No out path provided')
            return
    else:
        if out_file is None:
            click.echo('No out file provided')
            return

    server = redash.Redash(redash_url, api_key)
    queries = server.Get_Queries()
    queries = server.Get_Full_Queries(queries)

    if split_file:
        queries_path = os.path.join(out_path, 'queries')
        if not os.path.exists(queries_path):
            os.makedirs(queries_path)

        for item in queries:
            save_yaml(
                item,
                os.path.join(
                    queries_path,
                    '%s-%s.yaml' % (
                        item['id'],
                        slugify(item['name'])
                    )
                )
            )

        if include_dashboards:
            dashboards_path = os.path.join(out_path, 'dashboards')
            if not os.path.exists(dashboards_path):
                os.makedirs(dashboards_path)

            for item in server.Get_Dashboards():
                save_yaml(
                    item,
                    os.path.join(
                        dashboards_path,
                        '%s-%s.yaml' % (
                            item['id'],
                            slugify(item['name'])
                        )
                    )
                )

    else:
        save_yaml(queries, out_file)

@cli.command()
@click.option('--redash-url',envvar='REDASH_URL')
@click.option('--api-key',envvar='REDASH_KEY', help="API Key")
@click.option('-i', '--in-file', help="File to read the queries from", type=str)
def push(redash_url, api_key, in_file):
    
    if in_file is None:
        click.echo('No file provided')
        return
    server = redash.Redash(redash_url, api_key)
    old_queries = server.Get_Queries()
    old_queries = server.Get_Full_Queries(old_queries)

    new = read_yaml(in_file)
    server.Put_Queries(old_queries, new)
 
@cli.command()
@click.option('--redash-url',envvar='REDASH_URL')
@click.option('--api-key',envvar='REDASH_KEY', help="API Key")
@click.option('-i', '--in-file', help="File to read the queries from", type=str)
def archive(redash_url, api_key, in_file):
    
    if in_file is None:
        click.echo('No file provided')
        return
    server = redash.Redash(redash_url, api_key)
    server_queries = server.Get_Queries(True)

    new = read_yaml(in_file)
    server.Archive_Missing_Queries(server_queries, new)
 
@cli.command()
@click.option('--redash-url',envvar='REDASH_URL')
@click.option('--api-key',envvar='REDASH_KEY', help="API Key")
@click.option('-i', '--in-file', help="File to read the queries from", type=str)
def diff(redash_url, api_key, in_file):
    
    if in_file is None:
        click.echo('No file provided')
        return
    server = redash.Redash(redash_url, api_key)
    old_queries = server.Get_Queries()
    old_queries = server.Get_Full_Queries(old_queries)
    old_sorted_queries = sort_queries(old_queries)

    old_stream = StringIO()
    yaml.scalarstring.walk_tree(old_sorted_queries)
    yaml.dump(old_sorted_queries, old_stream,Dumper=yaml.RoundTripDumper) 

    new_queries = read_yaml(in_file)
    new_sorted_queries = sort_queries(new_queries)

    new_stream = StringIO()
    yaml.scalarstring.walk_tree(new_sorted_queries)
    yaml.dump(new_sorted_queries, new_stream,Dumper=yaml.RoundTripDumper) 

    # diff = difflib.ndiff(old_stream.getvalue().strip().splitlines(),new_stream.getvalue().strip().splitlines())
    diff = difflib.HtmlDiff().make_file(old_stream.getvalue().strip().splitlines(),new_stream.getvalue().strip().splitlines(), "test.html")
    sys.stdout.writelines(diff)


@cli.command()
@click.option('--redash-url',envvar='REDASH_URL')
@click.option('--api-key',envvar='REDASH_KEY', help="API Key")
@click.option('-o', '--out-file', help="File to store the queries", type=str)
def dashboards(redash_url, api_key, out_file):
    if out_file is None:
        click.echo('No out file provided')
        return
    server = redash.Redash(redash_url, api_key)
    dashboards = server.Get_Dashboards()

    save_yaml(dashboards, out_file)

@cli.command()
@click.option('--redash-url',envvar='REDASH_URL')
@click.option('--api-key',envvar='REDASH_KEY', help="API Key")
@click.option('-i', '--in-file', help="File (csv) to read users from. CSV format='name,lastname,email'", type=str)
def users(redash_url, api_key, in_file):
    if in_file is None:
        click.echo('No file provided')
        return
    
    users = []
    with open(in_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
                user = {'name': row[0] + ' ' + row[1], 'email': row[2]}   # TODO validation
                users.append(user)

    server = redash.Redash(redash_url, api_key)

    dashboards = server.Create_Users(users)



if __name__ == '__main__':
    cli()
