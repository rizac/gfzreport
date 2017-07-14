Deployment on Apache
====================

These guidelines help the installation of the software on an apache server

1. Install the package according to the documentation: https://github.com/rizac/gfzreport/blob/master/README.md

Now you should have a directory where the virtual environment is installed, we call it `$PYENV` and the directory the reportgen has been cloned, we call it `$GFZREPORT` (note that `$GFZREPORT` has been installed into $PYENV packages, but it needs not to be therein)

2. Copy example.wsgi in the gfzreport folder into where you want your wsgi to be executed (e.g., into /var/www/html/gfzreport):
```$ cp $GFZREPORT/example.wsgi /var/www/html/gfzreport/whateverIwant.wsgi```

3. Edit the file by setting `$PYENV` and the environment variable `os.environ['DATA_PATH']` which is the path where the source and build folders have to be found. Remember that `os.environ['DATA_PATH']` should contain a 'source' subfolder
which conforms to the sphinx build command (called internally from within the web interface). FIXME: check this and setup guidelines for the source folder structure!

4. Create the configurations for apache. You can also copy `$GFZREPORT/example.apache.conf`:
```$ cp $GFZREPORT/example.apache.conf /etc/apache2/conf-available/whateverIwant.conf```

5. Edit the file. Specifically, **set which URL address the given wsgi we created above should point to**. FIXME: the file seems to work on our apache server. However, it is slightly different than the one provided here: http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/. Nice would be to investigate if the one provided in the link works, and in case why not

6. Make ls:
```
$ /etc/apache2/conf-available$ cd ../conf-enabled
$ /etc/apache2/conf-enabled$ sudo ln -s ../conf-available/whateverIwant.conf whateverIwant.conf
```

7. (Optional) Repeat steps 2-6 for any report type you want

8. restart apache2 (needs sudo privileges)
```$ sudo service apache2 restart```

9. (Optional, but better doing it) check apache error.log. If the next (final) step fails, it shows up relevant infos:
```$ tail -f /var/log/apache2/error.log```

# and try navigating to the address you specified in /etc/apache2/conf-available/whateverIwant.conf
