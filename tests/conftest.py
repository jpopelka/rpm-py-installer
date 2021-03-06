"""Common functions and a list of pytest.fixture here."""

import getpass
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager

import pytest

OS_RELEASE_FILE = '/etc/os-release'

install_path = os.path.abspath('install.py')
sys.path.insert(0, install_path)

pytest_plugins = ['helpers_namespace']

running_user = getpass.getuser()


def _get_os_id():
    os_id = None
    if not os.path.isfile(OS_RELEASE_FILE):
        return os_id

    with open(OS_RELEASE_FILE) as f_in:
        for line in f_in:
            match = re.search(r'^ID=[\'"]?(\w+)?[\'"]?$', line)
            if match:
                os_id = match.group(1)
                break

    return os_id


_os_id = _get_os_id()
_is_dnf = True if os.system('dnf --version') == 0 else False
_is_debian = True if os.system('apt-get --version') == 0 else False


def pytest_collection_modifyitems(items):
    for item in items:
        if item.get_marker('integration') is not None:
            pass
        else:
            item.add_marker(pytest.mark.unit)


@pytest.fixture
def install_script_path():
    return install_path


@pytest.fixture
def is_fedora():
    """Return if it is Fedora Linux."""
    return _os_id == 'fedora'


@pytest.fixture
def is_centos():
    """Return if it is CentOS Linux."""
    return _os_id == 'centos'


@pytest.fixture
def is_debian():
    """Return if it is Debian base Linux."""
    return _is_debian


@pytest.fixture
def rpm_version_info():
    p = subprocess.Popen(['rpm', '--version'], stdout=subprocess.PIPE)
    out = p.communicate()[0]
    out = out.decode()
    version_str = out.split()[2]
    version_info_list = re.findall(r'[0-9a-zA-Z]+', version_str)

    def convert_to_int(string):
        value = None
        if re.match(r'^\d+$', string):
            value = int(string)
        else:
            value = string
        return value

    version_info_list = [convert_to_int(s) for s in version_info_list]

    return tuple(version_info_list)


@pytest.fixture
def rpm_version_info_min_rpm_build_libs():
    return (4, 9)


@pytest.fixture
def rpm_version_info_min_setup_py_in():
    return (4, 10)


@pytest.fixture
def has_rpm_rpm_build_libs(
    rpm_version_info,
    rpm_version_info_min_rpm_build_libs
):
    return rpm_version_info >= rpm_version_info_min_rpm_build_libs


@pytest.fixture
def has_rpm_setup_py_in(
    rpm_version_info,
    rpm_version_info_min_setup_py_in
):
    return rpm_version_info >= rpm_version_info_min_setup_py_in


@pytest.fixture
def is_dnf():
    return _is_dnf


@pytest.fixture
def pkg_cmd(is_dnf):
    return 'dnf' if is_dnf else 'yum'


@pytest.fixture
def file_url():
    url = (
        'https://raw.githubusercontent.com/junaruga/rpm-py-installer'
        '/master/README.md'
    )
    return url


@pytest.fixture
def archive_file_path_dicts():
    archive_dir = os.path.abspath('tests/fixtures/archive')

    path_dicts = {
        'tar.gz': {
            'valid': os.path.join(archive_dir, 'valid.tar.gz'),
            'invalid': os.path.join(archive_dir, 'invalid.tar.gz'),
         },
        'tar.bz2': {
            'valid': os.path.join(archive_dir, 'valid.tar.bz2'),
            'invalid': os.path.join(archive_dir, 'invalid.tar.bz2'),
        },
    }
    return path_dicts


@pytest.fixture
def rpm_files():
    rpm_dir = 'tests/fixtures/rpm'

    def add_abs_rpm_dir(file_name):
        return os.path.abspath(os.path.join(rpm_dir, file_name))

    files = list(map(add_abs_rpm_dir, os.listdir(rpm_dir)))

    return files


@pytest.fixture
def setup_py_path():
    return os.path.abspath('tests/fixtures/setup.py.in')


@pytest.helpers.register
def is_root_user():
    return running_user == 'root'


@pytest.helpers.register
def helper_is_debian():
    """Return if it is Debian base Linux. """
    # TODO: This method is duplicated with fixture: is_debian.
    return _is_debian


@pytest.helpers.register
@contextmanager
def reset_dir():
    current_dir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(current_dir)


@pytest.helpers.register
@contextmanager
def work_dir():
    with reset_dir():
        tmp_dir = tempfile.mkdtemp(suffix='-rpm-py-installer-test')
        os.chdir(tmp_dir)
        try:
            yield
        finally:
            shutil.rmtree(tmp_dir)


def helper_setup_py_path():
    # TODO: This method is duplicated with fixture: is_debian.
    return os.path.abspath('tests/fixtures/setup.py.in')


@pytest.helpers.register
@contextmanager
def work_dir_with_setup_py():
    path = helper_setup_py_path()
    with work_dir():
        shutil.copy(path, '.')
        yield


@pytest.helpers.register
@contextmanager
def pushd(target_dir):
    current_dir = os.getcwd()
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(current_dir)


@pytest.helpers.register
def touch(file_path):
    f = None
    try:
        f = open(file_path, 'a')
    finally:
        f.close()


@pytest.helpers.register
def run_cmd(cmd):
    print('CMD: {0}'.format(cmd))
    exit_status = os.system(cmd)
    return (exit_status == 0)
