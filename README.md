# Scythe
Harvests are always better with a good tool!

Scythe is a tool for interacting with the Harvest API


# Installation
The package is available on PyPi
```
$ pip install scythe-cli
```

# Scripts
`scythe help` - Displays all the help information for the CLI

`scythe init` - Used to initialize the tool with the Harvest token and Account ID. The auth token can be generated [here](https://id.getharvest.com/developers). Check [here](https://help.getharvest.com/api-v2/authentication-api/authentication/authentication/) for more information.

`scythe whoami` - Prints the Harvest user's information

`scythe project:list` - Lists out all the projects that the user is in

`scythe timer:create` - Presents an interface to create a timer based on project and task. Will automatically start the timer upon creation.

`scythe timer:start` - Used to start / restart a previously created timer.

`scythe timer:running` - Display the currently running timer

`scythe timer:stop` - Will stop the currenlty running timer

`scythe timer:delete` - Presents an interface to delete a timer from today

`scythe cache` - prints out the contents of the cache

`scythe cache:clear` - cleans out the cache

`sycthe cache:delete KEY` - deletes the `KEY` from the cache

## Atomic Jolt
Scythe comes with a namespace `atomic` for Atomic Jolt specific timers.

`scythe atomic:standup` - Starts the timer for standup

`scythe atomic:training` - Stats the timer for training

Both of these scripts also accept a `--launch` flag. This will open the link named `STANDUP_LINK` or `TRAINING_LINK` in the config if they exist.


# Development
This project uses [Poetry](https://python-poetry.org/) for dependancy / build management
```
$ git clone https://github.com/seanrcollings/scythe
$ cd scythe
$ poetry install
```

# TODO
- Implement a `stats` utility
  - Show time spent per project
  - Show time spent per project task
- Add the ability to update a timer
- Update the config file to use yaml
