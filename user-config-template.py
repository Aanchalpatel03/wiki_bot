# Pywikibot User Configuration Template
# Copy this file to user-config.py and customize for your bot account

# This is a sample user-config.py file for Wikimedia Commons bot
# For full documentation, see: https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py

# The family of sites we want to edit
family = 'commons'

# The language code of the site we want to edit
mylang = 'commons'

# The dictionary usernames should contain a username for each site where you
# have a bot account. Please set your own username.
usernames = {}
usernames['commons'] = {'commons': 'YourBotName'}

# Alternatively, you can use:
# usernames['commons'] = {'commons': 'YourBotName'}

# BotPasswords is recommended over main account password
# Create a bot password at: https://commons.wikimedia.org/wiki/Special:BotPasswords
# Then uncomment and fill in:
# password_file = "user-password.py"

# The default edit summary for this bot
# default_edit_summary = 'Bot: Automated template replacement'

# Simulate and ask for confirmation before actually writing to the server?
# Useful for testing. Set to False for production runs.
simulate = True

# Should the bot ask for confirmation before making changes?
# For production runs with approved bots, set to False
put_throttle = 5  # Minimum seconds to wait between saves

# Maximum number of retries for failed page saves
max_retries = 3

# Socket timeout (in seconds)
socket_timeout = 60

# Enable mwparserfromhell for better template parsing
use_mwparserfromhell = True

# Logging
log = ['*']  # Log everything
logfilename = 'pywikibot.log'

# Console output encoding
console_encoding = 'utf-8'

# Other useful settings:
# Enable cosmetic changes (minor formatting fixes)
cosmetic_changes = False

# Maximum number of pages loaded simultaneously
max_external_links = 50

# Colorize output (for terminal with color support)
colorized_output = True
