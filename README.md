# ShowMySlskD

ShowMySlskD is a Python-based tool designed to analyze and visualize file transfers from an SQLite database used by Soulseek (specifically the transfers.db file). It allows users to track the number of files and total data downloaded by each user, visualize the most downloaded artists, and identify users with high error or cancellation rates, etc.  

I wanted to move the data into a different database, because sometimes I just nuke the whole slskd/data directory.  It's the laziest way to get everything more responsive again.   I know all the retention tweaks in the config, but sometimes it still just needs a clean slate.

I don't claim to be a python programmer, but this seems to work for my purposes.   If you know better than me, and want to submit changes, I'm open to PRs.  That would include changes to this document, since writing documentation is one of my long-standing weaknesses.  Design choices like using PySide were made without much thought or research.

Finally, I'll mention that ChatGPT did write most of the initial code, based on requirements and feedback from me, helping me gt up and running quickly.   It's pretty awesome we can do that now...but it's honestly almost as much work telling ChatGPT what bonehead mistakes it has made as just learning the proper coding from scratch.   Debugging ChatGPT code is like debugging code written by a brand new Valedictorian Computer Science graduate who drinks on the job.   So we aren't about to be replaced as programmers too soon.

## Features

- **Import Data from slskd:**
  - Select input and output database paths.
  - Stores paths in `~/.local/share/showmyslskd/config.json`.
  - If paths exist, it automatically uses them and prints:
  - Option to **overwrite the output database** instead of appending new data.

- **Query and Filter Data:**
  - Top 10 users by **files downloaded**.
  - Top 10 users by **data downloaded (MB)**.
  - **Most downloaded artists**, globally or per user.
  - Users with the **most errors**.
  - Users with the **most canceled transfers**.
  - **Date range filtering** (All Time, Last 24 Hours, Last 7 Days, Last 30 Days).

- **Search and Autocomplete:**
  - Dropdown supports **manual entry with autocomplete**.
  - Allows filtering by **username or artist**.

- **Data Visualization:**
  - Bar charts for available
  - Uses Matplotlib for **data visualization**.

## Installation

### Prerequisites

Ensure you have Python 3.8+ installed.

### Clone the Repository
```
git clone https://github.com/yourusername/showmyslskd.git
cd showmyslskd
```
### Install Dependencies
This can either be done installing globally, or in a virtual env

#### Installing Globally
This will vary depending on your platform.   On Ubuntu:
```
sudo apt install python3-pyside2.qtcore python3-pyside2.qtwidgets python3-pyside2.qtgui python3-matplotlib
```

Other platforms/distros will vary.  Use your Google-Fu

#### Set up a Virtual Environment
The python world seems to prefer running everything in virtual environments.  I can see the value, it's just
a little cumbersome at times IMHO.   But here's the process.   In your showmyslskd directory:
```
python -m venv venv
source venv/bin/activate
# On Windows use 'venv\Scripts\activate' I think
```
Your prompt should now have a (venv) at the front to show you're in a virtual environment.
Verify that with:
```
which python
{your root directory}/venv/bin/python  ### This should be the local one, not a system one
```

##### Install Dependencies
```
pip install -r requirments.txt
```

## Usage
### Running the UI
```
python src/showmyslskd.py
```
### Importing Data

1. Click **"Import Data from slskd"**.
2. Select location of input and desired output databases.
3. If databases are already stored, it will automatically import.
4. Check **"Overwrite existing data"** if you want to blow away your db and start over (not the slskd db).
5. The import is cumulative, so it skips previously imported records

### Querying Data

1. Select a query type.
2. Choose a **date range**.
3. (Optional) Enter a username or artist for filtering.
4. Click **"Run Query"** to see results.
5. Click **"Show Chart"** to visualize the data.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Description of changes"`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## Screenshots
### Top 10 Users for a Specific Artist
![alt text](https://github.com/huckinfappy69/showmyslskd/blob/main/examples/Top10UsersByArtist.png?raw=true)

### Top 10 Users by Data Transfer
![alt text](https://github.com/huckinfappy69/showmyslskd/blob/main/examples/Top10UsersByMB.png?raw=true)

### Top 10 Artists for a Specific User
![alt text](https://github.com/huckinfappy69/showmyslskd/blob/main/examples/TopArtistsByUser.png?raw=true)

## License

This project is licensed under the MIT License.

## Acknowledgments

Special thanks to the Soulseek and slskd communities for inspiring this project.   
Keep on Sharing!
