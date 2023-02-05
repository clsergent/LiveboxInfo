# LiveboxInfo

## Overview
Get Orange Livebox information from commandline, such as ip, link status, and more.

Run `python3 liveboxinfo.py --help` to get a short help.

Livebox credentials must be provided, either from the `credentials` file or using `--credentials` argument, as a tuple `(<login>,<password>)` or a mapping `{login:<login>, password:<password>}`.

If you encounter any bug , please open an issue.

## Dependencies
Python 3.10 or higher is required.
The script also relies on the [requests](https://pypi.org/project/requests/) library. Run `pip install requests` to install it.

## License
This repository and its content are licensed under the EUPL-1.2-or-later.

## Credits
Requests scheme are based on work published on [forum-orange.com](https://www.forum-orange.com/viewtopic.php?pid=758919) by *shdf*.

Orange and Livebox are Orange trademarks.
