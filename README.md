# Skeleton Django Project

## Installation

1.  Make, enter and activate a virtualenv:

        $ mkvirtualenv mysite -p python2.7 --no-site-packages
        New python executable in mysite/bin/python
        Installing setuptools............done.
        $ workon mysite

2.  Clone this repo into a sub-directory of the new virtualenv:

        $ git clone 'git://github.com/stephanpoetschner/django-skeleton-project.git' myproject
        $ cd myproject/

        # Remove .empty files, used to make Hg track otherwise-empty dirs.
        $ find . -name '.empty' -exec rm {} \;

        # edit or clear .gitignore
        $ vi .gitignore
        $ echo > .gitignore

3.  Remove the pointer to the GitHub project:

        $ git config --unset remote.origin.url

    Later you’ll probably want to re-add this configuration with a pointer to
    your upstream repo. You can do that with the following command:

        $ git config remote.origin.url 'git@github.com:USERNAME/PROJECT.git'

4.  Ensure current (working) version numbers are documented

    * `pip freeze > requirements/base.txt`

5.  Go through the following files, editing as necessary:

    *   `settings.py`
        * Update SECRET_KEY (call `./manage.py generate_secret_key`)
    *   `urls.py`
    *   `requirements/project.txt`

6.  Install the basic project requirements:

        $ easy_install pip
        $ pip install -r requirements/project.txt

    As you edit your `requirements/project.txt` file, you can run that last command again;
    `pip` will realise which packages you’ve added and will ignore those already
    installed.

7.  Commit changes

    * `git commit -a`


## Managing Your Site

    $ ./manage.py syncdb
    $ ./manage.py.py runserver
    $ ./manage.py test myapp


