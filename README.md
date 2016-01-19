## indigo-messages
An Indigo Domotics plugin to enable Indigo to send and receive messages with the OS X Messages app.

In addition to iMessages, this also enables Indigo to communicate with the other services available in Messages, which are Yahoo Messenger, Google Talk/Hangouts, AOL Messaging/AIM and Jabber.

This plugin is a work in progress. The only configuration I've tried it on is OS X El Capitan and Indigo 6.1.4, using iMessages and Google Talk. Please only use it if you don't mind using beta software.

### Installation instructions

[Download the (zip archive of the) plugin here](https://github.com/gazally/indigo-messages/archive/master.zip)

[Follow the plugin installation instructions](http://wiki.indigodomo.com/doku.php?id=indigo_6_documentation:getting_started#installing_plugins_and_configuring_plugin_settings_pro_only_feature)

###Installing the Messages.app handler AppleScript

In order to receive messages from the Messages application, go to Preferences on the Messages menu, choose the General tab, and change the value of "AppleScript handler" to "Open Scripts Folder". Look where you unpacked the .zip file earlier, and you will find an .applescript file. Copy it into the scripts folder, then close and re-open Messages Preferences, and select the Run Indigo Message Plugin Action in the AppleScript handler list. Due to a bug in Messages, new messages will not always reach Indigo if Messages is in the foreground, so put an Indigo window in front of it.

###Create devices for each person you want to talk to

From the Indigo main window, choose Devices and then New...  On the Device Type list, choose Messages, and on the Device Model list, choose Messages App Device. Then Edit Device Settings...

Device configuration gives you two choices. The default is to connect the device to one specific person. In that case, there are two lists in the configuration dialog. The top one lets you choose the message service to use, which is the same as the list of accounts in Messages Preferences. Once you have chosen something there, the second list will fill up with all the people Messages knows how to talk to on that service. On some message services, Messages.app puts confusing and unhelpful things in its list of available chat contacts. If you're having trouble figuring out what to select here, try starting a conversation with the person, turning on debug output using Toggle Debugging on the Plugin menu under Messages, and then when a message arrives from that person, their message service and ID or login will appear in the Indigo Log window. If you don't see anything in the Indigo Log when a message arrives, either the Applescript handler isn't installed correctly (see above) or debug logging isn't on (try toggling it from the menu).

If you choose "Send and Receive messages from all senders" the two lists go away, because the device will now react to messages from anyone who you haven't set up a specific device for.

###Receiving Messages

Once you have a device set up, when Messages gets a message from that person, the device state will change to "New" and the message will be available in the device state, which you can see by scrolling the bottom of the Indigo home window when the device is selected. If more messages arrive before the first one is read (see below) they won't replace the current one, but will be saved up until it is read.

###Actions

This plugin defines three Actions in Indigo. The first, "Receive a message from the Messages app" is used by the Applescript handler, and won't do anything if you try to use it with the Indigo UI. Although it would be easy to write a Python script that makes the plugin think it's received a message from Messages, if you want to do that.

The second action is "Mark current message as Read, and allow the next one to be fetched." Once you have done something with a message, use this action and it will set the state of the device to Read. However, if one or more messages has arrived and is waiting, it will also immediately set the state of the device back to New, with the next new message.

The last action is "Send Message using the Messages app." Choose a Messages Plugin device for the person to send it to, and set the message in Edit Action Settings. If you set the device to react to all senders when you configured it, then you also get fields where you can enter any service and any login/phone number/handle available to Messages. There is a button which sets those fields up, using Indigo device substitution syntax, to send a message back to the person who last sent a message caught by this device. Please note that it is only safe to use this feature before you mark the message as Read. After you mark it read, another message could arrive at any time, changing the person you are sending the message to to someone you don't expect.

###Menu Items

Toggle Debugging

This works like any other plugin in Indigo. It toggles debugging output on and off. Use it with care, especially since it will cause every message received by Messages.app to be written to your Indigo log.

###Examples

Once you have a device set up and receiving messages, it's easy to make a trigger that automatically replies. First, look at the device and copy its device ID. Then create a new trigger, set its type to "Device State Changed", select your device and below that change the fields to "Status", "Becomes Equal to" and "New". Then select the Actions tab and choose "Send Message using the Messages App" from the Messages Actions list. Choose the same device, and then open Edit Action Settings. In there type "Thanks for the message! Here's what you sent me: %%d:0000000:message%%" except replace the 0000000 with the numeric ID of the device. Press Save, and then at the bottom of the Edit Trigger dialog find Add New. Select "Mark current message as Read" from the Messages Actions list, choose the same device, and press OK. If the device state was already at New the trigger won't start automatically, because it is waiting for it to become New. But you can press Execute Actions Now in the bottom corner of Indigo's home window to get it started.
