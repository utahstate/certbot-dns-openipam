# certbot-dns-openipam

For this to work you have to follow the Certbot install instructions and install with pip rather than your OS package manager.

https://certbot.eff.org/instructions?ws=nginx&os=pip&tab=wildcard

And then install this plugin with pip:

```
 pip install git+ssh://git@github.com/utahstate/certbot-dns-openipam#egg=certbot-dns-openipam
```

You'll need an openipam api key saved in an openipam.ini file.

Run the plugin like this:

certbot certonly --authenticator dns-openipam --dns-openipam-credentials=secrets/openipam.ini --dns-openipam-propagation-seconds=180 -d example.usu.edu
