# Copyright (c) 2016 Gemini Lasswell
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Handler for Messages Application
# to communicate new messages to Indigo Server Messages plugin
#
using terms from application "Messages"
	
	on message received theMessage from theBuddy for theChat
		set quoted_message to quoted_form_for_python(theMessage)
		set quoted_handle to quoted_form_for_python(handle of theBuddy as string)
		
		set theService to service of theBuddy
		set quoted_service to quoted_form_for_python(name of theService as string)
		set quoted_service_type to quoted_form_for_python(service type of theService as string)
		
		# if you modify this script, remember that quoted_form_for_python is using double quotes		
		set python_script to "
messageID = \"me.gazally.indigoplugin.Messages\"
messagePlugin = indigo.server.getPlugin(messageID)
if messagePlugin.isEnabled():
	messagePlugin.executeAction(\"receiveMessage\", props={\"message\": " & quoted_message & ", \"handle\":" & quoted_handle & ", \"service\":" & quoted_service & ", \"service_type\":" & quoted_service_type & "} )
"
		# newlines in the above quoted text ARE significant
		
		set indigo_plugin_host to quoted form of "/Library/Application Support/Perceptive Automation/Indigo 6/IndigoPluginHost.app/Contents/MacOS/IndigoPluginHost"
		set shell_safe_script to quoted form of python_script
		
		do shell script indigo_plugin_host & " -e " & shell_safe_script & "> /dev/null 2>&1 &"
	end message received
	
	# Look through a string and do these things:
	#  - delete backslashes because they make life difficult and I don't need them
	#  - add backslashes before single and double quotes
	#  - change newlines to \n
	# Then add double quotes to the beginning and end
	on quoted_form_for_python(s)
		set needs_backslashing to "'\""
		set newline to "
"
		set get_rid_of to "\\"
		
		set character_list to every character of s
		repeat with i from 1 to the count of characters of s
			set ch to item i of character_list
			if (offset of ch in needs_backslashing) is not 0 then
				set item i of character_list to "\\" & ch
			end if
			if (offset of ch in get_rid_of) is not 0 then
				set item i of character_list to ""
			end if
			if ch is newline then
				set item i of character_list to "\\n"
			end if
		end repeat
		return "\"" & (character_list as string) & "\""
	end quoted_form_for_python
	
	# Accept text chats but deny everything else
	
	on received text invitation theText from theBuddy for theChat
		accept theChat
	end received text invitation
	
	on buddy authorization requested theRequest
		accept theRequest
	end buddy authorization requested
	
	on received audio invitation theText from theBuddy for theChat
		decline theChat
	end received audio invitation
	
	on received video invitation theText from theBuddy for theChat
		decline theChat
	end received video invitation
	
	on received file transfer invitation theFileTransfer
		decline theFileTransfer
	end received file transfer invitation
	
	# The following are unused but need to be defined to avoid an error
	
	on message sent theMessage for theChat
		
	end message sent
	
	on chat room message received theMessage from theBuddy for theChat
		
	end chat room message received
	
	on active chat message received theMessage
		# If you're puzzling over why Indigo isn't informed about messages received while Messages is the foreground application,
		# it's because I didn't put anything here. However, the reason I didn't put anything here is because Messages (at least in OS X 10.11)
		# has a bug which causes it to call this handler twice per message, and I couldn't figure out a good way to make my Indigo 
		# plugin cope with that gracefully.		
	end active chat message received
	
	on addressed chat room message received theMessage from theBuddy for theChat
		
	end addressed chat room message received
	
	on addressed message received theMessage from theBuddy for theChat
		
	end addressed message received
	
	on av chat started
		
	end av chat started
	
	on av chat ended
		
	end av chat ended
	
	on login finished for theService
		
	end login finished
	
	on logout finished for theService
		
	end logout finished
	
	on buddy became available theBuddy
		
	end buddy became available
	
	on buddy became unavailable theBuddy
		
	end buddy became unavailable
	
	on completed file transfer
		
	end completed file transfer
	
end using terms from
