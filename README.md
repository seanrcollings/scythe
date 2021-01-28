# Scythe

## TODO:
### IMPROVEMENTS:

- List First by project then by task, rather than all at onc
- If there is no cached entry_id, fetch the running timer
- Need to properly validate input when starting a timer
- Add some more methods to the HarvestApi to streamline some of the api calls

### ADDITIONS:
- Swap from user input for most things to a urwid menu
    - Or some form of selectable menu?
- Create Assignments, Task, Project classes to abstract away some of the long winded dict accesses
- Give `timer:start` a `--restart` flag to restart the most recently stopped timer
