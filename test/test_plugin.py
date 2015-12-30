#! /usr/bin/env python
# Copyright (c) 2016 Gemini Lasswell
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import print_function
import os
import sys
import unittest

from mock import patch, Mock
from threading import Thread

sys.path.append(os.path.abspath('../Messages/Contents/Server Plugin'))

class PluginBaseForTest(object):
    def __init__(self, pid, name, version, prefs):
        pass
    def __del__(self):
        pass
    def sleep(self):
        pass
    def debugLog(self, string):
        pass
    def errorLog(self, string):
        pass

class DeviceForTest(object):
    def __init__(self, dev_id, name, props):
        self.id = dev_id
        self.name = name
        self.pluginProps = props
        self.states = {}
    def updateStateOnServer(self, key=None, value=None, clearErrorState=True):
        assert key is not None
        assert value is not None
        self.states[key] = value
    def replacePluginPropsOnServer(self, props):
        self.pluginProps = props
        

class PluginTestCase(unittest.TestCase):

    def setUp(self):
        self.indigo_mock = Mock()
        self.indigo_mock.PluginBase = PluginBaseForTest
        self.indigo_mock.PluginBase.pluginPrefs = {"showDebugInfo" : False}
        self.indigo_mock.Dict = Mock(return_value={}.copy())
        self.indigo_mock.devices = {}
        
        modules = sys.modules.copy()
        modules["indigo"] = self.indigo_mock
        self.module_patcher = patch.dict("sys.modules", modules)
        self.module_patcher.start()
        import plugin

        self.plugin_module = plugin
        self.plugin_module.indigo.PluginBase = PluginBaseForTest

        self.mapp_patch = patch('plugin.appscript.app')
        # appscript.app() adds attributes at execution time like Mock does,
        # so avoid calling it
        self.mapp_patch.start()   
        self.plugin = self.new_plugin()
        self.mapp = self.plugin.messages_app
        
    def tearDown(self):
        self.module_patcher.stop()
        self.mapp_patch.stop()

    def new_plugin(self):
        # Before I created this little function,
        # python was giving me a bizillion "NoneType object has no
        # attribute" warnings, I think because tearDown is called,
        # removing the base class, before the plugin objects are deleted.
        # why this fixed it is a mystery to me
        return self.plugin_module.Plugin("What's", "here", "doesn't matter",
                                           {"showDebugInfo" : False})

    def test_Startup_Succeeds(self):
        self.plugin.startup()
        pass

    def test_Shutdown_Succeeds(self):
        self.plugin.shutdown()
        pass

    def test_Update_Succeeds(self):
        self.plugin.update()
        pass

    def test_RunConcurrentThread_Exits_OnStopThread(self):
        self.plugin.StopThread = Exception
        self.plugin.sleep = Mock(side_effect = Exception("test"))

        t = Thread(target=self.plugin.runConcurrentThread)
        t.start()
        t.join(0.1)
        self.assertFalse(t.is_alive(), "I'm in an infinite loop!")

    def test_DebugMenuItem_Toggles(self):
        self.assertFalse(self.plugin.debug)
        self.plugin.debugLog = Mock()
        
        self.plugin.toggleDebugging()
        self.assertEqual(self.plugin.debugLog.call_count, 1)
        self.assertTrue(self.plugin.debug)

        self.plugin.toggleDebugging()
        self.assertEqual(self.plugin.debugLog.call_count, 2)
        self.assertFalse(self.plugin.debug)
             
    def test_PreferencesUIValidation_Succeeds(self):
        values = {"showDebugInfo":"false"}
        ok, d = self.plugin.validatePrefsConfigUi(values)
        self.assertTrue(ok)

    def test_ActionUIValidation_Succeeds_OnValidInput(self):
        values = {"message":"Hi"}
        tup = self.plugin.validateActionConfigUi(values, "sendMessage", 0)
        self.assertEqual(len(tup), 2)
        ok, val = tup
        self.assertTrue(ok)

    def test_ActionUIValidation_Fails_OnEmptyMessage(self):
        values = {"message":""}
        tup = self.plugin.validateActionConfigUi(values, "sendMessage", 0)
        self.asserts_for_UIValidation_Failure("message", tup)

    def test_ActionUIValidation_Fails_OnNoMessage(self):
        values = {"":"whatever"}
        tup = self.plugin.validateActionConfigUi(values, "sendMessage", 0)
        self.asserts_for_UIValidation_Failure("message", tup)
        
    def asserts_for_UIValidation_Failure(self, tag, tup):
        self.assertEqual(len(tup), 3)
        ok, val, errs = tup
        self.assertFalse(ok)
        if tag:
            self.assertEqual(len(errs), 2)
            self.assertTrue(tag in errs)
            self.assertTrue(errs[tag])
        else:
            self.assertEqual(len(errs), 1)

        self.assertTrue("showAlertText" in errs)
        self.assertTrue(errs["showAlertText"])

    def test_DeviceUIValidation_Succeeds_OnValidInput(self):
        values = {"handle":"1-800-CALL-ME", "service":"FooMessage"}
        tup = self.plugin.validateDeviceConfigUi(values, 0, 0)
        self.assertEqual(len(tup), 2)
        ok, val = tup
        self.assertTrue(ok)

    def test_ServiceGenerator_Succeeds_WhenMessagesAppRaisesException(self):
        self.mapp.services = Mock(side_effect = Exception("test"))
        s = self.plugin.serviceGenerator()
        self.assertEqual(len(s), 0)

    def test_ServiceGenerator_Succeeds_WhenMessagesAppAvailable(self):
        self.mock_services_and_buddies()
        s = self.plugin.serviceGenerator()
        self.assertTrue(len(s) == 1)

    def test_ServiceGenerator_Succeeds_WhenGivenUnknownService(self):
        self.mock_services_and_buddies()
        values = {"service":"unknown"}
        s = self.plugin.serviceGenerator(values=values)
        self.assertEqual(len(s), 2)

    def test_BuddyGenerator_Succeeds_WhenNotGivenService(self):
        self.mock_services_and_buddies()
        b = self.plugin.buddyGenerator()
        self.assertTrue(len(b) == 0)

    def test_BuddyGenerator_Succeeds_WhenMessagesAppRaisesException(self):
        self.mapp.services = Mock(side_effect=Exception("test"))
        b = self.plugin.buddyGenerator()
        self.assertEqual(len(b), 0)

    def test_BuddyGenerator_Succeeds_WhenGivenUnknownService(self):
        self.mock_services_and_buddies()
        values = {"service":"unknown"}
        b = self.plugin.buddyGenerator(values=values)
        self.assertEqual(len(b), 0)

    def test_BuddyGenerator_Succeeds_WhenGivenUnknownHandle(self):
        self.mock_services_and_buddies()
        values = {"service":"E:fred@bedrock.com",
                  "handle": "wilma@bedrock.com"}
        b = self.plugin.buddyGenerator(values=values)
        self.assertEqual(len(b), 2)

    def test_BuddyGenerator_Succeeds_WhenGivenUnknowns(self):
        self.mock_services_and_buddies()
        values = {"service":"unknown",
                  "handle": "wilma@bedrock.com"}
        b = self.plugin.buddyGenerator(values=values)
        self.assertEqual(len(b), 1)

    def test_DeviceStartComm_Succeeds_OnValidInput(self):
        self.mock_services_and_buddies()
        dev = self.make_and_start_a_test_device(
                      1, "dev1", {"handle":"barney@bedrock.com",
                                  "service":"E:fred@bedrock.com"})
        states = dev.states
        self.assertEqual(len(states), 5)
        self.assertEqual(states["message"], "")
        self.assertEqual(states["status"], "No Message")
        self.assertEqual(states["response"], "")
        self.assertEqual(states["responseStatus"], "No Message")
        self.assertTrue("name" in states)
                        
    def test_DeviceStartComm_Fails_WhenServiceNotFound(self):
        self.mapp.services.__getitem__ = Mock(side_effect=Exception("test"))
        dev1 = self.make_and_start_a_test_device(1, "d1",
                                                {"handle":"######",
                                                 "service":"#####"})
        self.asserts_for_DeviceStartComm_Failure(dev1.states)
        self.assertTrue(dev1.id in self.plugin.device_info)
        
        dev2 = self.make_and_start_a_test_device(2, "d2",
                    {"handle":"######", "service":"E:fred@bedrock.com"})
        self.asserts_for_DeviceStartComm_Failure(dev2.states)
        self.assertTrue(dev2.id in self.plugin.device_info)

    def asserts_for_DeviceStartComm_Failure(self, states):
        self.assertEqual(len(states), 5)
        self.assertEqual(states["message"], "")
        self.assertEqual(states["status"], "Error")
        self.assertEqual(states["response"], "")
        self.assertEqual(states["responseStatus"], "Error")
        self.assertTrue("name" in states)

    def test_DeviceStopComm_Succeeds(self):
        self.mock_services_and_buddies()
        dev = self.make_and_start_a_test_device(1, "d1",
                                                {"handle":"barney@bedrock.com",
                                                 "service":"E:fred@bedrock.com"})
        self.plugin.deviceStopComm(dev)
        self.assertFalse(dev.id in self.plugin.device_info)

    def test_receiveMessageAndMarkAsRead_Succeed_WhenMatchingDeviceExists(self):
        self.mock_services_and_buddies()
        dev = self.make_and_start_a_test_device(1, "d1",
                                            {"handle":"barney@bedrock.com",
                                             "service":"E:fred@bedrock.com"})
        self.assertEqual(dev.states["status"], "No Message")

        action = Mock()
        test_message = "This is a test"
        action.props = {"message":test_message,
                        "handle": "barney@bedrock.com",
                        "service": "E:fred@bedrock.com",
                        "service_type":"#####"}
        self.plugin.receiveMessage(action)
        self.assertEqual(dev.states["status"], "New")
        self.assertEqual(dev.states["message"], test_message)
        self.assertEqual(self.plugin.device_info[dev.id], [])

        # Because the setup is already done, test that receiveMessage adds to
        # the backlog when there is already a new message

        test_message2 = "This is a different test"
        action.props["message"] = test_message2
        self.plugin.receiveMessage(action)

        self.assertEqual(dev.states["status"], "New")
        self.assertEqual(dev.states["message"], test_message)
        self.assertEqual(len(self.plugin.device_info[dev.id]), 1)

        # Now test that markAsRead fetches the backlog message
        action = Mock()
        action.deviceId = dev.id
        self.plugin.markAsRead(action)
        self.assertEqual(dev.states["status"], "New")
        self.assertEqual(dev.states["message"], test_message2)
        self.assertEqual(self.plugin.device_info[dev.id], [])

        # And markAsRead again should change state to Read
        self.plugin.markAsRead(action)
        self.assertEqual(dev.states["status"], "Read")
        
    def test_receiveMessage_Ignores_MessageWithNoMatchingDevice(self):
        self.mock_to_make_deviceStartComm_succeed()
        dev = self.make_and_start_a_test_device(1, "d1",
                                            {"handle":"fred@fred.com",
                                             "service":"fredserv"})
        self.assertTrue(dev.states["status"] == "No Message")

        action = Mock()
        test_message = "This is a test"
        action.props = {"message":test_message,
                        "handle": "george@george.com",
                        "service":dev.pluginProps["service"],
                        "service_type":"#####"}
        self.plugin.receiveMessage(action)
        self.assertNotEqual(dev.states["status"], "New")
        self.assertEqual(dev.states["message"], "")
        self.assertEqual(self.plugin.device_info[dev.id], [])

    def mock_to_make_deviceStartComm_succeed(self):
        self.plugin._messages_app_buddy = Mock()
        self.plugin._name_of_buddy = Mock(return_value="whatever")

    def test_sendMessage_Succeeds_OnValidInput(self):
        dev = self.make_and_start_a_test_device(1, "d1",
                                            {"handle":"fred@fred.com",
                                             "service":"fredserv"})
        action = Mock()
        test_message = "This is a test"
        action.deviceId = dev.id
        action.props ={"message": test_message}
        self.plugin.sendMessage(action)

        self.assertTrue(self.mapp.send.called)
        self.assertEqual(dev.states["responseStatus"], "Sent")
        self.assertEqual(dev.states["response"], test_message)

    def test_sendMessage_SetsErrorState_OnMessagesAppException(self):
        # Turns out Messages.app doesn't throw exceptions no matter what
        # random non-handle string and service you give it
        self.mapp.send = Mock(side_effect=Exception("test"))
        
        dev = self.make_and_start_a_test_device(1, "d1",
                                            {"handle":"fred@fred.com",
                                             "service":"fredserv"})
        action = Mock()
        test_message = "This is a test"
        action.deviceId = dev.id
        action.props ={"message": test_message}
        self.plugin.sendMessage(action)

        self.assertEqual(dev.states["responseStatus"], "Error")
        self.assertEqual(dev.states["response"], test_message)
        
    def make_and_start_a_test_device(self, dev_id, name, props):
        dev = DeviceForTest(dev_id, name, props)
        self.indigo_mock.devices[dev_id] = dev
        self.plugin.deviceStartComm(dev)
        return dev

    def mock_services_and_buddies(self):
        self.mapp.services.name.get.return_value = ["E:fred@bedrock.com"]
        self.mapp.services.enabled.get.return_value = [True]
        self.mapp.services.service_type.get.return_value = ["iMessage"]
        
        mockbuddy = Mock()
        self.mapp.services.__getitem__.return_value = mockbuddy
        mockbuddy.buddies.name.get = Mock(return_value=["Barney Rubble"])
        mockbuddy.buddies.handle.get = Mock(return_value=["barney@bedrock.com"])
        mockbuddy.name.get = "Barney Rubble"
        mockbuddy.handle.get = "barney@bedrock.com"
        mockbuddy.buddies.__getitem__ = Mock()

if __name__ == "__main__":
    unittest.main()
