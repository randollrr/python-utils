# Utils

Utils is intended to be a swiss-army-knife toolbox that houses boilerplate codes for many apps or scripts. A generic API to access:
* databases,
* config files,
* logs,
* email servers for notifications,
* simple encryption, etc...


### Default parameters
```yaml
system:
  app-name: cox-papa-wae-design-simulation
directories:
  app-log: /var/log
logging:
  log-level: INFO
```

### Optional (but implemented defaults)
```yaml
database: (mysql or oracle)
  host: my_server
  user: root
  password: my_password
  schema: my_schema
sendmail:
  path: /usr/sbin/sendmail
  from: no-reply@cox.com
  stake_holders: Randoll.Revers@cox.com
```
