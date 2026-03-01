# sharkGameSQL

## What does this section do?
This section contains the entire backend logic behind some of the features the shark catch game has; the file creates a database that contains the list of the sharks that can be caught, as well as handling how coins and nets are managed.

## Imports needed:
1. `sqlite3`: This is to be able to use SQL with python and be able to use python to access all the necessary tables and data.
2. `json`: The json import is to be able to interact with json files, in this case it is used to take the shark data from the json file given.
3. `logging`: This is to be able to keep track of everything that is happening and keep them in a log file. Main use case is for tracking bugs when they happen and looking to see if certain actions are being processed and done properly
4. `datetime`: Datetime is used for the tables to be able to save and track the dates of when sharks are caught or when the nets table was updated.
5. `Enum`: The Enum class is not necessarily needed, but it does help make the code more readable.
