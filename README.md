####  DESCRIPTION

Create automated FE tests for given list of URLs. Check for JS errors and make screenshot comparsion


#### Installation


##### Ubuntu
```
    sudo apt-get install libxss1 libappindicator1 libindicator7 unzip xvfb python-pip imagemagick
```
```
    wget -N http://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip
    unzip chromedriver_linux64.zip
    chmod +x chromedriver
    sudo mv -f chromedriver /usr/local/share/chromedriver
    sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
    sudo ln -s /usr/local/share/chromedriver /usr/bin/chromedriver
```
```
    pip install pyvirtualdisplay selenium
```
