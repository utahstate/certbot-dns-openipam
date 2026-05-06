# certbot-dns-openipam

For this to work you have to follow the Certbot install instructions and install with pip rather than your OS package manager.

https://certbot.eff.org/instructions?ws=nginx&os=pip&tab=wildcard

And then install this plugin with pip:

```
 /opt/certbot/bin/pip install git+https://git@github.com/utahstate/certbot-dns-openipam#egg=certbot-dns-openipam
```

You'll need an openipam api key saved in an openipam.ini file.

```
dns_openipam_api_token=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Run the plugin like this:

```
certbot certonly --authenticator dns-openipam --dns-openipam-credentials=secrets/openipam.ini --dns-openipam-propagation-seconds=180 -d example.usu.edu
```
For multiple domain names, just append additional -d parameters.
```
certbot certonly --authenticator dns-openipam --dns-openipam-credentials=secrets/openipam.ini --dns-openipam-propagation-seconds=180 -d example.usu.edu -d example2.usu.edu -d example3.usu.edu
```
Make sure to schedule a cron job to do the certificate renewals.  Installing certbot with pip does not install a cron or a systemd timer.
```
echo "0 0,12 * * * root /opt/certbot/bin/python -c 'import random; import time; time.sleep(random.random() * 3600)' && sudo certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
```
