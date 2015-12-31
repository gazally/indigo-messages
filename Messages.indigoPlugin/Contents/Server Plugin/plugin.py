#! /usr/bin/env python
# Copyright (c) 2016 Gemini Lasswell
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Messages App plugin for IndigoServer"""

import appscript
import indigo

#todo - indigo.device has a setErrorStateOnServer method. Maybe I should
#       be using it
#todo - is it possible to programatically start a new conversation?
#todo - message handler, received text invitation, will that fix
#       first message problem?
# todo - catchall device for messages? or event?

class Plugin(indigo.PluginBase):
    """Messages App plugin class for IndigoServer"""

    ##### plugin framework ######
    def __init__(self, plugin_id, display_name, version, prefs):
        indigo.PluginBase.__init__(self, plugin_id, display_name,
                                   version, prefs)
        self.debug = True
        self.debugLog(u"showDebugInfo" + unicode(prefs.get("showDebugInfo", False)))
        self.debug = prefs.get("showDebugInfo", False)
        self.device_info = {}

        try:
            self._init_messages_app()
        except Exception, e:
            self.debugLog("Error talking to Messages:\n" + unicode(e))
            self.errorLog("The Messages App doesn't seem to be installed "
                          "on your system.")

    def __del__(self):
        indigo.PluginBase.__del__(self)

    def startup(self):
        pass
        
    def shutdown(self):
        pass

    def update(self):
        pass
       
    def runConcurrentThread(self):
        try:
            while True:
                self.update()
                self.sleep(3600) # seconds
        except self.StopThread:
             pass

    ###### Preferences UI ######

    def validatePrefsConfigUi(self, values):
        """called by the Indigo UI to validate the values dictionary for the
        Plugin Preferences user interface dialog

        """
        self.debugLog("Preferences Validation called")
        debug = values.get("showDebugInfo", False)
        if self.debug:
            if not debug:
                self.debugLog("Turning off debug logging")
        self.debug = debug
        self.debugLog("Debug logging is on") #won't print if self.debug is False
            
        return(True, values)

    ##### Action Configuration UI ######

    def validateActionConfigUi(self, values, type_id, device_id):
        """called by the Indigo UI to validate the values dictionary for the
        Action user interface dialog

        """
        self.debugLog("Action Validation called for " + type_id)
        errors = indigo.Dict()
        if type_id == "sendMessage":
            if "message" not in values or not values["message"]:
                errors["message"] = "Can't send an empty message."
                errors["showAlertText"] = "Please type a message to send."

        if errors:
            return (False, values, errors)
        else:
            return (True, values)

    ###### Device Configuration UI #####

    def validateDeviceConfigUi(self, values, type_id, device_id):
        """ called by the Indigo UI to validate the values dictionary for
        the Device user interface dialog. Since all the user can do is 
        select from lists created by the plugin, don't need to do anything 
        here.
        """
        self.debugLog("Device Validation called")
        return (True, values)

    def serviceGenerator(self, filter_by="", values=None, type_id="",
                         target_id=0):
        """Called by the Indigo UI to generate a list for the Message 
        Services dynamic list in the Device Configuration dialog.
        
        The Messages App can identify the message service by name,
        which is a string it constructs from the handle used to login
        to the message service. For example "E:email@icloud.com".
        "iMessage (E:email@icloud.com)" is a less confusing thing to
        show the user, but still uniquely identifies the service in
        the event of two accounts on the same service set up in
        Messages.

        If a pre-existing device is brought up in the Configuration 
        dialog, it may reference a message service that no longer exists
        in Messages. Put that in the list too, labeled as Unavailable.
        
        Returns a list of tuples, the first element of each is the service
        name and the second the display strings.

        """

        try:
            services = self._services_in_messages_app()
        except Exception, e:
            services = {}
            self.debugLog("Error getting list of services from Messages: " + 
                          unicode(e))
        return self._build_display_strings(values, "service", services)

    def buddyGenerator(self, filter_by="", values=None, type_id="",
                       target_id=0):
        """ Called by the Indigo UI to generate a list for the Contact handle
        dynamic list in the Device Configuration dialog.
        
        If a pre-existing device is brought up in the Configuration dialog,
        it may reference a buddy who no longer exists. That buddy will
        be in the list too, labeled as Unavailable.
        
        Returns a list of tuples, the first element of each is the handle
        and the second the person's name with the handle in parens, for
        example: "Fred Flintstone (fred@bedrock.com).

        This works great for iMessage and for people in your contacts list,
        but for Jabber conversations the buddy name is something like
        gibberish@id.talk.google.com.
        """
        try:
            service = None
            buddies = {}
            services = self._services_in_messages_app()
            if values is not None and "service" in values:
                service = values["service"]
            if service in services:
                buddies = self._buddies_on_service(service)
        except Exception, e:
            buddies = {}
            self.debugLog("Error getting list of buddies on service "
                          "from Messages: " + unicode(e))
        return self._build_display_strings(values, "handle", buddies)
    
    def _build_display_strings(self, values, tag, results):
        """ 
        Given a list of services or buddies in dictionary form, return a list
        of tuples with keys and display strings for the Indigo UI dialog,
        sorted by display string. If values[tag] is not in the list of results,
        add it.
        """
        tuples =  [(h, u"{0} ({1})".format(n, h)) for h, n in results.items()]

        if (values is not None and tag in values and values[tag]
            and values[tag] not in results.keys()):
            tup = (values[tag],
                   u"Unavailable ({0})".format(values[tag]))
            tuples.append(tup)

        return sorted(tuples, key=lambda tup: tup[1])

    def servicePopupChanged(self, values, type_id, device_id):
        """Called by the Indigo UI when the user selects something in the
        list of message services. This doesn't do anything, but if it's not
        here, buddyGenerator won't get called when the selected service is
        changed.

        """
        return values

    ###### Menu Items ######
    
    def toggleDebugging(self):
        """ Called by the Indigo UI for the Toggle Debugging menu item.
        """
	if self.debug:
            self.debugLog("Turning off debug logging")
	else:
            self.debugLog("Turning on debug logging")
	self.debug = not self.debug
        self.pluginPrefs["showDebugInfo"] = self.debug

    ##### Device Start and Stop methods  #####
 
    def deviceStartComm(self, device):
        """Called by Indigo Server to tell a device to start working.
        Validates the device by checking with the Messages App to see
        if the service is valid, and sets the device state
        accordingly.  Also maintains the list of devices used by
        receiveMessage.

        """
        props = device.pluginProps
        self.debugLog(u"Starting device: {0} "
                      u"for messages from: {1} "
                      u"on service {2}".format(device.id, props["handle"],
                                              props["service"]))
        self.device_info[device.id] = []

        try:
            status = "No Message"
            buddy = self._messages_app_buddy(props["handle"],
                                            props["service"])
            name = self._name_of_buddy(buddy)
        except Exception, e:
            self.debugLog("Error talking to Messages: " + unicode(e))
            self.errorLog(u'Device {0} cannot be started because '
                          u'Messages App does not recognize "{1}" '
                          u'as a valid handle on "{2}". '.format(
                              device.id, props["handle"], props["service"]))
            status = "Error"
            name = ""

        device.updateStateOnServer(key="message", value="")
        device.updateStateOnServer(key="status", value=status)
        device.updateStateOnServer(key="response", value="")
        device.updateStateOnServer(key="responseStatus", value=status)
        device.updateStateOnServer(key="name", value=name)
           
    def deviceStopComm(self, device):
        """ Called by Indigo Server to tell us it's done with a device.
        Maintains the list of devices used by receiveMessage.
        """
        self.debugLog(u"Stopping device: {0}".format(device.id))
        self.device_info.pop(device.id, None)
 

    ###### Action Callbacks ######

    def receiveMessage(self, action):
        """ Called by Indigo Server to implement receiveMessage action
        in Actions.xml, which is the action that the Messages App handler
        uses to pass messages to Indigo.

        action.props should contain the following keys:
            'message', 'handle', 'service', 'service_type'
            'service' needs to be the service name used by Messages.
            'service_type' is only used to make the log message more
            comprehensible.

        receiveMessage works by searching the plugin's list of devices
        for ones that match the handle and service of the sender. If such a 
        device already has an unread message the message will be added
        to the device's backlog list, which is the list of strings
        in self.device_info. If no matching device is found,
        the message will be ignored.
        """
        if ("message" not in action.props
            or "handle" not in action.props
            or "service" not in action.props):
            self.debugLog("receiveMessage called without message, "
                            "handle or service_name")
            return
        
        message = action.props["message"]
        handle = action.props["handle"]
        service_name = action.props["service"]
        service_type = action.props.get("service_type", "")

        self.debugLog(u'Received Message: "{0}" '
                      u'From handle: {1}  '
                      u'On service: {2} ({3})'.format(message, handle,
                                                   service_name, service_type))
        found_device = False
        for device_id in self.device_info.iterkeys():
            device = indigo.devices[device_id]
            props = device.pluginProps
            if (props["service"] == service_name and
                props["handle"] == handle):
                if device.states["status"] != "New":
                    device.updateStateOnServer(key="message", value=message)
                    device.updateStateOnServer(key="status", value="New")
                else:
                    self.device_info[device_id].append(message)
                found_device = True
        if not found_device:
            self.debugLog("No device has been set up for this sender. "
                          "Ignoring message.")

    def markAsRead(self, action):
        """Called by Indigo Server to implement markAsRead action in
        Actions.xml.  Uses only the deviceId of the action parameter.
        If the device has a backlog of messages, this will change the
        state to Read and then back to New with a message from the
        backlog.

        """
        device_id = action.deviceId
        if device_id not in indigo.devices:
            return
        device = indigo.devices[device_id]
        if device.states["status"] == "New":
            device.updateStateOnServer(key="status", value="Read")

        backlog = self.device_info.get(device_id, None)
        if backlog:
            message = backlog.pop(0)
            device.updateStateOnServer(key="message", value=message)
            device.updateStateOnServer(key="status", value="New")
                
                
    def sendMessage(self, action):
        """Called by Indigo Server to implement sendMessage action in
        Actions.xml.  

        action.props should contain the message with the key 'message' 
        action.deviceId is who to send the message to.

        The device's responseStatus state will be updated. This will
        catch exceptions thrown by Messages.app and log them, but at
        least in OS X 10.11, Messages.app does not throw exceptions
        when asked to send to an invalid handle. Instead it puts up a
        dialog. Leaving the code on this side of the scripting bridge
        with no idea anything went wrong.

        """
        if (action.deviceId not in indigo.devices or
            "message" not in action.props):
            return
        device = indigo.devices[action.deviceId]
        if ("handle" not in device.pluginProps or
            "service" not in device.pluginProps):
            return

        message = self.substitute(action.props["message"])
        handle = device.pluginProps["handle"]
        service = device.pluginProps["service"]

        device.updateStateOnServer(key="response", value=message)
        device.updateStateOnServer(key="responseStatus", value="Sending")
        try:
            self._send_using_messages_app(message, handle, service)
        except Exception, e:
            self.debugLog("Error talking to Messages:" +  unicode(e))
            self.errorLog(u"Message to {0} couldn't be sent".format(handle))
            device.updateStateOnServer(key="responseStatus", value="Error")
        else:
            device.updateStateOnServer(key="responseStatus", value="Sent")
            self.debugLog(u'Sent "{0}" to {1}.'.format(message, handle))


    ##### Dealing with Messages App #####

    def _init_messages_app(self):
        """ Use appscript to get a link to Messages.app. Puts the result in
        self.messages_app. Exceptions will be passed on to the caller.
        """
        self.messages_app = None
        self.messages_app = appscript.app("Messages") 

    def _messages_app_available(self):
        """ Returns a boolean, whether or not communication with Messages.app
        was successful on plugin startup.
        """
        return self.messages_app is not None

    def _service_available_in_messages(self, service):
        """ Given the name of a service, return True if it is recognized
        by and enabled in Messages.app, False otherwise.
        """
        try:
            return self.messages_app.services[service].enabled.get()
        except appscript.CommandError:
            return False

    def _buddy_exists_on_service(self, handle, service):
        """ Returns a boolean, True if both the handle and service
        are recognized by Messages.app. Messages will give you a buddy
        object for absolutely any random string you give it, so check
        the handle against the list of buddies on the service instead.
        """
        if not self._service_available_in_messages(service):
            return False
        try:
            handles = self.messages_app.services[service].buddies.handle.get()
            return handle in handles
        except appscript.CommandError:
            return False

    def _messages_app_buddy(self, handle, service):
        """ returns a Messages.app buddy object, given a message service
            name and the handle of a buddy on that service.
        """
        return self.messages_app.services[service].buddies[handle].get()

    def _name_of_buddy(self, buddy):
        """ Ask Messages.app for the name of a buddy. Pass a buddy object
        from Messages.app.
            
        Messages.app will return the handle of the buddy if it doesn't 
        have the full name of the buddy (which I think it asks Contacts.app
        for). It does do nicer formatting of phone numbers.
        """
        return buddy.full_name.get()

    def _send_using_messages_app(self, message, handle, service):
        """ Ask Messages.app to send a message, given the name of one of
            its message services and the handle of a buddy on that service.
        """
        buddy = self._messages_app_buddy(handle, service)
        self.messages_app.send(message, to=buddy)

    def _services_in_messages_app(self):
        """ Ask Messages.app for a list of all message services.
        Filter out the ones that are not currently enabled.
        Returns a dictionary where key, value is the name of the 
        service and the type of the service
        """
        services={}
        names = self.messages_app.services.name.get()
        flags = self.messages_app.services.enabled.get()
        types = self.messages_app.services.service_type.get(
            resulttype=appscript.k.string)
        
        for name, enabled, typ in zip(names, flags, types):
            if enabled:
                services[name] = self._trim_appscript_weirdness(unicode(typ))

        return services

    def _buddies_on_service(self, service):
        """ Ask Messages.app for a list of all buddies on one of its services.
        Returns a dictionary of buddy names keyed by buddy handle's
        """
        names = self.messages_app.services[service].buddies.name.get()
        handles = self.messages_app.services[service].buddies.handle.get()
        return dict(zip(handles, names))

    def _trim_appscript_weirdness(self, name):
        """ Return a string trimmed of an initial "k." if it has one
        """
        if name.startswith("k."):
            name = name[2:]
        return name
        
