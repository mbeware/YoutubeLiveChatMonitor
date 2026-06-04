# YoutubeLiveChatMonitor

YTChatMon is a Python-based bot designed to monitor YouTube live chat messages in real-time. It provides a modular architecture that allows users to create custom modules for processing chat messages and executing commands. The bot also includes a security system with user groups and permissions to control access to commands.

Installation :

1. Clone the repository: git clone
2. Navigate to the project directory: `cd YoutubeLiveChatMonitor`
3. Install the required dependencies: `pip install -r requirements.txt --break-system-packages`
4. Install the required dependencies for the modules you want to use. Each module may have its own dependencies, so make sure to check the documentation for each module for the required dependencies and install them using pip.
5. create the config files: python YTChatMon.py --install
6. (optionnal) Edit the config files to add your modules and commands. The config files are located in the .config/YoutubeLiveChatMonitor folder in your home directory. The main config file is config.toml, and the BotCommand module config file is bot_command.toml. The permissions for the user groups are defined in the BotCommandACL.toml config file.
7. Run the bot: `python YTChatMon.py --streamid <STREAM_ID>`. Replace <STREAM_ID> with the ID of the YouTube stream you want to monitor. You can find the stream ID in the URL of the stream (the part after the =). For example, if the URL of the stream is https://www.youtube.com/watch?v=abc123, the stream ID is abc123.
8. The bot will start monitoring the live chat messages for the specified stream and execute the modules and commands as configured in the config files.

## loading modules

The config.toml in the .config/YoutubeLiveChatMonitor folder from the user's home directory contains the list of modules to load. The file_path field for each module will be used to load the module. Each module has to have a function called "process_message" that will be called for each message received from the live chat. The function should take a two arguments (message and context) and return nothing. The context argument is a dictionary that can be used to store any data that needs to be shared between modules. The context dictionary is passed to each module, so any changes made to the context in one module will be available in the next modules.

```toml
[general]
modules_list = ["module1", "module2"]
[module1]
file_path = "path/module1.py"
[module2]
file_path = "path/module2.py"
```

## BotCommand Module configuration

Name : bot_command.toml in the .config/YoutubeLiveChatMonitor folder in the user's home directory.
TOML format is used for the config file. The following fields are required:

```toml
[general]
#if an emoticon is used, you must use the :name: format for the emoticon. For example :smile:  
CommandPrefix = "!"
[commands]
[commands.command1]
name = "hello"
description = "This is a command that says hello."
function_path = "path/function_file.py"
function = "cmd_hello"
user_groups = ["user", "moderator", "admin"]
MaxUsagePerUserPerHour = 5
DelayBetweenUsageInSeconds = 10
enabled = true

[commands.command2]
name = "goodbye"
description = "This is a command that says goodbye."
function_path = "path/function_file.py"
function = "function_name"

user_groups = ["user", "moderator", "admin"]
```

the command name is the name of the command that will be used in the chat. For example, if the command prefix is "!" and the command name is "hello", the command will be triggered when a user types ```!hello``` in the chat.

function is the name of the function that will be called when the command is triggered. The function should take a single argument, which will be the message object.

4 groups of users are defined in the security system: owner, admin, moderator, and user. The owner has all permissions, the admin has permissions to manage the bot, the modules and the moderators, the moderator has permissions to manage the chat and the users, and the user has permissions to use some commands. The permissions for each group can be defined in the BotCommand config file with the user_groups field. The user_groups is a list of user groups that are allowed to use this command. The user groups are defined in the config file, and the permissions for each group can be defined in the config file as well. For example, if you want to allow only moderators and admins to use this command, you can set the user_groups field to ["moderator", "admin"]. If you want to allow all users to use this command, you can set the user_groups field to ["user", "moderator", "admin"]. Owners have all permissions, so they can use all commands regardless of the user_groups field.

MaxUsagePerUserPerHour is the maximum number of times a user can use this command in an hour. This is to prevent spamming of the command. If a user exceeds this limit, they will not be able to use the command until the hour is over.
DelayBetweenUsageInSeconds is the minimum delay between two usages of the command from any user. This is to prevent spamming of the command. If the command is invoked before the delay is over, the command will not be executed.
enabled is a boolean field that indicates whether the command is enabled or not. If the command is disabled, it will not be executed when triggered.

Predefined commands:

