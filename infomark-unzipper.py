#!/usr/bin/env python3
import atexit

import click
import zipfile as zf
import io
import re
import os
import shutil
import fileinput
from collections import namedtuple
from pathlib import Path

Student = namedtuple('Student', 'firstname surname zipfile')


def project_from_zip(file: str, sheet):
    zip = zf.ZipFile(file)
    task = re.compile('task[0-9]+').search(file).group(0)

    students = get_all_students(zip)
    create_project_directory(students, f"sheet{sheet}", task)

    # cleanup
    zip.close()
    for student in students:
        student.zipfile.close()

    print("All done!")


def create_project_directory(students, sheet, task):
    project_folder_name = f"{sheet}-{task}-unzipped"
    if os.path.exists(project_folder_name):
        if click.confirm(f"Project folder {project_folder_name} exists. Delete?"):
            shutil.rmtree(project_folder_name)
        else:
            print("Cannot proceed with the folder being present already. Exiting.")
    os.mkdir(project_folder_name)
    src_path = os.path.join(project_folder_name, "src", "main", "java", "com", "infomark")
    os.makedirs(src_path)

    for student in students:
        name_combined = student.firstname + student.surname
        code_folder = os.path.join(src_path, f"{name_combined}")
        os.mkdir(code_folder)
        student.zipfile.extractall(code_folder)

        # fixing all packages in the files:
        for path in Path(code_folder).rglob('*.java'):
            path_split = os.path.normpath(path).split(os.sep)
            # we're getting the path from the last occurence of com to the last occurence of main
            package = ".".join(path_split[last_occurence(path_split, 'com'):last_occurence(path_split, 'main')])
            prepend_package_prefix(path, package)

def last_occurence(list, item):
    return len(list) - list[::-1].index(item) - 1

def prepend_package_prefix(file, prefix):
    p = re.compile("package (.+);")
    new_content = ""
    with open(file, "rb") as f:
        for line in f.readlines():
            # one of these two should work...
            try:
                line = line.decode('utf-8')
            except UnicodeDecodeError:
                line = line.decode('windows-1252')
            if line.lstrip().startswith("package"):
                line = re.sub(r'package (.+);', r'package ' + prefix + r'.\1;', line)
            new_content += line

    with open(file, "w+") as f:
        f.write(new_content)


def get_all_students(zip):
    """Returns student tuple for all zipped submissions found in the zip file."""
    students = []
    # creating all the student objects that we can zip files of
    for filename in zip.namelist():
        if not filename.endswith(".zip"):
            continue
        firstname, surname = split_zipname(filename)
        student_zip_data = io.BytesIO(zip.open(filename).read())
        student_zipfile = zf.ZipFile(student_zip_data)
        students.append(Student(firstname, surname, student_zipfile))
    return students


def split_zipname(zipname: str):
    """Splits name of student submission zip file into (firstname,surname) and cleans the names"""
    firstname, surname = zipname.strip(".zip").split("-", 1)
    return clean_name(firstname), clean_name(surname)


def clean_name(name: str):
    stripped = name.replace("-", "").replace("_", "").replace(" ", "").strip()
    # remove accents
    normalized = unicodedata.normalize('NFKD', stripped).encode('ASCII', 'ignore').decode('UTF-8', 'ignore')
    return normalized


@click.argument("zipfile", type=click.Path(exists=True), nargs=-1, required=True)
@click.option("-s", "--sheet", type=int, prompt="Enter the number of the current sheet",
              help="Number of the current sheet.")
@click.command()
def cli(zipfile, sheet):
    # validation
    for file in zipfile:
        if not file.endswith(".zip"):
            raise ValueError(f"Given file {file} was not a zip file.")
    for file in zipfile:
        project_from_zip(file, sheet)


if __name__ == "__main__":
    cli()
