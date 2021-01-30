# Scythe
Harvests are always better with a good tool!


# Installation
Clone this repo
```
$ git clone https://github.com/seanrcollings/scythe
```

Install with pip
```
$ pip install ./scythe
```

# Scripts
`scythe init` - Used to initialize the tool with the Harvest token and Account ID. The auth token can be generated [here](https://id.getharvest.com/developers). Check [here](https://help.getharvest.com/api-v2/authentication-api/authentication/authentication/) for more information.

`scythe whoami` - Prints the Harvest user's information

`scythe project:list` - Lists out all the projects that the user is in

`scythe timer:create` - Presents an interface to create a timer based on project and task. Will automatically start the timer upon creation.

`scythe timer:start/restart` - Used to start / restart a previously created timer.

`scythe timer:running` - Display the currently running timer

`scythe timer:stop` - Will stop the currenlty running timer

`scythe timer:delete` - Presents an interface to delete a timer from today


# TODO
- Spice up the design of `timer:running` with a big ASCII clock
- Implement a `stats` utility
  - Show time spent per project
  - Show time spent per project task
- Add the ability to update a timer