- AddUser : This command will add a user to the user group. The command should be used like this: ```<prefix>AddUser username```.  Moderators and admins can use this command
- RemoveUser : This command will remove a user from the user group. The command should be used like this: ```<prefix>RemoveUser username```.  Moderators and admins can use this command.
- AddMod : This command will add a user to the moderator group. The command should be used like this: ```<prefix>AddMod username```. Admins can use this command.
- RemoveMod : This command will remove a user from the moderator group. The command should be used like this: ```<prefix>RemoveMod username```. Admins can use this command.
- AddAdmin : This command will add a user to the admin group. The command should be used like this: ```<prefix>AddAdmin username```. Owners can use this command.
- RemoveAdmin : This command will remove a user from the admin group. The command should be used like this: ```<prefix>RemoveAdmin username```. Owners can use this command.
- enableCommand : This command will enable a command. The command should be used like this: ```<prefix>enableCommand command_name```. Admins can use this command. The change will not persist after the bot is restarted. The default state of the command (enabled or disabled) is determined by the enabled field in the config file.
- disableCommand : This command will disable a command. The command should be used like this: ```<prefix>disableCommand command_name```. Admins can use this command. The change will not persist after the bot is restarted. The default state of the command (enabled or disabled) is determined by the enabled field in the config file.
- ResetUsage : This command will reset the usage count for a user for a specific command. The command should be used like this: ```<prefix>ResetUsage username``` command_name. Admins and moderator can use this command.
  
The members for each groups are stored in the BotCommandACL.toml config file, so they will persist even after the bot is restarted. The groups members are stored in the config file in the following format:

```toml
[groups]
[groups.owner]
members = ["owner_username"]
[groups.admin]
members = ["admin_username1", "admin_username2"]
[groups.moderator]
members = ["moderator_username1", "moderator_username2"]
[groups.user]
members = ["user_username1", "user_username2"]
```

To check is the message sender is in the allowed user groups for a command, you can use the following code in the function that handles the command:

```python
# check if function is already imported, if not import it  
if 'check_user_permission' not in dir():
    from BotCommand import check_user_permission    
def cmd_hello(message):
    if not check_user_permission(message, "command1"):
        return
    # your command code here
    
```

## TTSbot

The TTSbot module is a text-to-speech bot that speak the youtube live chat comment for the users who you have added the permission. Users can select the voice and other parameter for the voice, using the command prefix 🤖💬. any voice in the EDGE_TTS library can be used. The selection for the user is save in a configuration file (TTSBOT_USERCONFIG.toml).  The module can be configured in the config.toml file to set the default voice for the text-to-speech conversion and the prefix for the TTS to speak the message (default 💬). 

Commands for the TTSbot module:

- setVoice : This command will set the voice for the user. The command should be used like this: ```<prefix>setVoice voice_name```. The voice_name is the name of the voice in the EDGE_TTS library. For example, if you want to use the "en-US-JennyNeural" voice, you can set the voice_name to "en-US-JennyNeural". Users can use this command to select their preferred voice for the text-to-speech conversion. Available voices can be found here : [https://gist.github.com/BettyJJ/17cbaa1de96235a7f5773b8690a20462](https://gist.github.com/BettyJJ/17cbaa1de96235a7f5773b8690a20462) 
  
- setPitch : This command will set the pitch for the user's voice. The command should be used like this: ```<prefix>setPitch pitch_value```. The pitch_value is percentage (negative or positive). A value of 0 represents the default pitch. Users can use this command to adjust the pitch of their selected voice for the text-to-speech conversion.

- setRate : This command will set the rate for the user's voice. The command should be used like this: ```<prefix>setRate rate_value```. The rate_value is a percentage that represents the rate of the voice. A value of 0 represents the default rate. Users can use this command to adjust the rate of their selected voice for the text-to-speech conversion.

- setVolume : This command will set the volume for a user voice. Only the owner can change the value.  The command should be used like this: ```<prefix>setVolume username volume_value```. The volume_value is a percentage that represents the volume of the voice. A value of 0 represents the default volume. The owner can use this command to adjust the volume of a user's voice for the text-to-speech conversion.

##### LLM usage disclosure

The code for this project has been handwritten by me (and normal auto-complete). The README file was created with some help from LLM autocomplete feature of VSCode (copilot and local LLM) and chatGPT. The LLM was used to generate the initial content of the README file, and then the content was edited and modified by me to fit the project. The LLM was also used to generate some of the code snippets in the README file, but all the code snippets were reviewed and modified by me to ensure they are correct and relevant to the project.
