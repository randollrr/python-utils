# python-utils

Python-Utils is intended to be a swiss-army-knife toolbox that houses boilerplate codes for many apps or scripts. A generic set of libs to access the following: `(inspired by my home-automation services)`
* databases,
* config files,
* logs,
* email servers for notifications,
* simple encryption, etc...
<br/><br/>

## Tools by lib:

- [common.utils](common_utils.md) : add support for log, config, etc...
- [common.mongo](common_mongo.md) : add basic MongoDB CRUD support to your script/app
- [common.fm](common_fm.md) : basic file management (file processing most common tasks)
<br/><br/>

### Default parameters:
`config.json`
```json
{
  "service": {
    "app-name": "app",
    "app-logs": "logs",
    "log-level": "DEBUG",
    "log-stdout": true,
    "base-url": "/",
    "security": null
  }
}
```

or

`config.yaml`
```yaml
service:
  app-name: app
  app-log: /var/log
  log-level: INFO
  log-stdout: true
```

### Optional (when email notification is necessary)
```yaml
sendmail:
  server: mta.sendmail.com
  port: null
  default-from: noreply@memail.com
  to:
    - you1@memail.com
    - you-two@example.com
    - you.three@somewhere.com
  subject: "sending emails"
  body: "This is an email..."
```
