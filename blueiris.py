#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Magnus Appelquist 2014-06-02 Initial
#

import requests, json, hashlib, sys, argparse

def main():
    parser = argparse.ArgumentParser(description='Blue Iris controller', prog='blueiris')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0 https://github.com/magapp/blueiris')
    parser.add_argument("--host", help="Blue Iris host to connect to ", required=True)
    parser.add_argument('--user', help='User to use when connecting', required=True)
    parser.add_argument('--password', help='Password to use when connecting', required=True)
    parser.add_argument('--debug', action='store_true', help='Print debug messages')
    parser.add_argument('--list-profiles', action='store_true', help='List all available profiles')
    parser.add_argument('--set-profile', action='store', help='Set current profile', metavar='profile-name', default=None)
    parser.add_argument('--trigger', action='store', help='Trigger camera', metavar='camera-short-name', default=None)

    args = parser.parse_args()

    bi = BlueIris(args.host, args.user, args.password, args.debug)
    current_profile = bi.get_profile()
    print "Profile '%s' is active" % current_profile

    if args.list_profiles:
        print "Available profiles are:"
        print ", ".join(bi.profiles_list)

    if args.set_profile:
        try:
            profile_id = bi.profiles_list.index(args.set_profile)
        except:
            print "Could not find any profile with that name. Use --list-profiles to see available profiles."
            sys.exit(0)
        print "Setting active profile to '%s' (id: %d)" % (args.set_profile, profile_id)
        bi.cmd("status", {"profile": profile_id})

    if args.trigger:
        print "Triggering camera '%s'" % args.trigger
        bi.cmd("trigger", {"camera": args.trigger})

    bi.logout()
    sys.exit(0)

class BlueIris:
    session = None
    response = None

    def __init__(self, host, user, password, debug=False):
        self.host = host
        self.user = user
        self.password = password
        self.debug = debug
        self.url = "http://"+host+"/json"
        r = requests.post(self.url, data=json.dumps({"cmd":"login"}))
        if r.status_code != 200:
            print r.status_code
            print r.text
            sys.exit(1)

        self.session = r.json()["session"]
        self.response = hashlib.md5("%s:%s:%s" % (user, self.session, password)).hexdigest()
        if self.debug:
            print "session: %s response: %s" % (self.session, self.response)

        r = requests.post(self.url, data=json.dumps({"cmd":"login", "session": self.session, "response": self.response}))
        if r.status_code != 200 or r.json()["result"] != "success":
            print r.status_code
            print r.text
            sys.exit(1)
        self.system_name = r.json()["data"]["system name"]
        self.profiles_list = r.json()["data"]["profiles"]

        print "Connected to '%s'" % self.system_name

    def cmd(self, cmd, params=dict()):
        args = {"session": self.session, "response": self.response, "cmd": cmd}
        args.update(params)

        r = requests.post(self.url, data=json.dumps(args))

        if r.status_code != 200 or r.json()["result"] != "success":
            print r.status_code
            print r.text
            sys.exit(1)

        if self.debug:
            print str(r.json())

        try:
            return r.json()["data"]
        except:
            return r.json()

    def get_profile(self):
        r = self.cmd("status")
        profile_id = int(r["profile"])
        if profile_id == -1:
            return "Undefined"
        return self.profiles_list[profile_id]

    def logout(self):
        self.cmd("logout")

if __name__ == "__main__":
    main()
